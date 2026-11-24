-- Record count
SELECT COUNT(*) AS stored_records FROM spotify_tracks;

-- Primary-key uniqueness
SELECT COUNT(*) AS duplicate_ids
FROM (
    SELECT track_id
    FROM spotify_tracks
    GROUP BY track_id
    HAVING COUNT(*) > 1
);

-- Distribution by album type
SELECT album_type, COUNT(*) AS track_count,
       ROUND(AVG(duration_minutes), 2) AS avg_duration_minutes
FROM spotify_tracks
GROUP BY album_type
ORDER BY track_count DESC;

-- Release-year summary
SELECT release_year, COUNT(*) AS track_count
FROM spotify_tracks
GROUP BY release_year
ORDER BY release_year;

-- Explicit content share
SELECT explicit, COUNT(*) AS track_count
FROM spotify_tracks
GROUP BY explicit;
