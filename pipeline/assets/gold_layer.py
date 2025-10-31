from datetime import datetime

from dagster import AssetExecutionContext, AssetIn, Output, asset
from deltalake import DeltaTable, write_deltalake
import pandas as pd

try:
    from deltalake.exceptions import DeltaError
except ImportError:  # deltalake<0.17 does not expose this in exceptions module
    try:
        from deltalake import DeltaError  # type: ignore[attr-defined]
    except ImportError:  # pragma: no cover - fallback for very old versions
        class DeltaError(Exception):  # type: ignore[override]
            """Fallback DeltaError when not provided by the installed deltalake package."""
            pass

_TRANSFORM_GROUP_NAME_ = 'gold_layer'


def create_gold_asset(table_name: str):

    @asset(
        name=f"load_{table_name}_from_silver_gold",
        description=f"Load {table_name} data from silver layer and write to Delta Table in gold layer",
        group_name=_TRANSFORM_GROUP_NAME_,
        ins={'load_from_bronze_silver': AssetIn('load_from_bronze_silver')},
        required_resource_keys={'minio_resource'},
        compute_kind='minio',
    )
    def _asset_fn(context: AssetExecutionContext, load_from_bronze_silver):
        df: pd.DataFrame = load_from_bronze_silver[table_name]
        context.log.info(f"Loaded {table_name} data with {len(df)} rows from silver layer")

        minio_resource = context.resources.minio_resource
        storage_options = minio_resource.storage_options

        bucket_name = "gold"
        if not minio_resource.bucket_exists(bucket_name):
            context.log.info(f"Bucket '{bucket_name}' not found. Creating it now.")
            minio_resource.make_bucket(bucket_name)

        table_path = f"s3://{bucket_name}/delta/{table_name}"

        try:
            _ = DeltaTable(table_path, storage_options=storage_options)
            write_mode = "overwrite"  # chuyển sang "append" nếu cần cộng dồn dữ liệu
            context.log.info(f"Existing Delta table found at {table_path}, mode={write_mode}")
        except DeltaError:
            write_mode = "overwrite"
            context.log.info(f"No existing Delta table found, creating new one at {table_path}")
        except Exception as exc:
            context.log.error(f"Unexpected error while checking Delta table at {table_path}: {exc}")
            raise

        write_deltalake(
            table_path,
            df,
            mode=write_mode,
            storage_options=storage_options,
        )

        context.log.info(f"Delta Table for {table_name} written successfully to {table_path}")

        return Output(
            value={"path": table_path, "rows": len(df)},
            metadata={
                "destination_bucket": "gold",
                "delta_table_path": table_path,
                "record_count": len(df),
                "write_mode": write_mode,
                "timestamp": datetime.now().isoformat(),
            },
        )

    return _asset_fn


tables = ['customer', 'corporate', 'home_office']
gold_assets = [create_gold_asset(t) for t in tables]


