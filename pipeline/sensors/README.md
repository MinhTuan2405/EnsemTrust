# Landing Zone File Sensor

## 📋 Tổng quan

Hệ thống sensor tự động theo dõi **landing zone** trong MinIO và trigger asset `ingest_new_file` khi phát hiện file mới được upload.

## 🎯 Cách hoạt động

### 1. **Landing Zone Asset Sensor** (Recommended)
- **Sensor name**: `landing_zone_asset_sensor`
- **Chức năng**: Theo dõi bucket `landing` và tự động trigger asset materialization
- **Interval**: Check mỗi 30 giây
- **Auto-start**: Bật tự động khi Dagster khởi động

### 2. **Asset: ingest_new_file**
- **Chức năng**: 
  - Đọc file từ `landing` bucket
  - Copy file sang `bronze` bucket với timestamp
  - Xóa file khỏi `landing` sau khi ingest thành công
- **Group**: bronze_layer

## 🚀 Sử dụng

### Cách 1: Tự động (Sensor)

1. **Enable sensor** trong Dagster UI:
   - Truy cập: `http://localhost:3001`
   - Vào tab **Sensors**
   - Tìm `landing_zone_asset_sensor`
   - Click **Start** (mặc định đã được bật)

2. **Upload file vào landing zone**:
   ```bash
   # Sử dụng MinIO Console: http://localhost:9001
   # Hoặc dùng MinIO CLI:
   mc cp your_file.csv minio/landing/
   ```

3. **Sensor tự động phát hiện và trigger**:
   - Sensor check mỗi 30 giây
   - Khi phát hiện file mới → trigger `ingest_new_file`
   - File được move từ `landing` → `bronze`

### Cách 2: Manual (Chạy trực tiếp)

Trong Dagster UI:
1. Vào tab **Assets**
2. Tìm asset `ingest_new_file`
3. Click **Materialize**

## 📊 Monitoring

### Xem sensor logs
```bash
# Trong Dagster UI
Automation > Sensors > landing_zone_asset_sensor > View logs
```

### Xem asset runs
```bash
# Trong Dagster UI
Assets > ingest_new_file > View runs
```

## 📁 File Structure

```
pipeline/
├── assets/
│   └── bronze/
│       └── bronze_layer.py      # Asset ingest_new_file
├── sensors/
│   └── file_sensor.py           # Landing zone sensors
├── jobs/
│   └── ingestion_job.py         # Ingestion jobs
└── __init__.py                  # Definitions với sensors
```

## 🔧 Configuration

### Bucket names
- **Landing zone**: `landing`
- **Bronze layer**: `bronze`

### Sensor settings
- **Minimum interval**: 30 seconds
- **Default status**: RUNNING
- **Cursor tracking**: Lưu trạng thái files đã xử lý

## 📝 Metadata được log

Mỗi lần ingest sẽ log:
- Số lượng files processed
- Tổng dung lượng (bytes)
- Tên file gốc và tên file mới
- Timestamp
- Status

## 🎨 Features

✅ **Auto-detection**: Tự động phát hiện file mới  
✅ **Cursor tracking**: Không xử lý lại file cũ  
✅ **Timestamp naming**: Tránh ghi đè file  
✅ **Auto-cleanup**: Xóa file khỏi landing sau khi ingest  
✅ **Error handling**: Xử lý lỗi gracefully  
✅ **Rich metadata**: Log đầy đủ thông tin  

## 🧪 Testing

### 1. Upload test file
```bash
# Tạo test file
echo "test,data,here" > test_data.csv

# Upload vào landing zone (dùng MinIO console hoặc CLI)
```

### 2. Monitor sensor
- Đợi tối đa 30 giây
- Sensor sẽ phát hiện và trigger
- Check logs trong Dagster UI

### 3. Verify
- File xuất hiện trong bronze bucket
- File biến mất khỏi landing bucket
- Asset run thành công

## 🚨 Troubleshooting

**Sensor không chạy?**
- Check sensor status trong UI (phải là RUNNING)
- Verify MinIO connection
- Check bucket `landing` tồn tại

**File không được ingest?**
- Check sensor logs
- Verify file permissions
- Check MinIO credentials

**File bị duplicate?**
- Sensor có cursor tracking để tránh xử lý lại
- Nếu clear cursor, file sẽ được xử lý lại
