"""Collect track metadata from Spotify Web API using Client Credentials OAuth."""
import base64
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from src.config import CLIENT_ID, CLIENT_SECRET, MARKET, SEARCH_TERMS, TARGET_RECORDS, DATA_DIR

TOKEN_URL = "https://accounts.spotify.com/api/token"
API_URL = "https://api.spotify.com/v1/search"


class SpotifyClient:
    def __init__(self):
        if not CLIENT_ID or not CLIENT_SECRET:
            raise RuntimeError("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env")
        self.session = requests.Session()
        self.token = None
        self.token_expires_at = 0

    def authenticate(self):
        credentials = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
        response = self.session.post(
            TOKEN_URL,
            headers={"Authorization": f"Basic {credentials}"},
            data={"grant_type": "client_credentials"},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        self.token = payload["access_token"]
        self.token_expires_at = time.time() + int(payload.get("expires_in", 3600)) - 60

    def get(self, url, params=None):
        if not self.token or time.time() >= self.token_expires_at:
            self.authenticate()
        headers = {"Authorization": f"Bearer {self.token}"}
        for attempt in range(5):
            response = self.session.get(url, headers=headers, params=params, timeout=30)
            if response.status_code == 401:
                self.token = None
                self.authenticate()
                headers["Authorization"] = f"Bearer {self.token}"
                continue
            if response.status_code == 429:
                wait = int(response.headers.get("Retry-After", "2"))
                time.sleep(wait + 1)
                continue
            if response.status_code >= 500:
                time.sleep(2 ** attempt)
                continue
            response.raise_for_status()
            return response.json()
        raise RuntimeError("Spotify API request failed after retries")

    def collect(self):
        records = {}
        for term in SEARCH_TERMS:
            offset = 0
            while offset <= 1000 and len(records) < TARGET_RECORDS:
                params = {
                    "q": term, "type": "track", "market": MARKET,
                    "limit": 10, "offset": offset,
                }
                payload = self.get(API_URL, params=params)
                page = payload.get("tracks", {}).get("items", [])
                if not page:
                    break
                for track in page:
                    album = track.get("album") or {}
                    artists = track.get("artists") or []
                    track_id = track.get("id")
                    if not track_id:
                        continue
                    release_date = album.get("release_date")
                    # Preserve the API's date precision and normalize to an ISO date.
                    if release_date:
                        if len(release_date) == 4:
                            release_date = f"{release_date}-01-01"
                        elif len(release_date) == 7:
                            release_date = f"{release_date}-01"
                    records[track_id] = {
                        "track_id": track_id,
                        "track_name": track.get("name"),
                        "artist_names": ", ".join(a.get("name", "") for a in artists),
                        "album_name": album.get("name"),
                        "album_type": album.get("album_type"),
                        "release_date": release_date,
                        "release_date_precision": album.get("release_date_precision"),
                        "duration_ms": track.get("duration_ms"),
                        "explicit": track.get("explicit"),
                        "track_number": track.get("track_number"),
                        "disc_number": track.get("disc_number"),
                        "album_total_tracks": album.get("total_tracks"),
                        "market": MARKET,
                        "spotify_url": (track.get("external_urls") or {}).get("spotify"),
                        "collected_at": datetime.now(timezone.utc).isoformat(),
                    }
                    if len(records) >= TARGET_RECORDS:
                        break
                offset += 10

        rows = list(records.values())
        if len(rows) < 200:
            raise RuntimeError(
                f"Only {len(rows)} unique tracks collected. Need at least 200. "
                "Add more search terms or check Spotify API access."
            )
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        out = DATA_DIR / "raw_data.json"
        out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        import pandas as pd
        pd.DataFrame(rows).to_csv(DATA_DIR / "raw_data.csv", index=False)
        print(f"Collected {len(rows)} unique Spotify track records.")
        print(f"Original API data preserved in {out}")
        return rows


def main():
    SpotifyClient().collect()


if __name__ == "__main__":
    main()
