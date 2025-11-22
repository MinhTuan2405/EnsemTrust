from dagster import asset, AssetExecutionContext, Output, MetadataValue, AssetIn
from pipeline.utils.spark import create_spark_session
from pyspark.sql.functions import lit, to_timestamp, coalesce, date_format, col, create_map, length
from io import BytesIO
import pyarrow.parquet as pq
import pyarrow as pa

from datetime import datetime

@asset(
    description="Merge Fake và Real datasets, add label, remove duplicates",
    compute_kind='Spark',
    required_resource_keys={'minio_resource'},
    group_name='silver_layer',
    ins={
        'load_fake_dataset': AssetIn('load_fake_dataset'),
        'load_true_dataset': AssetIn('load_true_dataset'),
    }
)
def transform_news_dataset(
    context: AssetExecutionContext,
    load_fake_dataset,
    load_true_dataset
) -> Output[dict]:
    
    if load_fake_dataset is None or load_true_dataset is None:
        return Output(
            value={"status": "error", "message": "Missing upstream data"},
            metadata={"error": "upstream_data_missing"}
        )
    
    timestamp = datetime.now()
    app_name = f'transform_news_dataset_{timestamp.strftime("%Y%m%d_%H%M%S")}'
    
    spark = create_spark_session(app_name)
    # Set legacy time parser for compatibility with various date formats
    spark.conf.set("spark.sql.legacy.timeParserPolicy", "LEGACY")

    context.log.info(f"SparkSession created: {app_name}")

    # Convert Pandas -> Spark
    fake_df = spark.createDataFrame(load_fake_dataset)
    real_df = spark.createDataFrame(load_true_dataset)

    # Add label column
    fake_df = fake_df.withColumn("label", lit(0))
    real_df = real_df.withColumn("label", lit(1))

    # Merge using Spark
    df = fake_df.unionByName(real_df)

    # Remove duplicates
    df = df.dropDuplicates()

    # Parse date column - try multiple formats    
    df = df.withColumn(
        "date_parsed",
        coalesce(
            to_timestamp("date", "MMM d, yyyy"),   # "Dec 4, 2017"
            to_timestamp("date", "MMMM d, yyyy"),  # "January 21, 2016"
            to_timestamp("date", "yyyy-MM-dd"),
            to_timestamp("date", "dd/MM/yyyy"),
            to_timestamp("date", "MM-dd-yyyy"),
            to_timestamp("date", "M/d/yyyy"),
            to_timestamp("date", "d-MMM-yy")
        )
    )
    
    # Replace original date column
    df = df.withColumn("date", col("date_parsed")).drop("date_parsed")

    # Extract month and year
    df = df.withColumn("month", date_format(col("date"), "MM"))
    df = df.withColumn("year", date_format(col("date"), "yyyy"))
    df = df.withColumn("year_month", date_format(col("date"), "yyyy-MM"))

    mapping = {
        "Government News": "Politics",
        "politics": "Politics",
        "politicsNews": "Politics",
        "left-news": "Politics",
        "worldnews": "World",
        "Middle-east": "World",
        "US_News": "US",
        "News": "General"
    }

    mapping_expr = create_map([lit(x) for kv in mapping.items() for x in kv])

    df = df.withColumn(
        "subject",
        coalesce(mapping_expr[col("subject")], col("subject"))
    )

    # add length of the title and text
    df = df.withColumn("text_length", length(col("text")))
    df = df.withColumn("title_length", length(col("title")))

    context.log.info("Transformation complete, converting to Pandas for MinIO upload...")
    
    # Convert back to Pandas for reliable MinIO upload
    result_df = df.toPandas()
    
    spark.stop()
    context.log.info("SparkSession stopped")

    # Save to MinIO using pandas/pyarrow
    minio_client = context.resources.minio_resource
    silver_bucket = 'silver'

    if not minio_client.bucket_exists(silver_bucket):
        minio_client.make_bucket(silver_bucket)

    output_file = "dataset.parquet"

    try:
        # Convert to Parquet in memory
        table = pa.Table.from_pandas(result_df)
        parquet_buffer = BytesIO()
        pq.write_table(table, parquet_buffer)
        parquet_buffer.seek(0)
        
        # Upload to MinIO
        file_size = len(parquet_buffer.getvalue())
        minio_client.put_object(
            silver_bucket,
            output_file,
            parquet_buffer,
            length=file_size,
            content_type='application/octet-stream'
        )

        context.log.info(f"Saved {output_file} to MinIO silver bucket ({file_size} bytes)")

        return Output(
            value={
                "status": "success",
                "output_path": f"s3a://{silver_bucket}/{output_file}",
                "file_size_bytes": file_size,
                "records": len(result_df)
            },
            metadata={
                "output_path": f"s3a://{silver_bucket}/{output_file}",
                "file_size_bytes": file_size,
                "records": len(result_df),
                "columns": result_df.columns.tolist()
            }
        )

    except Exception as e:
        context.log.error(f"Error saving to MinIO: {str(e)}")
        raise e