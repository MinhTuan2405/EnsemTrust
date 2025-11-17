from dagster import Definitions, load_assets_from_modules

from pipeline.assets.gold import gold_layer
from pipeline.assets.bronze import bronze_layer
from pipeline.assets.silver import get_dataset, transform
from pipeline.resources.minio import minio_resource

from pipeline.sensors.file_sensor import (
    landing_zone_file_sensor,
)
from pipeline.jobs.ingestion_job import (
    ingest_file_job,
)

import os



bronze_assets = load_assets_from_modules([bronze_layer])
silver_assets = load_assets_from_modules([get_dataset, transform])
gold_assets = load_assets_from_modules([gold_layer])

all_assets = [*bronze_assets, *silver_assets, *gold_assets]


defs = Definitions(
    assets=all_assets,
    sensors=[
        landing_zone_file_sensor,  
    ],
    jobs=[
        ingest_file_job,
    ],
    resources={
        "minio_resource": minio_resource.configured({
            "minio_endpoint": os.getenv("MINIO_ENDPOINT", "minio:9000"),
            "minio_access_key": os.getenv("MINIO_ROOT_USER", "admin"),
            "minio_secret_key": os.getenv("MINIO_ROOT_PASSWORD", "admin123"),
            "secure": False,
        }),
    },
)
