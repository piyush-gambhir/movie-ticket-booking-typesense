# movie-ticket-booking-typesense

Typesense setup and ETL scripts for the movie catalog used by the QuickNix movie booking app. Pulls movie metadata from TMDB and indexes it into a Typesense collection so the front-end can do fast typo-tolerant search.

## What's here

- `docker-compose.yaml` — single-node Typesense 27.0 with persistent volume
- `schemas/movies.json` — collection schema (movie fields, facets, default sort by `popularity`)
- `scripts/fetch_data_from_tmdb.py` — fetches movies from TMDB by IMDb ID and normalizes them
- `scripts/import_data_to_typesense.py` — bulk-imports the normalized JSON into Typesense

## Quickstart

```bash
# 1. Start Typesense
echo "TYPESENSE_API_KEY=changeme" > .env
docker compose up -d

# 2. Fetch movies from TMDB (set TMDB credentials in the script or env)
python scripts/fetch_data_from_tmdb.py

# 3. Import into Typesense
python scripts/import_data_to_typesense.py
```

Typesense listens on `http://localhost:8108`.

## Schema highlights

Defined in `schemas/movies.json`:

- `id`, `imdbId`, `title`, `originalTitle`
- `overview`, `releaseDate`, `popularity` (default sort), `voteAverage`, `voteCount`
- Faceted: `genres[]`, `originalLanguage`, `mediaType`, `adult`
- `posterPath`, `backdropPath` for UI rendering
- Locale `en`, stemming on title fields, token separators `- _`

## Environment

- `TYPESENSE_API_KEY` — admin key passed to the server and used by the import script
- TMDB credentials — set in `scripts/fetch_data_from_tmdb.py` (do not commit real keys)

## License

MIT
