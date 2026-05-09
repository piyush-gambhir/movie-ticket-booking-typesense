import os
import json
import requests
import pandas as pd  # Import pandas for CSV handling
from concurrent.futures import ThreadPoolExecutor

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv is optional; if not installed, rely on the shell environment.
    pass

# TMDB API read access token (v4 auth). Get yours at https://www.themoviedb.org/settings/api
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
if not TMDB_API_KEY:
    raise RuntimeError(
        "TMDB_API_KEY is not set. Add it to a .env file in this directory "
        "(see .env.example) or export it in your shell."
    )

# Genre mapping dictionary
GENRE_MAP = {
    28: 'Action',
    12: 'Adventure',
    16: 'Animation',
    35: 'Comedy',
    80: 'Crime',
    99: 'Documentary',
    18: 'Drama',
    10751: 'Family',
    14: 'Fantasy',
    36: 'History',
    27: 'Horror',
    10402: 'Music',
    9648: 'Mystery',
    10749: 'Romance',
    878: 'Science Fiction',
    10770: 'TV Movie',
    53: 'Thriller',
    10752: 'War',
    37: 'Western'
}

# Function to fetch data from TMDB using IMDb ID
def fetch_movie_data(imdb_id):
    url = f"https://api.themoviedb.org/3/find/{imdb_id}"
    headers = {
        'Authorization': f'Bearer {TMDB_API_KEY}',
        'accept': 'application/json'
    }
    params = {'external_source': 'imdb_id'}
    response = requests.get(url, headers=headers, params=params)
    return response.json()

# Function to transform the data to the required schema
def transform_data(imdb_id, data):
    movie_data = data.get('movie_results', [])  # Get movie results
    tv_show_data = data.get('tv_results', [])  # Get TV show results

    if tv_show_data:
        # If TV data exists, dump it into a CSV file with the raw API response
        tv_data_to_csv(imdb_id, data)
        return None  # Skip processing for TV shows

    if not movie_data:
        return None  # Return None if there's no movie data

    # Map genre_ids to genre names
    genres = [GENRE_MAP.get(genre_id, "Unknown")
              for genre_id in movie_data[0].get('genre_ids', [])]

    transformed_data = {
        "imdbId": imdb_id,  # Store IMDb ID instead of TMDB ID
        "title": movie_data[0].get("title"),
        "originalTitle": movie_data[0].get("original_title"),
        "backdropPath": f"https://image.tmdb.org/t/p/w500/{movie_data[0].get('backdrop_path')}",
        "posterPath": f"https://image.tmdb.org/t/p/w500/{movie_data[0].get('poster_path')}",
        "overview": movie_data[0].get("overview"),
        "releaseDate": movie_data[0].get("release_date"),
        "popularity": movie_data[0].get("popularity"),
        "adult": movie_data[0].get("adult"),
        "mediaType": movie_data[0].get("media_type"),
        "originalLanguage": movie_data[0].get("original_language"),
        "voteAverage": movie_data[0].get("vote_average"),
        "voteCount": movie_data[0].get("vote_count"),
        "genres": genres  # Add mapped genres
    }
    return transformed_data

# Function to store TV show data into a CSV
def tv_data_to_csv(imdb_id, raw_data):
    # Define file path for CSV
    csv_file_path = 'tv_show_data.csv'
    
    # Prepare the data for CSV
    tv_show_data = {
        "imdbId": imdb_id,
        "rawResponse": json.dumps(raw_data)  # Store the full raw response as a string
    }
    
    # Append to the CSV file, creating it if it doesn't exist
    df = pd.DataFrame([tv_show_data])
    if not os.path.exists(csv_file_path):
        df.to_csv(csv_file_path, mode='w', header=True, index=False)
    else:
        df.to_csv(csv_file_path, mode='a', header=False, index=False)

# Function to send the transformed data to your local API
def send_data_to_api(transformed_data):
    url = "http://localhost:3001/api/v1/movies"
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers,
                             data=json.dumps(transformed_data))
    return response.json()

# Worker function to fetch, transform, and store data
def process_movie(imdb_id):
    # Fetch movie data
    raw_data = fetch_movie_data(imdb_id)

    # Transform data
    transformed_data = transform_data(imdb_id, raw_data)
    if not transformed_data:
        print(f"No movie data found for IMDb ID: {imdb_id} or it is a TV show")
        return

    # Send data to the local API
    api_response = send_data_to_api(transformed_data)
    print(f"API Response for IMDb ID {imdb_id}: {api_response}")

# Function to handle multiple workers and process IMDb IDs concurrently
def process_movies_concurrently(imdb_ids, max_workers=50):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(process_movie, imdb_ids)

# Function to fetch IMDb IDs from CSV file
def fetch_imdb_ids_from_csv(file_path):
    df = pd.read_csv(file_path)
    return df['id'].tolist()  # Assuming 'id' is the column containing IMDb IDs

def main():
    # Path to the CSV file
    csv_file_path = r'G:\My Drive\CS\#Data\Movies Dataset\movies.csv'  # Update this with the actual path

    # Fetch IMDb IDs from the CSV file
    imdb_ids = fetch_imdb_ids_from_csv(csv_file_path)

    # Process movies concurrently based on IMDb IDs
    process_movies_concurrently(imdb_ids)

if __name__ == "__main__":
    main()
