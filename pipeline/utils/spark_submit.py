import subprocess
import tempfile
import os
from pathlib import Path

def submit_spark_job(script_content: str, app_name: str = "Dagster Spark Job"):
    """
    Submit a PySpark job to the Spark cluster
    
    Args:
        script_content: Python code to execute on Spark
        app_name: Name of the Spark application
    
    Returns:
        tuple: (stdout, stderr, return_code)
    """
    
    # Create temporary file for the script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(script_content)
        script_path = f.name
    
    try:
        # Spark submit command
        cmd = [
            "spark-submit",
            "--master", "spark://spark-master:7077",
            "--deploy-mode", "client",
            "--conf", "spark.hadoop.fs.s3a.endpoint=http://minio:9000",
            "--conf", f"spark.hadoop.fs.s3a.access.key={os.getenv('MINIO_ROOT_USER', 'admin')}",
            "--conf", f"spark.hadoop.fs.s3a.secret.key={os.getenv('MINIO_ROOT_PASSWORD', 'admin123')}",
            "--conf", "spark.hadoop.fs.s3a.path.style.access=true",
            "--conf", "spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem",
            "--conf", "spark.hadoop.fs.s3a.connection.ssl.enabled=false",
            "--conf", f"spark.app.name={app_name}",
            "--packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262",
            script_path
        ]
        
        # Execute spark-submit
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )
        
        return result.stdout, result.stderr, result.returncode
        
    finally:
        # Clean up temporary file
        if os.path.exists(script_path):
            os.remove(script_path)
