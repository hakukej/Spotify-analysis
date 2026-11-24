"""Kafka Producer: publishes each collected Spotify record as JSON."""
import json
from kafka import KafkaProducer
from kafka.errors import KafkaError
from src.config import BOOTSTRAP, TOPIC, DATA_DIR


def publish_records(records):
    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP,
        value_serializer=lambda value: json.dumps(value, ensure_ascii=False).encode("utf-8"),
        acks="all",
        retries=5,
        request_timeout_ms=30000,
    )
    sent = 0
    try:
        for record in records:
            future = producer.send(TOPIC, value=record)
            future.get(timeout=30)
            sent += 1
        producer.flush()
    except (KafkaError, Exception):
        producer.close()
        raise
    finally:
        producer.close()
    print(f"Kafka messages successfully published: {sent}")
    return sent


def main():
    import json
    path = DATA_DIR / "raw_data.json"
    if not path.exists():
        raise FileNotFoundError("Run API collection first: python -m src.api_client")
    records = json.loads(path.read_text(encoding="utf-8"))
    publish_records(records)


if __name__ == "__main__":
    main()
