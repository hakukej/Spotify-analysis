# Spotify SIS2 — Data Streaming and Validation Pipeline

## Project overview
This project collects Spotify track metadata through the Spotify Web API, streams records through a real Apache Kafka broker, validates them with Pandera, cleans and transforms them with pandas/NumPy, stores them in SQLite3, and performs EDA with three visualizations.

Source: Spotify Web API `GET https://api.spotify.com/v1/search` (`type=track`).

## Prerequisites
- Python 3.11+
- Docker Desktop with Docker Compose
- A Spotify Developer application and its Client ID / Client Secret
- Spotify developer account/app eligibility under Spotify's current Developer Mode rules

Spotify Web API requires OAuth authorization. This project uses the server-to-server Client Credentials flow for public catalog metadata. Do not commit `.env` or credentials.

## Setup
```bash
git clone <your-repository-url>
cd spotify_sis2_project
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
```
Put your own `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` into `.env`.

Create the Spotify app in the Spotify Developer Dashboard and select Web API. Check the current account eligibility, Premium requirement for Development Mode, allowlist, and endpoint availability in Spotify's dashboard/documentation. The project does not contain or provide credentials.

## Start a real Kafka broker
```bash
docker compose up -d
docker compose ps
```
Kafka is a real Apache Kafka broker running in Docker; this is not a Python-list simulation. The project uses topic `spotify-tracks`. The producer creates the topic automatically through Kafka's auto-topic-creation configuration. If your broker disables auto topic creation, create the topic with Kafka's `kafka-topics.sh` utility before running the pipeline.

## Run the complete pipeline
```bash
python main.py
```
The script runs the stages in order:
1. Collect at least 200 unique track records and preserve raw JSON/CSV.
2. Start the finite Kafka consumer.
3. Publish each record as JSON to Kafka.
4. Consume the expected number of records and save the Kafka output.
5. Validate records with Pandera, including three synthetic negative tests.
6. Clean and transform valid records with pandas and NumPy.
7. Load SQLite twice, verify no duplicate primary keys, and run EDA.

## Run individual components
```bash
python -m src.api_client
python -m src.consumer --expected 200
python -m src.producer
python -m src.validator
python -m src.cleaner
python -m src.loader
python -m src.analysis
```
For separate consumer/producer execution, start the consumer first and set `--expected` to the number of records in `data/raw_data.json`.

## Outputs
- `data/raw_data.json`, `data/raw_data.csv` — original API records
- `data/kafka_messages.jsonl` — records consumed from Kafka
- `data/validated_data.csv`, `data/invalid_records.csv`
- `data/validation_summary.json`
- `data/cleaned_data.csv`, `data/grouped_album_type.csv`, `data/pivot_melted_release_year.csv`
- `data/spotify.db` — SQLite database
- `data/database_verification.json`, `data/pipeline_metrics.json`
- `data/descriptive_statistics.csv`, `data/categorical_statistics.csv`, `data/eda_grouped_analysis.csv`
- `data/eda_findings.json`
- `figures/01_duration_distribution.png`
- `figures/02_tracks_by_album_type.png`
- `figures/03_tracks_by_release_year.png`

## Validation rules
1. Track ID is required, string, sufficiently long, and unique.
2. Track name, artist names, and album name are required and non-empty.
3. Album type must be album, single, or compilation.
4. Duration must be between 1 and 3,600,000 ms.
5. Explicit flag must be boolean.
6. Track number, disc number, and album track count must be positive.
7. Track number cannot exceed album track count.
8. Release date must be parseable.
9. Market must be a two-character code.

Three deliberately invalid test records are tested independently and excluded from the production data.

## Cleaning and transformation
- Remove duplicate track IDs and rows with missing required values.
- Convert release date to datetime and derive release year.
- Normalize whitespace in track/artist/album names.
- Use NumPy to calculate duration z-scores and vectorized duration categories.
- Filter records using multiple duration and track-number conditions.
- Use GroupBy aggregation by album type.
- Use pivot_table followed by melt to reshape median duration by release year and album type.

## SQLite and idempotency
`track_id` is the primary key. Inserts use `ON CONFLICT(track_id) DO NOTHING`. `python -m src.loader` loads the same cleaned data twice and compares counts. SQL checks are in `sql/verification.sql`.

## Reproducibility and limitations
Spotify search results are dynamic and may vary by execution date, market, and API access policy. The API may return fewer than 200 unique results for the configured search terms; the collector stops with an error rather than silently using fabricated data. Add search terms in `.env` if needed. The API's search `limit` is capped at 10 in the current reference; pagination uses offsets. API 429 responses are handled using `Retry-After`.

A successful end-to-end run requires valid Spotify credentials and a running Kafka broker. Execution metrics and figures are generated locally by the submitted code. Do not report expected or sample counts as actual results before running the pipeline.

## References
- Spotify Web API: https://developer.spotify.com/documentation/web-api
- Search endpoint: https://developer.spotify.com/documentation/web-api/reference/search
- Client Credentials flow: https://developer.spotify.com/documentation/web-api/tutorials/client-credentials-flow
- API calls and authorization: https://developer.spotify.com/documentation/web-api/concepts/api-calls
- Rate limits: https://developer.spotify.com/documentation/web-api/concepts/rate-limits
- Apache Kafka: https://kafka.apache.org/documentation/
- Pandera: https://pandera.readthedocs.io/
- pandas: https://pandas.pydata.org/docs/
- NumPy: https://numpy.org/doc/
- SQLite: https://www.sqlite.org/docs.html
