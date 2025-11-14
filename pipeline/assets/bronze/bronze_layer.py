from dagster import asset, AssetExecutionContext

@asset (
    description='load file from landing zone of MinIO to the bronze layer for raw file storing',
    compute_kind='python',

)
def ingest_new_file (context: AssetExecutionContext):
    ...



