# EnsemTrust

## Introduction
EnsemTrust is a comprehensive data pipeline and machine learning project designed to streamline data ingestion, processing, and analysis. The project integrates multiple technologies to ensure efficient data handling and insightful analytics.

## Key Features
- Automated data ingestion and processing pipelines.
- Support for bronze, silver, and gold data layers.
- Machine learning model training and deployment.
- Interactive dashboards using Streamlit.
- Scalable architecture leveraging Docker and Dagster.

## Architecture

### Overview
The architecture of EnsemTrust is modular and scalable, consisting of the following components:

- **Data Layers**: Bronze, Silver, and Gold layers for raw, processed, and refined data.
- **Dagster**: Orchestrates the data pipelines.
- **Streamlit**: Provides an interactive interface for data visualization and insights.
- **Spark**: Handles large-scale data processing.
- **MinIO**: Object storage for data layers.

![Architecture Overview](image/architecture_overview.png)

### Data Lineage
The data lineage is managed and visualized using Dagster, ensuring traceability and transparency in data transformations.

![Dagster Lineage Overview](image/dagster_lineage_overview.svg)

## Key Technologies
- **Dagster**: Pipeline orchestration.
- **Apache Spark**: Distributed data processing.
- **Streamlit**: Interactive dashboards.
- **MinIO**: Object storage.
- **Docker**: Containerization.
- **Python**: Core programming language.

## Prerequisites
- Python 3.8 or higher.
- Docker and Docker Compose installed.
- NVIDIA GPU with CUDA support (for machine learning tasks).
- NVIDIA drivers and CUDA toolkit installed.

## Installation Guide

### Step 1: Clone the Repository
```bash
git clone https://github.com/MinhTuan2405/EnsemTrust.git
cd EnsemTrust
```

### Step 2: Set Up Python Environment
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3: Set Up Docker Containers
```bash
docker-compose up -d
```

### Step 4: Configure GPU (Optional)
Ensure NVIDIA drivers and CUDA toolkit are installed. Use the following command to verify:
```bash
nvidia-smi
```
Install NVIDIA Docker toolkit:
```bash
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

## Running the Project

### Run the Data Pipeline
```bash
dagster dev
```

### Run the Streamlit Dashboard
```bash
cd streamlit
streamlit run app.py
```

## Authors
This project is developed by:
- Nguyễn Hà Minh Tuấn
- Trần Phan Thanh Tùng
- Trần Nguyễn Đức Trung

The team belongs to the University of Information Technology (UIT).

### Supervisor
Dr. Hà Minh Tân, Lecturer, Faculty of Information Science and Engineering.

---

# EnsemTrust

## Giới thiệu
EnsemTrust là một dự án toàn diện về pipeline dữ liệu và machine learning, được thiết kế để tự động hóa quy trình nhập liệu, xử lý và phân tích dữ liệu. Dự án tích hợp nhiều công nghệ để đảm bảo xử lý dữ liệu hiệu quả và cung cấp các phân tích sâu sắc.

## Các tính năng chính
- Pipeline tự động hóa nhập liệu và xử lý dữ liệu.
- Hỗ trợ các lớp dữ liệu Bronze, Silver và Gold.
- Huấn luyện và triển khai mô hình machine learning.
- Dashboard tương tác sử dụng Streamlit.
- Kiến trúc mở rộng sử dụng Docker và Dagster.

## Kiến trúc

### Tổng quan
Kiến trúc của EnsemTrust được thiết kế theo mô hình module và có khả năng mở rộng, bao gồm các thành phần:

- **Lớp dữ liệu**: Bronze, Silver và Gold cho dữ liệu thô, đã xử lý và tinh chỉnh.
- **Dagster**: Điều phối các pipeline dữ liệu.
- **Streamlit**: Giao diện tương tác để trực quan hóa dữ liệu và cung cấp insights.
- **Spark**: Xử lý dữ liệu quy mô lớn.
- **MinIO**: Lưu trữ đối tượng cho các lớp dữ liệu.

![Tổng quan Kiến trúc](image/architecture_overview.png)

### Data Lineage
Data lineage được quản lý và trực quan hóa bằng Dagster, đảm bảo khả năng truy xuất nguồn gốc và minh bạch trong các chuyển đổi dữ liệu.

![Tổng quan Dagster Lineage](image/dagster_lineage_overview.svg)

## Các công nghệ chính
- **Dagster**: Điều phối pipeline.
- **Apache Spark**: Xử lý dữ liệu phân tán.
- **Streamlit**: Dashboard tương tác.
- **MinIO**: Lưu trữ đối tượng.
- **Docker**: Container hóa.
- **Python**: Ngôn ngữ lập trình chính.

## Yêu cầu trước khi cài đặt
- Python 3.8 hoặc cao hơn.
- Cài đặt Docker và Docker Compose.
- GPU NVIDIA hỗ trợ CUDA (cho các tác vụ machine learning).
- Cài đặt driver NVIDIA và bộ công cụ CUDA.

## Hướng dẫn cài đặt

### Bước 1: Clone Repository
```bash
git clone https://github.com/MinhTuan2405/EnsemTrust.git
cd EnsemTrust
```

### Bước 2: Thiết lập môi trường Python
```bash
python -m venv venv
source venv/bin/activate # Trên Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Bước 3: Thiết lập Docker Containers
```bash
docker-compose up -d
```

### Bước 4: Cấu hình GPU (Tùy chọn)
Đảm bảo driver NVIDIA và bộ công cụ CUDA đã được cài đặt. Sử dụng lệnh sau để kiểm tra:
```bash
nvidia-smi
```
Cài đặt NVIDIA Docker toolkit:
```bash
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

## Chạy dự án

### Chạy Data Pipeline
```bash
dagster dev
```

### Chạy Streamlit Dashboard
```bash
cd streamlit
streamlit run app.py
```

## Nhóm phát triển
Dự án được phát triển bởi:
- Nguyễn Hà Minh Tuấn
- Trần Phan Thanh Tùng
- Trần Nguyễn Đức Trung

Nhóm thuộc Trường Đại học Công nghệ Thông tin (UIT).

### Người hướng dẫn
Tiến sĩ Hà Minh Tân, Giảng viên Khoa Khoa học Kỹ thuật Thông tin.