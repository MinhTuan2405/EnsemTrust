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
        .getOrCreate()
    )
    
    spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")
    spark.conf.set("spark.sql.execution.arrow.pyspark.fallback.enabled", "true")

    return spark