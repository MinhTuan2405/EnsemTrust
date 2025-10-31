from dagster import Definitions, load_assets_from_modules

from pipeline.assets import bronze_layer, silver_layer, gold_layer
from pipeline.resources.kafka import kafka_resource
from pipeline.resources.minio import minio_resource


import os



bronze_assets = load_assets_from_modules([bronze_layer])
silver_assets = load_assets_from_modules([silver_layer])
gold_assets = load_assets_from_modules([gold_layer])

all_assets = [*bronze_assets, *silver_assets, *gold_assets]


defs = Definitions(
    assets=all_assets,
    resources={
        "kafka_resource": kafka_resource.configured({
            "bootstrap_servers": os.getenv("KAFKA_BROKER", "kafka:9092"),
        }),
        "minio_resource": minio_resource.configured({
            "minio_endpoint": os.getenv("MINIO_ENDPOINT", "minio:9000"),
            "minio_access_key": os.getenv("AWS_ACCESS_KEY_ID", "admin"),
            "minio_secret_key": os.getenv("AWS_SECRET_ACCESS_KEY", "admin123"),
            "secure": False,
        }),
    },
)
