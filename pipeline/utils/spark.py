from pyspark.sql import SparkSession
import os
from dotenv import load_dotenv

load_dotenv ()

def create_spark_session (app_name):
    spark = (
    SparkSession.builder
        .appName(app_name)
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


    return spark