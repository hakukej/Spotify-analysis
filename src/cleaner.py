"""Clean and transform validated Spotify track records using pandas and NumPy."""
import json
import numpy as np
import pandas as pd
from src.config import DATA_DIR


def clean_transform(df):
    before = len(df)
    df = df.copy()
    duplicate_count = int(df.duplicated(subset=["track_id"]).sum())
    df = df.drop_duplicates(subset=["track_id"])
    missing_before = int(df.isna().sum().sum())
    df = df.dropna(subset=[
        "track_id", "track_name", "artist_names", "album_name", "album_type",
        "release_date", "duration_ms", "track_number", "disc_number",
        "album_total_tracks",
    ])
    df["track_name"] = df["track_name"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    df["artist_names"] = df["artist_names"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    df["album_name"] = df["album_name"].astype(str).str.strip()
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    df["release_year"] = df["release_date"].dt.year.astype("Int64")
    df["duration_ms"] = pd.to_numeric(df["duration_ms"], errors="coerce")
    df["duration_minutes"] = df["duration_ms"] / 60000.0
    # NumPy operations: z-score and vectorized duration classification.
    mean = float(np.mean(df["duration_ms"]))
    std = float(np.std(df["duration_ms"])) or 1.0
    df["duration_zscore"] = (df["duration_ms"].to_numpy(dtype=float) - mean) / std
    df["duration_category"] = np.select(
        [df["duration_minutes"] < 3, df["duration_minutes"] <= 5],
        ["short", "medium"], default="long"
    )
    # Multiple-condition filter excludes implausibly short/long metadata records.
    df = df[
        (df["duration_ms"] >= 30000)
        & (df["duration_ms"] <= 1200000)
        & (df["track_number"] >= 1)
        & (df["album_total_tracks"] >= df["track_number"])
    ].copy()
    df = df.dropna(subset=["release_date"])
    df = df.sort_values(["release_date", "track_name"]).reset_index(drop=True)

    grouped = df.groupby("album_type", dropna=False).agg(
        track_count=("track_id", "count"),
        avg_duration_minutes=("duration_minutes", "mean"),
        explicit_share=("explicit", "mean"),
    ).reset_index()
    pivot = pd.pivot_table(
        df, index="release_year", columns="album_type",
        values="duration_minutes", aggfunc="median"
    )
    melted = pivot.reset_index().melt(
        id_vars="release_year", var_name="album_type",
        value_name="median_duration_minutes"
    )
    df.to_csv(DATA_DIR / "cleaned_data.csv", index=False)
    grouped.to_csv(DATA_DIR / "grouped_album_type.csv", index=False)
    melted.to_csv(DATA_DIR / "pivot_melted_release_year.csv", index=False)
    metrics = {
        "input_valid_records": before,
        "duplicates_removed": duplicate_count,
        "missing_values_before_handling": missing_before,
        "cleaned_records": len(df),
        "duration_mean_ms": mean,
        "duration_std_ms": std,
    }
    (DATA_DIR / "cleaning_summary.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return df, grouped, melted


if __name__ == "__main__":
    valid = pd.read_csv(DATA_DIR / "validated_data.csv")
    cleaned, _, _ = clean_transform(valid)
    print(f"Records after cleaning: {len(cleaned)}")
