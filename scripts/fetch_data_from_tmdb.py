import os
import json
import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
if not TMDB_API_KEY:
    raise RuntimeError(
        "TMDB_API_KEY is not set. Add it to a .env file in this directory "
        "(see .env.example) or export it in your shell."
    )

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

def fetch_movie_data(imdb_id):
    url = f"https://api.themoviedb.org/3/find/{imdb_id}"
    headers = {
        'Authorization': f'Bearer {TMDB_API_KEY}',
        'accept': 'application/json'
    }
    params = {'external_source': 'imdb_id'}
    response = requests.get(url, headers=headers, params=params)
    return response.json()

def transform_data(imdb_id, data):
    movie_data = data.get('movie_results', [])
    tv_show_data = data.get('tv_results', [])

    if tv_show_data:
        tv_data_to_csv(imdb_id, data)
        return None

    if not movie_data:
        return None

    genres = [GENRE_MAP.get(genre_id, "Unknown")
              for genre_id in movie_data[0].get('genre_ids', [])]

    transformed_data = {
        "imdbId": imdb_id,
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
        "genres": genres
    }
    return transformed_data

def tv_data_to_csv(imdb_id, raw_data):
    csv_file_path = 'tv_show_data.csv'
    
    tv_show_data = {
        "imdbId": imdb_id,
        "rawResponse": json.dumps(raw_data)
    }
    
    df = pd.DataFrame([tv_show_data])
    if not os.path.exists(csv_file_path):
        df.to_csv(csv_file_path, mode='w', header=True, index=False)
    else:
        df.to_csv(csv_file_path, mode='a', header=False, index=False)

def send_data_to_api(transformed_data):
    url = "http://localhost:3001/api/v1/movies"
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers,
                             data=json.dumps(transformed_data))
    return response.json()

def process_movie(imdb_id):
    raw_data = fetch_movie_data(imdb_id)

    transformed_data = transform_data(imdb_id, raw_data)
    if not transformed_data:
        print(f"No movie data found for IMDb ID: {imdb_id} or it is a TV show")
        return

    api_response = send_data_to_api(transformed_data)
    print(f"API Response for IMDb ID {imdb_id}: {api_response}")

def process_movies_concurrently(imdb_ids, max_workers=50):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(process_movie, imdb_ids)

def fetch_imdb_ids_from_csv(file_path):
    df = pd.read_csv(file_path)
    return df['id'].tolist()

def main():
    csv_file_path = r'G:\My Drive\CS\#Data\Movies Dataset\movies.csv'

    imdb_ids = fetch_imdb_ids_from_csv(csv_file_path)

    process_movies_concurrently(imdb_ids)

if __name__ == "__main__":
    main()
