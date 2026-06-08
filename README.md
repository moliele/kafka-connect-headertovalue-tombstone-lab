
### ⚠️ IMPORTANT: LAB DISCLAIMER
> **DISCLAIMER:** This repository and the configurations provided here are for **educational and lab purposes only**. It is **not** production-ready.
> Do not use this in production.

# HeaderToValue tombstone lab with Avro

This repository reproduces a Kafka Connect tombstone error when the SMT chain is `HoistField -> HeaderToValue`, and shows a change using `RecordIsTombstone`.

The lab uses:

- Kafka + Schema Registry
- Kafka Connect
- Avro
- FileStreamSinkConnector for simple end-to-end local validation

## Goal

This lab demonstrates two scenarios:

### Repro

- a normal Avro message is processed successfully
- a tombstone message (`value=null`) hits the `HoistField -> HeaderToValue` chain
- the tombstone path fails

### Change

- normal Avro messages still work
- tombstones are excluded from both SMTs with `RecordIsTombstone`
- the connector no longer fails on tombstones

## Repository structure

```text
header-to-value-lab/
├── docker-compose.yml
├── connect/
│   └── Dockerfile
├── config/
│   ├── connector-repro.json
│   └── connector-changed.json
├── producer/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── produce.py
├── out/
└── README.md
```

## How to run

### 1. Build and start the environment

```bash
mkdir -p out
docker compose build --no-cache connect producer
docker compose up -d
```

### 2. Verify FileStream is available

```bash
curl -s http://localhost:8083/connector-plugins | jq '.[].class' | grep FileStream
```

You should see `org.apache.kafka.connect.file.FileStreamSinkConnector`.

## Lab flow

### 1. Create the repro connector

```bash
curl -X PUT \
  -H "Content-Type: application/json" \
  --data @config/connector-repro.json \
  http://localhost:8083/connectors/fs-h2v-repro/config
```

### 2. Produce a normal message and then a tombstone

```bash
docker compose run --rm \
  -e MODE=repro_with_normal \
  producer
```

### 3. Inspect the result

Connector logs:

```bash
docker compose logs connect | grep -E "HeaderToValue|Only Struct|null|tombstone"
```

FileStream output:

```bash
cat out/filestream-repro.txt
```

### Expected repro behavior

- the normal Avro message should be written to `out/filestream-repro.txt`
- the tombstone should trigger the failure path

## Lab Changed flow

### 1. Remove the repro connector

```bash
curl -X DELETE http://localhost:8083/connectors/fs-h2v-repro
rm -f out/filestream-repro.txt out/filestream-changed.txt
```

### 2. Create the changed connector

```bash
curl -X PUT \
  -H "Content-Type: application/json" \
  --data @config/connector-changed.json \
  http://localhost:8083/connectors/fs-h2v-changed/config
```

### 3. Run the changed scenario

```bash
docker compose run --rm \
  -e MODE=changed \
  producer
```

### 4. Inspect the result

Connector logs:

```bash
docker compose logs connect | grep -E "HeaderToValue|Only Struct|null|tombstone"
```

FileStream output:

```bash
cat out/filestream-changed.txt
```

### Expected changed behavior

- the normal Avro message should be written successfully
- the tombstone should not break the connector
- the SMT chain should be skipped for tombstones

## Why it works

The change does not make `HeaderToValue` support tombstones.

Instead, it uses `RecordIsTombstone` so that:

- normal messages still go through `HoistField` and `HeaderToValue`
- tombstones bypass those SMTs entirely

That preserves the delete semantics of tombstones while avoiding the failing transformation path.

## What `HoistField` does

`HoistField` wraps the current value inside a new field, typically `__payload`.

Conceptually:

### Before

```json
{
  "id": 1,
  "name": "alice"
}
```

### After

```json
{
  "__payload": {
    "id": 1,
    "name": "alice"
  }
}
```

## What removing `HoistField` means

If you remove `HoistField`:

- the payload is no longer wrapped under `__payload`
- `HeaderToValue` writes directly into the root value structure
- the SMT chain becomes simpler

Conceptually:

### With `HoistField`

```json
{
  "__payload": {
    "id": 1,
    "name": "alice"
  },
  "schema_id": "123"
}
```

### Without `HoistField`

```json
{
  "id": 1,
  "name": "alice",
  "schema_id": "123"
}
```

## Tombstones

If a record must remain a true tombstone, its full value must stay `null`.

That means you cannot insert extra fields into the value and still preserve tombstone semantics.


## Versions used

- Confluent Platform `7.9.3`
- `confluentinc/connect-transforms:1.4.3`
- Debezium plugin `2.7.3.Final`

## Sources

- [debezium HeaderToValue](https://debezium.io/documentation/reference/stable/transformations/header-to-value.html)
- [Kafka Connect HoistField SMT Usage Reference for Confluent Platform](https://docs.confluent.io/kafka-connectors/transforms/current/hoistfield.html)
