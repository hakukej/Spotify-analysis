"""Pandera schema, validation summary, and deliberate negative tests."""
import json
import pandas as pd
import pandera.pandas as pa
from pandera import Check
from pandera.errors import SchemaErrors
from src.config import DATA_DIR

SCHEMA = pa.DataFrameSchema(
    {
        "track_id": pa.Column(str, nullable=False, unique=True, checks=Check.str_length(min_value=10)),
        "track_name": pa.Column(str, nullable=False, checks=Check.str_length(min_value=1)),
        "artist_names": pa.Column(str, nullable=False, checks=Check.str_length(min_value=1)),
        "album_name": pa.Column(str, nullable=False, checks=Check.str_length(min_value=1)),
        "album_type": pa.Column(str, nullable=False, checks=Check.isin(["album", "single", "compilation"])),
        "release_date": pa.Column(str, nullable=False),
        "duration_ms": pa.Column(int, nullable=False, checks=Check.in_range(1, 3600000)),
        "explicit": pa.Column(bool, nullable=False),
        "track_number": pa.Column(int, nullable=False, checks=Check.ge(1)),
        "disc_number": pa.Column(int, nullable=False, checks=Check.ge(1)),
        "album_total_tracks": pa.Column(int, nullable=False, checks=Check.ge(1)),
        "market": pa.Column(str, nullable=False, checks=Check.str_length(min_value=2, max_value=2)),
        "spotify_url": pa.Column(str, nullable=False),
        "collected_at": pa.Column(str, nullable=False),
    },
    checks=[
        Check(lambda df: df["track_number"] <= df["album_total_tracks"],
              error="track_number cannot exceed album_total_tracks"),
        Check(lambda df: pd.to_datetime(df["release_date"], errors="coerce").notna().all(),
              error="release_date must be parseable"),
    ],
    coerce=True,
    strict=False,
)


def validate_rows(rows):
    df = pd.DataFrame(rows)
    try:
        valid = SCHEMA.validate(df, lazy=True)
        invalid = pd.DataFrame(columns=df.columns)
        errors = []
    except SchemaErrors as exc:
        failure_cases = exc.failure_cases
        bad_indices = set()
        if "index" in failure_cases.columns:
            bad_indices = set(failure_cases["index"].dropna().tolist())
        invalid = df.loc[df.index.isin(bad_indices)].copy()
        valid = df.loc[~df.index.isin(bad_indices)].copy()
        errors = failure_cases.to_dict(orient="records")
        invalid["validation_errors"] = invalid.index.map(
            lambda idx: "; ".join(
                str(x.get("check", x.get("failure_case", "validation failure")))
                for x in errors if x.get("index") == idx
            )
        )
    return valid, invalid, errors


def run_validation(rows):
    valid, invalid, errors = validate_rows(rows)
    valid.to_csv(DATA_DIR / "validated_data.csv", index=False)
    invalid.to_csv(DATA_DIR / "invalid_records.csv", index=False)
    # Negative tests are synthetic and are never added to the production dataset.
    sample = rows[0].copy()
    bad_tests = []
    bad = sample.copy(); bad["duration_ms"] = -100; bad_tests.append(bad)
    bad = sample.copy(); bad["album_type"] = "unknown"; bad_tests.append(bad)
    bad = sample.copy(); bad["track_number"] = 0; bad_tests.append(bad)
    detected = 0
    for test in bad_tests:
        try:
            SCHEMA.validate(pd.DataFrame([test]), lazy=True)
        except pa.errors.SchemaErrors:
            detected += 1
    summary = {
        "valid_records": int(len(valid)),
        "invalid_records": int(len(invalid)),
        "synthetic_invalid_tests": len(bad_tests),
        "synthetic_errors_detected": detected,
        "validation_failure_cases": errors,
    }
    (DATA_DIR / "validation_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    print(f"Valid records: {len(valid)} | Invalid records: {len(invalid)}")
    print(f"Synthetic invalid tests detected: {detected}/{len(bad_tests)}")
    if detected != 3:
        raise RuntimeError("Pandera negative validation tests did not all fail as expected.")
    return valid, invalid


if __name__ == "__main__":
    import json
    rows = [json.loads(line) for line in (DATA_DIR / "kafka_messages.jsonl").read_text(encoding="utf-8").splitlines()]
    run_validation(rows)
