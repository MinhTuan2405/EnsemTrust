from dagster import asset, AssetExecutionContext, Output, MetadataValue, AssetIn
from pipeline.utils.spark import create_spark_session
from pyspark.sql.functions import lit

@asset(
    description="Merge Fake và Real datasets, add label, remove duplicates",
    compute_kind='Spark',
    required_resource_keys={'minio_resource'},
    group_name='silver_layer',
    ins={
        'load_fake_dataset': AssetIn('load_fake_dataset'),
        'load_real_dataset': AssetIn('load_real_dataset'),
    }
)
def transform_news_dataset(
    context: AssetExecutionContext,
    load_fake_dataset,
    load_real_dataset
) -> Output[dict]:
    
    if load_fake_dataset is None or load_real_dataset is None:
        return Output(
            value={"status": "error", "message": "Missing upstream data"},
            metadata={"error": "upstream_data_missing"}
        )
    
    spark = create_spark_session('transform_news_dataset')
    context.log.info("SparkSession created")

    # Convert Pandas -> Spark
    fake_df = spark.createDataFrame(load_fake_dataset)
    real_df = spark.createDataFrame(load_real_dataset)

    # Add label column
    fake_df = fake_df.withColumn("label", lit(0))
    real_df = real_df.withColumn("label", lit(1))

    # Merge using Spark
    combined_df = fake_df.unionByName(real_df)

    # Remove duplicates
    combined_df = combined_df.dropDuplicates()

    # Stats
    total_records = combined_df.count()
    fake_count = combined_df.filter("label == 0").count()
    real_count = combined_df.filter("label == 1").count()

    context.log.info(f"Total records after deduplicate: {total_records}")
    context.log.info(f"Fake count: {fake_count}")
    context.log.info(f"Real count: {real_count}")

    # Save to MinIO
    minio_client = context.resources.minio_resource
    silver_bucket = 'silver'

    if not minio_client.bucket_exists(silver_bucket):
        minio_client.make_bucket(silver_bucket)

    output_path = f"s3a://{silver_bucket}/combined_news.parquet"

    try:
        combined_df.coalesce(1).write.mode("overwrite").parquet(output_path)

        # Fetch file size
        objects = list(minio_client.list_objects(silver_bucket, recursive=True))
        parquet_files = [obj for obj in objects if obj.object_name.endswith('.parquet')]
        total_size = sum(obj.size for obj in parquet_files)

        spark.stop()

        return Output(
            value={
                "status": "success",
                "output_path": output_path,
                "total_records": total_records,
                "fake_count": fake_count,
                "real_count": real_count,
                "file_size_bytes": total_size,
            },
            metadata={
                "total_records": total_records,
                "fake_count": fake_count,
                "real_count": real_count,
                "fake_percentage": MetadataValue.float(fake_count / total_records * 100),
                "real_percentage": MetadataValue.float(real_count / total_records * 100),
                "output_path": output_path,
                "file_size_bytes": total_size,
            }
        )

    except Exception as e:
        spark.stop()
        raise e
