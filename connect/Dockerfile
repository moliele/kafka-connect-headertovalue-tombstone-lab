FROM confluentinc/cp-kafka-connect:7.9.3

RUN confluent-hub install --no-prompt confluentinc/connect-transforms:1.4.3

RUN mkdir -p /usr/share/confluent-hub-components/debezium-connector-postgres \
 && curl -fSL https://repo1.maven.org/maven2/io/debezium/debezium-connector-postgres/2.7.3.Final/debezium-connector-postgres-2.7.3.Final-plugin.tar.gz \
    -o /tmp/debezium-connector-postgres-2.7.3.Final-plugin.tar.gz \
 && tar -xzf /tmp/debezium-connector-postgres-2.7.3.Final-plugin.tar.gz \
    -C /usr/share/confluent-hub-components/debezium-connector-postgres \
    --strip-components=1 \
 && rm -f /tmp/debezium-connector-postgres-2.7.3.Final-plugin.tar.gz
