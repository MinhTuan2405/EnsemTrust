from dagster import asset, AssetExecutionContext, AssetIn, MetadataValue, Output
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from kafka import KafkaProducer, KafkaConsumer
import json
import io

_INGEST_GROUP_NAME_ = 'bronze_layer'
_KAFKA_TOPIC_ = 'raw_csv'

@asset (
    description='Read the csv data file then load into minio as a parquet formatted file',
    group_name=_INGEST_GROUP_NAME_,
    compute_kind="pandas",
)
def ingest_data (context: AssetExecutionContext):
    df = pd.read_csv ('pipeline/test_data/customers.csv')

    context.log.info (df.head (10))

    return Output (
        df,
        metadata= {
            'colums': list (df.columns),
            'total_record': len (df)
        }
    )
    
@asset (
    description='Load ingested data to the kafka topic',
    group_name=_INGEST_GROUP_NAME_,
    compute_kind='kafka',
    required_resource_keys={"kafka_resource"},
    ins= {
        'ingest_data': AssetIn ('ingest_data')
    }
)
def load_data_to_kafka_topic (context: AssetExecutionContext, ingest_data):
    kafka_cfg = context.resources.kafka_resource

    producer = KafkaProducer(
        bootstrap_servers=kafka_cfg["bootstrap_servers"],
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    records = ingest_data.to_dict(orient="records")
    for record in records:
        producer.send(_KAFKA_TOPIC_, value=record)
    producer.flush()
    producer.close()

    context.log.info (f"sent {len(records)} records to Kafka topic '{_KAFKA_TOPIC_}'")

    output_data = {
        "topic": _KAFKA_TOPIC_,
        "record_count": len(records)
    }

    return Output (
        output_data, 
        metadata={
            "topic": _KAFKA_TOPIC_,
            "record_count": len(records),
            "preview": MetadataValue.md(ingest_data.head().to_markdown())
        }
    )

@asset (
    description='load all data from kafka topic then write into the minio bucket',
    compute_kind='minio',
    ins={
        'load_data_to_kafka_topic': AssetIn ('load_data_to_kafka_topic')
    },
    required_resource_keys={'minio_resource', 'kafka_resource'},
    group_name=_INGEST_GROUP_NAME_
)
def read_data_from_kafka_topic (context: AssetExecutionContext, load_data_to_kafka_topic): # <--- Biến này BÂY GIỜ là một dictionary
    minio_client = context.resources.minio_resource
    kafka_cfg = context.resources.kafka_resource
    bucket = 'bronze'

    kafka_info = load_data_to_kafka_topic
    topic_name = kafka_info["topic"]
    expected_record_count = kafka_info["record_count"]
    
    if expected_record_count == 0:
        context.log.info("No records to process from Kafka topic.")
        df = pd.DataFrame()
    else:
        consumer = KafkaConsumer(
            topic_name, 
            bootstrap_servers=kafka_cfg["bootstrap_servers"],
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id="dagster-etl",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),

            consumer_timeout_ms=10000 
        )

        messages = []
        try:
            for msg in consumer:
                messages.append(msg.value)
                if len(messages) >= expected_record_count: 
                    break
        except StopIteration:
            context.log.warning(f"Consumer timed out. Expected {expected_record_count} records, but only got {len(messages)}.")
        finally:
            consumer.close()

        df = pd.DataFrame(messages)

    object_name = 'customer.parquet'

    buf = io.BytesIO()
    table = pa.Table.from_pandas(df)
    pq.write_table(table, buf)
    buf.seek(0)

    minio_client.put_object(bucket, object_name, buf, length=buf.getbuffer().nbytes)

    return Output (
        f'bronze/{object_name}',
        metadata={
            "file_url": f'./bronze/{object_name}',
            "rows": len(df),
            "columns": list(df.columns) if not df.empty else [],
            "size_bytes": buf.getbuffer().nbytes,
        }
    )