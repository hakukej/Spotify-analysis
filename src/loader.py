"""SQLite storage with primary-key idempotency and SQL verification."""
import sqlite3
import pandas as pd
from src.config import DB_PATH, DATA_DIR


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def create_schema(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS spotify_tracks (
            track_id TEXT PRIMARY KEY,
            track_name TEXT NOT NULL,
            artist_names TEXT NOT NULL,
            album_name TEXT NOT NULL,
            album_type TEXT NOT NULL,
            release_date TEXT NOT NULL,
            release_year INTEGER,
            duration_ms INTEGER NOT NULL,
            duration_minutes REAL NOT NULL,
            duration_zscore REAL NOT NULL,
            duration_category TEXT NOT NULL,
            explicit INTEGER NOT NULL,
            track_number INTEGER NOT NULL,
            disc_number INTEGER NOT NULL,
            album_total_tracks INTEGER NOT NULL,
            market TEXT NOT NULL,
            spotify_url TEXT NOT NULL
        )
    """)
    conn.commit()


def load_dataframe(df):
    columns = [
        "track_id", "track_name", "artist_names", "album_name", "album_type",
        "release_date", "release_year", "duration_ms", "duration_minutes",
        "duration_zscore", "duration_category", "explicit", "track_number",
        "disc_number", "album_total_tracks", "market", "spotify_url"
    ]
    payload = df[columns].copy()
    payload["release_date"] = payload["release_date"].astype(str)
    payload["release_year"] = payload["release_year"].astype("Int64")
    payload["explicit"] = payload["explicit"].astype(int)
    payload = payload.astype(object).where(pd.notna(payload), None)
    rows = [
        tuple(value.item() if hasattr(value, "item") else value for value in row)
        for row in payload.itertuples(index=False, name=None)
    ]
    conn = connect()
    try:
        create_schema(conn)
        sql = f"""INSERT INTO spotify_tracks ({",".join(columns)})
                  VALUES ({",".join(["?"] * len(columns))})
                  ON CONFLICT(track_id) DO NOTHING"""
        conn.executemany(sql, rows)
        conn.commit()
        stored = conn.execute("SELECT COUNT(*) FROM spotify_tracks").fetchone()[0]
        unique = conn.execute("SELECT COUNT(DISTINCT track_id) FROM spotify_tracks").fetchone()[0]
        return stored, unique
    finally:
        conn.close()


def verify_idempotency(df):
    first_count, _ = load_dataframe(df)
    second_count, _ = load_dataframe(df)
    conn = connect()
    try:
        duplicate_count = conn.execute(
            "SELECT COUNT(*) - COUNT(DISTINCT track_id) FROM spotify_tracks"
        ).fetchone()[0]
        sample = conn.execute(
            "SELECT track_id, track_name, album_type, duration_ms FROM spotify_tracks LIMIT 5"
        ).fetchall()
    finally:
        conn.close()
    result = {
        "stored_after_first_load": first_count,
        "stored_after_second_load": second_count,
        "duplicate_primary_keys": duplicate_count,
        "idempotency_passed": first_count == second_count and duplicate_count == 0,
        "sample_rows": sample,
    }
    import json
    (DATA_DIR / "database_verification.json").write_text(
        json.dumps(result, indent=2, default=str), encoding="utf-8"
    )
    if not result["idempotency_passed"]:
        raise RuntimeError("SQLite idempotency test failed.")
    print(f"SQLite rows after first load: {first_count}")
    print(f"SQLite rows after second load: {second_count}")
    print(f"Duplicate primary keys: {duplicate_count}")
    print("Idempotency test: PASS")
    return result


if __name__ == "__main__":
    df = pd.read_csv(DATA_DIR / "cleaned_data.csv")
    verify_idempotency(df)
