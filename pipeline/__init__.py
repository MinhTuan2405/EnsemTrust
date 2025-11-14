from dagster import Definitions, load_assets_from_modules

from pipeline.assets.gold import gold_layer
from pipeline.assets.bronze import bronze_layer
from pipeline.assets.silver import silver_layer
from pipeline.resources.minio import minio_resource
import os

def _resolve_bool(env_value: str | None, default: bool = False) -> bool:
    if env_value is None:
        return default
    return env_value.strip().lower() in {"1", "true", "yes", "on"}

minio_endpoint = (
    os.getenv("MINIO_ENDPOINT")
    or os.getenv("AWS_S3_ENDPOINT")
    or "minio:9000"
)
minio_access_key = (
    os.getenv("MINIO_ROOT_USER")
    or os.getenv("AWS_ACCESS_KEY_ID")
    or "admin"
)
minio_secret_key = (
    os.getenv("MINIO_ROOT_PASSWORD")
    or os.getenv("AWS_SECRET_ACCESS_KEY")
    or "admin123"
)
minio_secure = _resolve_bool(os.getenv("MINIO_SECURE"), default=False)


bronze_assets = load_assets_from_modules([bronze_layer])
silver_assets = load_assets_from_modules([silver_layer])
gold_assets = load_assets_from_modules([gold_layer])

all_assets = [*bronze_assets, *silver_assets, *gold_assets]


defs = Definitions(
    assets=all_assets,
    resources={
        "minio_resource": minio_resource.configured({
            "minio_endpoint": minio_endpoint,
            "minio_access_key": minio_access_key,
            "minio_secret_key": minio_secret_key,
            "secure": minio_secure,
        }),
    },
)
