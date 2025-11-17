from dagster import asset, AssetExecutionContext, Output, AssetIn
from io import BytesIO
import pandas as pd
from deltalake import write_deltalake
import trino
import os

@asset(
    description="Load transformed dataset from silver layer and save as Delta table in gold layer",
    compute_kind='Delta Lake',
    required_resource_keys={'minio_resource'},
    group_name='gold_layer',
    ins={
        'transform_news_dataset': AssetIn('transform_news_dataset')
    }
)
def gold_news_dataset(
    context: AssetExecutionContext,
    transform_news_dataset
) -> Output[dict]:
    
    if transform_news_dataset is None or transform_news_dataset.get("status") != "success":
        return Output(
            value={"status": "error", "message": "Transform dataset not available"},
            metadata={"error": "upstream_data_missing"}
        )
    
    minio_client = context.resources.minio_resource
    silver_bucket = 'silver'
    gold_bucket = 'gold'
    
    # Create gold bucket if not exists
    if not minio_client.bucket_exists(gold_bucket):
        minio_client.make_bucket(gold_bucket)
        context.log.info(f"Created bucket: {gold_bucket}")
    
    # Read parquet from silver layer
    context.log.info("Reading dataset.parquet from silver bucket...")
    file_obj = minio_client.get_object(silver_bucket, "dataset.parquet")
    df = pd.read_parquet(BytesIO(file_obj.read()))
    file_obj.close()
    file_obj.release_conn()
    
    context.log.info(f"Loaded {len(df)} records from silver layer")
    
    # Write to Delta Lake in gold bucket
    delta_path = f"s3a://{gold_bucket}/news_dataset"
    storage_options = minio_client.storage_options
    
    context.log.info(f"Writing Delta table to {delta_path}...")
    
    try:
        write_deltalake(
            delta_path,
            df,
            mode="overwrite",
            storage_options=storage_options
        )
        
        context.log.info(f"Successfully wrote Delta table to {delta_path}")
        
        # Register table in Hive Metastore via Trino
        try:
            context.log.info("Registering Delta table in Hive Metastore via Trino...")
            
            conn = trino.dbapi.connect(
                host='trino',
                port=8080,
                user='admin',
                catalog='delta',
                schema='default'
            )
            cursor = conn.cursor()
            
            # Create schema if not exists
            cursor.execute("CREATE SCHEMA IF NOT EXISTS delta.gold WITH (location = 's3a://gold/')")
            context.log.info("Ensured schema delta.gold exists")
            
            # Drop table if exists (unregister first)
            try:
                cursor.execute("CALL delta.system.unregister_table('gold', 'news_dataset')")
                context.log.info("Unregistered existing table")
            except:
                pass  # Table doesn't exist yet
            
            # Register Delta table using system procedure
            cursor.execute("CALL delta.system.register_table('gold', 'news_dataset', 's3a://gold/news_dataset')")
            context.log.info("Registered Delta table via system.register_table()")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            context.log.warning(f"Failed to register table in Hive Metastore: {str(e)}")
            context.log.warning("Table created but not registered. You can query directly via Delta connector.")
        
        return Output(
            value={
                "status": "success",
                "delta_path": delta_path,
                "records": len(df),
                "columns": df.columns.tolist()
            },
            metadata={
                "delta_path": delta_path,
                "records": len(df),
                "columns": df.columns.tolist(),
                "table_name": "news_dataset"
            }
        )
    
    except Exception as e:
        context.log.error(f"Error writing Delta table: {str(e)}")
        raise e
