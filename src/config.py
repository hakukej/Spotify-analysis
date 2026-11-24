from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
MARKET = os.getenv("SPOTIFY_MARKET", "US")
SEARCH_TERMS = [x.strip() for x in os.getenv(
    "SPOTIFY_SEARCH_TERMS",
    "year:2024 genre:pop;year:2023 genre:rock;year:2022 genre:hip-hop"
).split(";") if x.strip()]
TARGET_RECORDS = int(os.getenv("TARGET_RECORDS", "250"))
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "spotify-tracks")
GROUP_ID = os.getenv("KAFKA_GROUP_ID", "spotify-sis2-consumer")
DB_PATH = ROOT / os.getenv("SPOTIFY_DB_PATH", "data/spotify.db")
DATA_DIR = ROOT / "data"
FIGURES_DIR = ROOT / "figures"
