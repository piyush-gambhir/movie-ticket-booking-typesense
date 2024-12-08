from typesense import Client
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from dotenv import load_dotenv

load_dotenv()


def setup_logger(
    name,
    level=logging.DEBUG
    if os.getenv("ENVIRONMENT", "production").lower() == "development"
    else logging.INFO,
    log_to_file=False,
    file_path="app.log",
    max_bytes=5 * 1024 * 1024,
    backup_count=3,
):
    """
    Sets up and returns a logger with consistent formatting.

    Args:
        name (str): The name of the logger.
        level (int): Logging level.
        log_to_file (bool): If True, logs to a file in addition to console.
        file_path (str): Path for the log file if log_to_file is True.
        max_bytes (int): Maximum size of the log file before rotating (default: 5MB).
        backup_count (int): Number of backup files to keep.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    if len(logger.handlers) == 0:
        logger.setLevel(level)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        if log_to_file:
            file_handler = RotatingFileHandler(
                file_path, maxBytes=max_bytes, backupCount=backup_count
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        logger.propagate = False

    return logger


logger = setup_logger(__name__, log_to_file=True, file_path="script.log")


def initialize_typesense_client():
    return Client(
        {
            "nodes": [{"host": "localhost", "port": "8108", "protocol": "http"}],
            "api_key": "xyz",
            "connection_timeout_seconds": 2,
        }
    )


def create_typesense_collection(client, collection_name, schema):
    try:
        client.collections[collection_name].retrieve()
        logger.debug(f"Collection '{collection_name}' already exists.")
    except Exception as e:
        logger.debug(
            f"Collection '{collection_name}' does not exist. Creating a new collection."
        )
        client.collections.create(schema)
        logger.info(f"Collection '{collection_name}' created successfully.")


def transform_json_data(data):
    def to_camel_case(snake_str):
        components = snake_str.split("_")
        return components[0] + "".join(x.title() for x in components[1:])

    transformed_data = []
    for document in data:
        document_camel_case = {to_camel_case(k): v for k, v in document.items()}
        transformed_data.append(document_camel_case)
    return transformed_data


def import_typesense_collection_bulk(
    client, collection_name, documents, batch_size=100
):
    for i in range(0, len(documents), batch_size):
        batch = documents[i : i + batch_size]
        try:
            client.collections[collection_name].documents.import_(
                batch, {"action": "upsert"}
            )
            logger.info(f"Batch {i//batch_size + 1} imported successfully.")
        except Exception as e:
            logger.error(f"Error importing batch starting at index {i}: {e}")


collection_schema = None
with open("schemas/movies.json", "r", encoding="utf-8") as schema_file:
    collection_schema = json.load(schema_file)


data_filename = "dataset/movies.json"
documents = []
with open(data_filename, "r", encoding="utf-8") as f:
    data = json.load(f)
    documents = transform_json_data(data)
collection_name = "movies"
batch_size = 10000

client = initialize_typesense_client()
create_typesense_collection(client, collection_name, collection_schema)
import_typesense_collection_bulk(client, collection_name, documents, batch_size)
