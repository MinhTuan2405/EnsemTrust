"""
Transform Silver Layer - Merge and Save Combined Dataset
Hợp nhất Fake và Real datasets, thêm labels, và lưu dưới dạng Parquet sử dụng Spark
"""
from dagster import asset, AssetExecutionContext, Output, MetadataValue, AssetIn
from datetime import datetime
from pyspark.sql import SparkSession
import pandas as pd
import os


@asset(
    description="Merge Fake và Real datasets, thêm labels và lưu thành Parquet sử dụng Spark",
    compute_kind='Spark',
    required_resource_keys={'minio_resource'},
    group_name='silver_layer',
    ins={
        'load_Fake.csv': AssetIn('load_Fake.csv'),
        'load_Real.csv': AssetIn('load_Real.csv'),
    }
)
def combined_news_dataset(
    context: AssetExecutionContext,
    **kwargs
) -> Output[dict]:
    """
    Đọc Fake.csv và Real.csv từ upstream assets,
    thêm labels (0: fake, 1: real),
    merge lại và lưu thành file Parquet duy nhất sử dụng Spark
    """
    
    minio_client = context.resources.minio_resource
    
    # Lấy data từ upstream assets
    fake_df = kwargs.get('load_Fake.csv')
    real_df = kwargs.get('load_Real.csv')
    
    if fake_df is None or real_df is None:
        context.log.error("Không thể load được datasets từ upstream assets")
        return Output(
            value={"status": "error", "message": "Missing upstream data"},
            metadata={"error": "upstream_data_missing"}
        )
    
    context.log.info(f"Loaded Fake dataset: {len(fake_df)} records")
    context.log.info(f"Loaded Real dataset: {len(real_df)} records")
    
    # Thêm label cho mỗi dataset
    fake_df['label'] = 0  # 0 = Fake
    real_df['label'] = 1  # 1 = Real
    
    # Merge hai datasets
    combined_df = pd.concat([fake_df, real_df], ignore_index=True)
    
    # Shuffle data
    combined_df = combined_df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    total_records = len(combined_df)
    fake_count = (combined_df['label'] == 0).sum()
    real_count = (combined_df['label'] == 1).sum()
    
    context.log.info(f"📊 Combined dataset: {total_records} records")
    context.log.info(f"   - Fake: {fake_count} ({fake_count/total_records*100:.1f}%)")
    context.log.info(f"   - Real: {real_count} ({real_count/total_records*100:.1f}%)")
    
    # Tạo SparkSession đơn giản
    spark = (
        SparkSession.builder
            .appName("EnsemTrust-Combined-Dataset")
            .master("spark://spark-master:7077")
            .config("spark.hadoop.fs.s3a.endpoint", f"http://minio:9000")
            .config("spark.hadoop.fs.s3a.access.key", os.getenv("MINIO_ROOT_USER", "admin"))
            .config("spark.hadoop.fs.s3a.secret.key", os.getenv("MINIO_ROOT_PASSWORD", "admin123"))
            .config("spark.hadoop.fs.s3a.path.style.access", "true")
            .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
            .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
            .getOrCreate()
    )
    
    spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")
    spark.conf.set("spark.sql.execution.arrow.pyspark.fallback.enabled", "true")
    
    context.log.info("✅ SparkSession created")
    
    # Convert Pandas DataFrame to Spark DataFrame
    spark_df = spark.createDataFrame(combined_df)
    
    # Đảm bảo silver bucket tồn tại
    silver_bucket = 'silver'
    if not minio_client.bucket_exists(silver_bucket):
        context.log.info(f"🪣 Tạo silver bucket: {silver_bucket}")
        minio_client.make_bucket(silver_bucket)
    
    # Lưu file Parquet vào MinIO sử dụng Spark
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"s3a://{silver_bucket}/combined_news_{timestamp}.parquet"
    
    try:
        context.log.info(f"💾 Đang lưu Parquet file với Spark: {output_path}")
        
        # Write to S3/MinIO using Spark
        spark_df.coalesce(1).write \
            .mode("overwrite") \
            .parquet(output_path)
        
        context.log.info(f"✅ Đã lưu thành công: {output_path}")
        
        # Get file size (approximate from MinIO)
        objects = list(minio_client.list_objects(silver_bucket, recursive=True))
        parquet_files = [obj for obj in objects if 'combined_news' in obj.object_name and obj.object_name.endswith('.parquet')]
        total_size = sum(obj.size for obj in parquet_files)
        
        result = {
            "status": "success",
            "output_path": output_path,
            "total_records": total_records,
            "fake_count": int(fake_count),
            "real_count": int(real_count),
            "file_size_bytes": total_size,
        }
        
        # Stop Spark session
        spark.stop()
        context.log.info("🛑 SparkSession stopped")
        
        return Output(
            value=result,
            metadata={
                "total_records": total_records,
                "fake_count": int(fake_count),
                "real_count": int(real_count),
                "fake_percentage": MetadataValue.float(fake_count/total_records*100),
                "real_percentage": MetadataValue.float(real_count/total_records*100),
                "output_path": output_path,
                "file_size_bytes": total_size,
                "columns": MetadataValue.text(", ".join(combined_df.columns)),
                "distribution": MetadataValue.md(f"""
**Dataset Distribution:**
- Total Records: {total_records:,}
- Fake News: {fake_count:,} ({fake_count/total_records*100:.1f}%)
- Real News: {real_count:,} ({real_count/total_records*100:.1f}%)

**Output:**
- Format: Parquet
- Engine: Apache Spark
- Location: {output_path}
- Size: {total_size:,} bytes
                """),
            }
        )
        
    except Exception as e:
        context.log.error(f"❌ Lỗi khi lưu file: {str(e)}")
        spark.stop()
        raise
