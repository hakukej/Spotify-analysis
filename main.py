"""End-to-end SIS2 pipeline coordinator."""
import json
import subprocess
import sys
import time
from pathlib import Path

from src.api_client import SpotifyClient
from src.producer import publish_records
from src.consumer import consume_records
from src.validator import run_validation
from src.cleaner import clean_transform
from src.loader import verify_idempotency
from src.analysis import run_eda
from src.config import DATA_DIR


def run_pipeline():
    print("\n[1/7] Collecting Spotify API records")
    records = SpotifyClient().collect()

    print("\n[2/7] Starting finite Kafka consumer")
    consumer_process = subprocess.Popen([
        sys.executable, "-m", "src.consumer",
        "--expected", str(len(records)), "--timeout", "120"
    ])
    time.sleep(4)  

    print("\n[3/7] Publishing records to Kafka")
    published = publish_records(records)
    return_code = consumer_process.wait(timeout=140)
    if return_code != 0:
        raise RuntimeError("Kafka consumer process failed.")

    print("\n[4/7] Validating consumed records with Pandera")
    lines = (DATA_DIR / "kafka_messages.jsonl").read_text(encoding="utf-8").splitlines()
    consumed = [json.loads(line) for line in lines]
    valid, invalid = run_validation(consumed)

    print("\n[5/7] Cleaning and transforming")
    cleaned, grouped, melted = clean_transform(valid)

    print("\n[6/7] Loading SQLite and checking idempotency")
    db_result = verify_idempotency(cleaned)

    print("\n[7/7] Exploratory data analysis")
    findings = run_eda(cleaned)

    summary = {
        "api_collected": len(records),
        "kafka_published": published,
        "kafka_consumed": len(consumed),
        "valid_records": len(valid),
        "invalid_records": len(invalid),
        "cleaned_records": len(cleaned),
        "sqlite_records": db_result["stored_after_second_load"],
        "idempotency_passed": db_result["idempotency_passed"],
        "eda": findings,
    }
    (DATA_DIR / "pipeline_metrics.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    print("\nPIPELINE COMPLETED")
    print(json.dumps(summary, indent=2, default=str))
    return summary


if __name__ == "__main__":
    run_pipeline()
