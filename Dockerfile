FROM confluentinc/cp-server-connect-base:7.9.3

RUN confluent-hub install --no-prompt confluentinc/connect-transforms:1.4.3
RUN confluent-hub install --no-prompt debezium/debezium-connector-postgresql:2.7.3.Final
