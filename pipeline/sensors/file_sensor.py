"""
File Sensor - Monitor MinIO Landing Zone for New Files
Sensor này theo dõi landing zone trong MinIO và trigger job khi có file mới
"""
from dagster import (
    sensor,
    RunRequest,
    SensorEvaluationContext,
    DefaultSensorStatus,
    AssetMaterialization,
    SensorResult,
)
from datetime import datetime
import json


@sensor(
    name="landing_zone_file_sensor",
    description="Theo dõi landing zone trong MinIO và trigger ingest job khi có file mới",
    default_status=DefaultSensorStatus.RUNNING,
    minimum_interval_seconds=30,  # Check mỗi 30 giây
    required_resource_keys={"minio_resource"},
)
def landing_zone_file_sensor(context: SensorEvaluationContext):
    """
    Sensor kiểm tra landing zone bucket trong MinIO để phát hiện file mới.
    Khi có file mới, sensor sẽ trigger job để ingest file vào bronze layer.
    """
    
    # Lấy MinIO resource
    minio_client = context.resources.minio_resource
    
    landing_bucket = "landing"
    
    # Kiểm tra bucket tồn tại
    if not minio_client.bucket_exists(landing_bucket):
        context.log.warning(f"⚠️ Landing bucket '{landing_bucket}' không tồn tại. Tạo bucket...")
        minio_client.make_bucket(landing_bucket)
        return
    
    # Lấy cursor từ lần chạy trước (lưu timestamp của file cuối cùng đã xử lý)
    cursor_dict = json.loads(context.cursor) if context.cursor else {}
    last_processed_time = cursor_dict.get("last_processed_time", "")
    processed_files = set(cursor_dict.get("processed_files", []))
    
    context.log.info(f"🔍 Đang quét landing zone bucket: {landing_bucket}")
    context.log.info(f"📅 Last processed time: {last_processed_time or 'None'}")
    
    # List tất cả objects trong landing bucket
    objects = minio_client.list_objects(landing_bucket, recursive=True)
    
    new_files = []
    current_files = set()
    latest_time = last_processed_time
    
    for obj in objects:
        file_name = obj.object_name
        file_time = obj.last_modified.isoformat()
        current_files.add(file_name)
        
        # Kiểm tra file mới (chưa được xử lý)
        if file_name not in processed_files:
            new_files.append({
                "file_name": file_name,
                "size": obj.size,
                "last_modified": file_time,
                "etag": obj.etag,
            })
            
            # Cập nhật latest_time
            if file_time > latest_time:
                latest_time = file_time
    
    if not new_files:
        context.log.info("✅ Không có file mới trong landing zone")
        return
    
    context.log.info(f"🆕 Phát hiện {len(new_files)} file mới:")
    for file_info in new_files:
        context.log.info(f"  📄 {file_info['file_name']} ({file_info['size']} bytes)")
    
    # Tạo RunRequest cho mỗi file mới
    run_requests = []
    for file_info in new_files:
        run_config = {
            "ops": {
                "ingest_new_file": {
                    "config": {
                        "file_name": file_info["file_name"],
                        "file_size": file_info["size"],
                        "file_modified": file_info["last_modified"],
                    }
                }
            }
        }
        
        run_requests.append(
            RunRequest(
                run_key=f"ingest_{file_info['file_name']}_{file_info['last_modified']}",
                run_config=run_config,
                tags={
                    "source": "landing_zone_sensor",
                    "file_name": file_info["file_name"],
                    "file_size": str(file_info["size"]),
                },
            )
        )
    
    # Cập nhật cursor với danh sách file đã xử lý
    updated_processed_files = processed_files.union({f["file_name"] for f in new_files})
    new_cursor = json.dumps({
        "last_processed_time": latest_time,
        "processed_files": list(updated_processed_files),
        "last_check": datetime.now().isoformat(),
    })
    
    return SensorResult(
        run_requests=run_requests,
        cursor=new_cursor,
    )


@sensor(
    name="landing_zone_asset_sensor",
    description="Sensor để trigger asset ingest_new_file khi có file mới",
    default_status=DefaultSensorStatus.RUNNING,
    minimum_interval_seconds=30,
    asset_selection=["ingest_new_file"],  # Chỉ định asset cần materialize
    required_resource_keys={"minio_resource"},
)
def landing_zone_asset_sensor(context: SensorEvaluationContext):
    """
    Alternative sensor sử dụng asset materialization approach.
    Sensor này trực tiếp trigger asset thay vì job.
    """
    
    minio_client = context.resources.minio_resource
    landing_bucket = "landing"
    
    if not minio_client.bucket_exists(landing_bucket):
        context.log.warning(f"⚠️ Bucket '{landing_bucket}' chưa tồn tại")
        minio_client.make_bucket(landing_bucket)
        return
    
    # Load cursor
    cursor_dict = json.loads(context.cursor) if context.cursor else {}
    processed_files = set(cursor_dict.get("processed_files", []))
    
    # Scan for new files
    objects = list(minio_client.list_objects(landing_bucket, recursive=True))
    
    new_files = []
    for obj in objects:
        if obj.object_name not in processed_files:
            new_files.append({
                "name": obj.object_name,
                "size": obj.size,
                "modified": obj.last_modified.isoformat(),
            })
    
    if not new_files:
        return
    
    context.log.info(f"🆕 Phát hiện {len(new_files)} file mới - triggering asset materialization")
    
    # Tạo RunRequest để materialize asset
    run_requests = []
    for file_info in new_files:
        run_requests.append(
            RunRequest(
                run_key=f"asset_ingest_{file_info['name']}_{file_info['modified']}",
                tags={
                    "file_name": file_info["name"],
                    "file_size": str(file_info["size"]),
                    "trigger": "landing_zone_sensor",
                },
            )
        )
    
    # Update cursor
    all_processed = processed_files.union({f["name"] for f in new_files})
    new_cursor = json.dumps({
        "processed_files": list(all_processed),
        "last_check": datetime.now().isoformat(),
    })
    
    return SensorResult(
        run_requests=run_requests,
        cursor=new_cursor,
    )
