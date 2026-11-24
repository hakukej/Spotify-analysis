"""Exploratory data analysis and three visualizations."""
import json
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from src.config import DATA_DIR, FIGURES_DIR


def run_eda(df):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    df = df.copy()
    df["release_date"] = pd.to_datetime(df["release_date"])
    describe = df[["duration_ms", "duration_minutes", "track_number", "album_total_tracks"]].describe()
    describe.to_csv(DATA_DIR / "descriptive_statistics.csv")
    categorical = df["album_type"].value_counts().rename_axis("album_type").reset_index(name="count")
    categorical.to_csv(DATA_DIR / "categorical_statistics.csv", index=False)
    grouped = df.groupby("album_type").agg(
        count=("track_id", "count"),
        mean_duration=("duration_minutes", "mean"),
        median_duration=("duration_minutes", "median"),
        explicit_rate=("explicit", "mean"),
    )
    grouped.to_csv(DATA_DIR / "eda_grouped_analysis.csv")

    plt.figure(figsize=(9, 5))
    sns.histplot(df["duration_minutes"], bins=25, kde=True)
    plt.title("Distribution of Spotify Track Durations")
    plt.xlabel("Duration (minutes)")
    plt.ylabel("Number of tracks")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "01_duration_distribution.png", dpi=160)
    plt.close()

    plt.figure(figsize=(8, 5))
    sns.countplot(data=df, x="album_type", order=df["album_type"].value_counts().index)
    plt.title("Tracks by Album Type")
    plt.xlabel("Album type")
    plt.ylabel("Number of tracks")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "02_tracks_by_album_type.png", dpi=160)
    plt.close()

    yearly = df.groupby("release_year").size().reset_index(name="track_count")
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=yearly, x="release_year", y="track_count", marker="o")
    plt.title("Collected Tracks by Release Year")
    plt.xlabel("Release year")
    plt.ylabel("Number of tracks")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "03_tracks_by_release_year.png", dpi=160)
    plt.close()

    findings = {
        "records": int(len(df)),
        "mean_duration_minutes": float(df["duration_minutes"].mean()),
        "median_duration_minutes": float(df["duration_minutes"].median()),
        "most_common_album_type": str(df["album_type"].mode().iloc[0]),
        "explicit_share": float(df["explicit"].mean()),
        "earliest_release_year": int(df["release_year"].min()),
        "latest_release_year": int(df["release_year"].max()),
        "figure_interpretation": {
            "01_duration_distribution": "Shows the shape, spread, and concentration of track durations; compare the mean and median to assess skew.",
            "02_tracks_by_album_type": "Compares the number of collected tracks classified as albums, singles, and compilations.",
            "03_tracks_by_release_year": "Shows how the collected search sample is distributed across release years; it is a sample, not a census of Spotify releases."
        }
    }
    (DATA_DIR / "eda_findings.json").write_text(json.dumps(findings, indent=2), encoding="utf-8")
    print(json.dumps(findings, indent=2))
    return findings


if __name__ == "__main__":
    run_eda(pd.read_csv(DATA_DIR / "cleaned_data.csv"))
