import os
import time
from confluent_kafka import SerializingProducer
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

bootstrap = os.environ.get("BOOTSTRAP_SERVERS", "broker:29092")
schema_registry_url = os.environ.get("SCHEMA_REGISTRY_URL", "http://schema-registry:8081")
topic = os.environ.get("TOPIC", "purchase.demo")
mode = os.environ.get("MODE", "repro_with_normal")

schema_str = """
{
  "type": "record",
  "name": "DemoRecord",
  "namespace": "demo",
  "fields": [
    {"name": "id", "type": "int"},
    {"name": "name", "type": "string"}
  ]
}
"""

def to_dict(obj, ctx):
    return obj

schema_registry_client = SchemaRegistryClient({"url": schema_registry_url})
value_serializer = AvroSerializer(schema_registry_client, schema_str, to_dict)

producer = SerializingProducer({
    "bootstrap.servers": bootstrap,
    "key.serializer": StringSerializer("utf_8"),
    "value.serializer": value_serializer,
})

def delivery(err, msg):
    if err:
        print(f"delivery failed: {err}")
    else:
        print(f"delivered topic={msg.topic()} partition={msg.partition()} offset={msg.offset()}")

if mode == "repro_tombstone":
    producer.produce(
        topic=topic,
        key="k1",
        value=None,
        headers={"schemaId": "123"},
        on_delivery=delivery,
    )
    producer.flush()

elif mode == "repro_with_normal":
    producer.produce(
        topic=topic,
        key="k1",
        value={"id": 1, "name": "alice"},
        headers={"schemaId": "123"},
        on_delivery=delivery,
    )
    producer.flush()

    producer.produce(
        topic=topic,
        key="k1",
        value=None,
        headers={"schemaId": "123"},
        on_delivery=delivery,
    )
    producer.flush()

elif mode == "changed":
    producer.produce(
        topic=topic,
        key="k1",
        value={"id": 1, "name": "alice"},
        headers={"schemaId": "123"},
        on_delivery=delivery,
    )
    producer.flush()

    producer.produce(
        topic=topic,
        key="k1",
        value=None,
        headers={"schemaId": "123"},
        on_delivery=delivery,
    )
    producer.flush()

else:
    raise RuntimeError(f"Unknown MODE={mode}")

time.sleep(2)
