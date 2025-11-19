from pyspark.sql import SparkSession
import os
from dotenv import load_dotenv

load_dotenv()

def create_spark_session(app_name):
    """
    Create a SparkSession that connects to remote Spark cluster.
    This requires PySpark to be installed in the Dagster container.
    """
    
    spark = (
        SparkSession.builder
        .appName(app_name)
        .master("spark://spark-master:7077")
        .config("spark.pyspark.python", "python3.10")
        .config("spark.pyspark.driver.python", "python3.10")
        # JAR packages for S3/MinIO access
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262,io.delta:delta-spark_2.12:3.1.0")
        # S3/MinIO configuration
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
        .config("spark.hadoop.fs.s3a.access.key", os.getenv("AWS_ACCESS_KEY_ID", "admin"))
        .config("spark.hadoop.fs.s3a.secret.key", os.getenv("AWS_SECRET_ACCESS_KEY", "admin123"))
        # Delta Lake
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        # Driver configuration
        .config("spark.driver.host", "dagster")
        .config("spark.driver.memory", "2g")
        .getOrCreate()
    )
    
    spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")
    spark.conf.set("spark.sql.execution.arrow.pyspark.fallback.enabled", "true")

    return spark