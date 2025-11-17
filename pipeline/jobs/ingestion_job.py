from dagster import (
    define_asset_job,
    AssetSelection,
)

ingest_file_job = define_asset_job(
    name="ingest_file_from_landing",
    description="Job để ingest file mới từ landing zone vào bronze layer",
    selection=AssetSelection.assets("ingest_new_file"),
)

