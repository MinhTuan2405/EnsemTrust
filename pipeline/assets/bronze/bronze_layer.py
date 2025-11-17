from dagster import asset, AssetExecutionContext, Output, MetadataValue
import pandas as pd
import io
from datetime import datetime


@asset(
    description='Load file from landing zone of MinIO to the bronze layer for raw file storing',
    compute_kind='python',
    required_resource_keys={'minio_resource'},
    group_name='bronze_layer',
)
def ingest_new_file(context: AssetExecutionContext):

    minio_client = context.resources.minio_resource
    
    landing_bucket = "landing"
    bronze_bucket = "bronze"
    
    # Đảm bảo bronze bucket tồn tại
    if not minio_client.bucket_exists(bronze_bucket):
        context.log.info(f"Tạo bronze bucket: {bronze_bucket}")
        minio_client.make_bucket(bronze_bucket)
    
    # Lấy danh sách files từ landing zone
    objects = list(minio_client.list_objects(landing_bucket, recursive=True))
    
    if not objects:
        context.log.warning("Không có file nào trong landing zone")
        return Output(
            value={"files_processed": 0},
            metadata={"status": "no_files"}
        )
    
    processed_files = []
    total_size = 0
    
    for obj in objects:
        file_name = obj.object_name
        file_size = obj.size
        
        try:
            # Đọc file từ landing zone
            context.log.info(f"Đang đọc file: {file_name} ({file_size} bytes)")
            response = minio_client.get_object(landing_bucket, file_name)
            file_data = response.read()
            response.close()
            response.release_conn()
            
            base_name = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name
            extension = file_name.rsplit('.', 1)[1] if '.' in file_name else ''
            new_file_name = f"{base_name}.{extension}" if extension else f"{base_name}"
            
            # Upload vào bronze bucket
            context.log.info(f"Đang upload vào bronze: {new_file_name}")
            minio_client.put_object(
                bronze_bucket,
                new_file_name,
                io.BytesIO(file_data),
                length=len(file_data)
            )
            
            processed_files.append({
                "original_name": file_name,
                "bronze_name": new_file_name,
                "size": file_size
            })
            total_size += file_size
            
            context.log.info(f"Đã ingest thành công: {file_name} -> {new_file_name}")
            
            # Không xóa file khỏi landing zone - giữ lại để backup
            # minio_client.remove_object(landing_bucket, file_name)
            # context.log.info(f"Đã xóa file khỏi landing zone: {file_name}")
            
        except Exception as e:
            context.log.error(f"Lỗi khi xử lý file {file_name}: {str(e)}")
            continue
    
    # Tạo summary
    summary_text = "\n".join([
        f"- {f['original_name']} → {f['bronze_name']} ({f['size']} bytes)"
        for f in processed_files
    ])
    
    context.log.info(f"Hoàn thành! Đã ingest {len(processed_files)} file(s)")
    
    return Output(
        value={
            "files_processed": len(processed_files),
            "total_size": total_size,
            "files": processed_files
        },
        metadata={
            "num_files": len(processed_files),
            "total_size_bytes": total_size,
            "destination_bucket": bronze_bucket,
            "files_summary": MetadataValue.md(f"**Files Processed:**\n\n{summary_text}"),
            "timestamp": datetime.now().isoformat(),
        }
    )



