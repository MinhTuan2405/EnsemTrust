from dagster import asset, AssetIn, AssetExecutionContext, Output
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import io

_TRANSFORM_GROUP_NAME_ = 'silver_layer'

@asset(
    description='Full loading from bronze layer to silver layer',
    group_name=_TRANSFORM_GROUP_NAME_,
    ins={'read_data_from_kafka_topic': AssetIn('read_data_from_kafka_topic')},
    required_resource_keys={'minio_resource'},
    compute_kind='minio',
)
def load_from_bronze_silver(context: AssetExecutionContext, read_data_from_kafka_topic):
    bucket, object_name = read_data_from_kafka_topic.split('/')
    destination_bucket = 'silver'

    minio_client = context.resources.minio_resource

    data = minio_client.get_object(bucket, object_name).read()
    df = pd.read_parquet(io.BytesIO(data))

    customer_df = df[df['segment'] == 'Consumer']
    corporate_df = df[df['segment'] == 'Corporate']
    home_office_df = df[df['segment'] == 'Home Office']

    data_groups = {
        'customer': customer_df,
        'corporate': corporate_df,
        'home_office': home_office_df,
    }

    for name, part_df in data_groups.items():
        buf = io.BytesIO()
        table = pa.Table.from_pandas(part_df)
        pq.write_table(table, buf)
        buf.seek(0)

        file_name = f"{name}.parquet"
        minio_client.put_object(
            destination_bucket,
            file_name,
            buf,
            length=buf.getbuffer().nbytes,
            content_type='application/octet-stream'
        )

    context.log.info("Successfully loaded data to silver layer.")

    return Output(
        value={
            'customer': customer_df,
            'corporate': corporate_df,
            'home_office': home_office_df
        },
        metadata={
            'source_bucket': bucket,
            'destination_bucket': destination_bucket,
            'total_rows': len(df),
        }
    )
