from dagster import AssetIn, Output, asset, AssetExecutionContext
import pandas as pd
from io import BytesIO

def create_loading_dataset_asset(file_name: str):
    origin_file = file_name

    file_name = file_name.replace ('.csv', '').lower ()
    @asset(
        description="Load file from bronze layer to the silver layer then clean them",
        compute_kind='Spark',
        required_resource_keys={'minio_resource'},
        group_name='silver_layer',
        name=f'load_{file_name}_dataset'
    )
    def load_dataset(context: AssetExecutionContext):
        minio_client = context.resources.minio_resource
        default_bucket = 'bronze'

        # Kiểm tra bucket tồn tại
        if not minio_client.bucket_exists(default_bucket):
            context.log.warning(f"Bucket {default_bucket} không tồn tại")
            return

        try:
            file_obj = minio_client.get_object(default_bucket, origin_file)
        except Exception as e:
            context.log.error(f"Không tìm thấy file {origin_file} trong bucket {default_bucket}: {e}")
            return

        df = pd.read_csv(BytesIO(file_obj.read()))

        file_obj.close()
        file_obj.release_conn()

        return Output(
            value=df,
            metadata={
                "records": len(df),
            }
        )

    return load_dataset

fake_dataset_asset = create_loading_dataset_asset ('Fake.csv')
real_dataset_asset = create_loading_dataset_asset ('True.csv')