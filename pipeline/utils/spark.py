from pyspark.sql import SparkSession
import os
from dotenv import load_dotenv

load_dotenv()

def create_spark_session(app_name):
    """
    Create a SparkSession that connects to remote Spark cluster.
    This requires PySpark to be installed in the Dagster container.
    """
    
    # Get Python executable path
    import sys
    python_path = sys.executable
    
    spark = (
        SparkSession.builder
        .appName(app_name)
        .master("spark://spark-master:7077")
        .config("spark.submit.deployMode", "client")
        .config("spark.driver.host", "dagster")
        .config("spark.driver.port", "7078")
        .config("spark.driver.bindAddress", "0.0.0.0")
        .config("spark.driver.memory", "2g")
        .config("spark.executor.memory", "2g")
        # Fix Python version mismatch - force workers to use same Python as driver
        .config("spark.pyspark.python", python_path)
        .config("spark.pyspark.driver.python", python_path)
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
        .config("spark.hadoop.fs.s3a.access.key", os.getenv("MINIO_ROOT_USER", "admin"))
        .config("spark.hadoop.fs.s3a.secret.key", os.getenv("MINIO_ROOT_PASSWORD", "admin123"))
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262")
        .getOrCreate()
    )
    
    spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")
    spark.conf.set("spark.sql.execution.arrow.pyspark.fallback.enabled", "true")

    return spark