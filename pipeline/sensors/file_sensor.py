from dagster import (
    sensor,
    RunRequest,
    SensorEvaluationContext,
    DefaultSensorStatus,
    SensorResult,
)
from datetime import datetime
import json


@sensor(
    name="landing_zone_file_sensor",
    description="Theo dõi landing zone trong MinIO và trigger ingest job khi có file mới",
    job_name="ingest_file_from_landing",
    default_status=DefaultSensorStatus.RUNNING,
    minimum_interval_seconds=15,  # Check mỗi 15 giây
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
    
    if not minio_client.bucket_exists(landing_bucket):
        context.log.warning(f"Landing bucket '{landing_bucket}' không tồn tại. Tạo bucket...")
        minio_client.make_bucket(landing_bucket)
        return
    
    # Lấy cursor từ lần chạy trước (lưu timestamp của file cuối cùng đã xử lý)
    cursor_dict = json.loads(context.cursor) if context.cursor else {}
    last_processed_time = cursor_dict.get("last_processed_time", "")
    processed_files = set(cursor_dict.get("processed_files", []))
    
    context.log.info(f"Đang quét landing zone bucket: {landing_bucket}")
    context.log.info(f"Last processed time: {last_processed_time or 'None'}")
    
    # List tất cả objects trong landing bucket
    objects = minio_client.list_objects(landing_bucket, recursive=True)
    
    new_files = []
    current_files = set()
    latest_time = last_processed_time
    
    for obj in objects:
        file_name = obj.object_name
        file_time = obj.last_modified.isoformat()
        current_files.add(file_name)
        
        if file_name not in processed_files:
            new_files.append({
                "file_name": file_name,
                "size": obj.size,
                "last_modified": file_time,
                "etag": obj.etag,
            })
            
            if file_time > latest_time:
                latest_time = file_time
    
    if not new_files:
        context.log.info("Không có file mới trong landing zone")
        return
    
    context.log.info(f"Phát hiện {len(new_files)} file mới:")
    for file_info in new_files:
        context.log.info(f"  📄 {file_info['file_name']} ({file_info['size']} bytes)")
    
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
