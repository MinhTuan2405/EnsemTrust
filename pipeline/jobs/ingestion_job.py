"""
Ingestion Job Definitions
Định nghĩa các job cho việc ingest dữ liệu từ landing zone vào bronze layer
"""
from dagster import (
    define_asset_job,
    AssetSelection,
)


# Job để ingest file từ landing zone
ingest_file_job = define_asset_job(
    name="ingest_file_from_landing",
    description="Job để ingest file mới từ landing zone vào bronze layer",
    selection=AssetSelection.assets("ingest_new_file"),
)


# Job để xử lý toàn bộ bronze layer
bronze_processing_job = define_asset_job(
    name="bronze_layer_processing",
    description="Xử lý toàn bộ bronze layer assets",
    selection=AssetSelection.groups("bronze_layer"),
)
