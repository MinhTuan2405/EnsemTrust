from dagster import AssetCheckEvaluation, AssetIn, asset, AssetExecutionContext, Output
from pipeline.utils.spark import create_spark_session
from datetime import datetime


@asset(
    description='Load training dataset from silver layer',
    compute_kind='Spark',
    required_resource_keys={'minio_resource'},
    group_name='ML_pipeline',
    ins={
        'transform_news_dataset': AssetIn('transform_news_dataset')
    }
)
def load_data_from_silver(context: AssetExecutionContext, transform_news_dataset):
    
    if transform_news_dataset is None or transform_news_dataset.get("status") != "success":
        context.log.error("Transform dataset not available")
        return None
    
    timestamp = datetime.now()
    app_name = f'load_ml_data_{timestamp.strftime("%Y%m%d_%H%M%S")}'
    
    spark = create_spark_session(app_name)
    spark.conf.set("spark.sql.legacy.timeParserPolicy", "LEGACY")
    context.log.info(f"SparkSession created: {app_name}")
    
    # Get MinIO storage options
    minio_client = context.resources.minio_resource
    storage_options = minio_client.storage_options
    
    # Read parquet from silver bucket using Spark
    silver_path = "s3a://silver/dataset.parquet"
    context.log.info(f"Reading dataset from {silver_path}")
    
    try:
        df = spark.read.parquet(silver_path)
        
        # Cache DataFrame in Spark memory for downstream use
        df.cache()
        
        record_count = df.count()
        columns = df.columns
        
        context.log.info(f"Loaded {record_count} records with {len(columns)} columns")
        context.log.info(f"Columns: {columns}")
        
        # Show sample data
        context.log.info("Sample data:")
        df.show(5, truncate=True)
        
        # Convert to Pandas for serialization (Dagster can't serialize Spark DataFrame)
        pandas_df = df.toPandas()
        
        spark.stop()
        context.log.info("SparkSession stopped, converted to Pandas DataFrame")
        
        return Output(
            value=pandas_df,
            metadata={
                "records": record_count,
                "columns": columns,
                "source_path": silver_path,
                "spark_app": app_name,
                "note": "Converted from Spark DataFrame to Pandas for serialization"
            }
        )
    
    except Exception as e:
        context.log.error(f"Error loading data: {str(e)}")
        spark.stop()
        raise e