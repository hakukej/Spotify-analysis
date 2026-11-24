# Data Dictionary

| Field | Type | Description |
|---|---|---|
| track_id | string | Spotify unique track identifier; SQLite primary key |
| track_name | string | Track title |
| artist_names | string | Artist names joined into one text field |
| album_name | string | Album title |
| album_type | category | album, single, or compilation |
| release_date | date | Release date normalized to YYYY-MM-DD |
| release_date_precision | category | Original Spotify precision: year, month, or day |
| duration_ms | integer | Track duration in milliseconds |
| explicit | boolean | Whether Spotify marks the track as explicit |
| track_number | integer | Position of the track on its disc |
| disc_number | integer | Disc number |
| album_total_tracks | integer | Total number of tracks on the album |
| market | category | Two-letter market code used in the search |
| spotify_url | string | Spotify track URL |
| collected_at | datetime | UTC timestamp when this record was collected |

Derived fields created during transformation:
- `release_year`: year extracted from release_date.
- `duration_minutes`: duration_ms divided by 60,000.
- `duration_zscore`: NumPy z-score of duration_ms within the collected sample.
- `duration_category`: short (<3 min), medium (3–5 min), or long (>5 min).
