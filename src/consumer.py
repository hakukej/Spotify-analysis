"""Kafka Consumer: consumes a finite number of Spotify JSON messages."""
import json
import argparse
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from src.config import BOOTSTRAP, TOPIC, GROUP_ID, DATA_DIR


def consume_records(expected_count, timeout_seconds=90):
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id=GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        consumer_timeout_ms=timeout_seconds * 1000,
        max_poll_records=100,
    )
    rows = []
    try:
        for message in consumer:
            rows.append(message.value)
            if len(rows) >= expected_count:
                break
        consumer.commit()
    except KafkaError:
        raise
    finally:
        consumer.close()

    if len(rows) != expected_count:
        raise RuntimeError(
            f"Consumer received {len(rows)} of {expected_count} expected messages. "
            "Check broker, topic, and consumer startup."
        )
    path = DATA_DIR / "kafka_messages.jsonl"
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(f"Kafka messages successfully consumed: {len(rows)}")
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected", type=int, required=True)
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args()
    consume_records(args.expected, args.timeout)


if __name__ == "__main__":
    main()
