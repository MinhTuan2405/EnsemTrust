# EnsemTrust: End-to-End Fake News Detection Platform

<div align="center">

![Architecture Overview](./image/architecture_overview.png)

**An enterprise-grade data engineering and machine learning platform for automated fake news detection**

[🇻🇳 Tiếng Việt](#tiếng-việt) | [🇬🇧 English](#english)

</div>

---

## English 

### Table of Contents
- [Dataset](#dataset)
- [Introduction](#introduction)
- [Key Features](#key-features)
- [Architecture](#architecture)
  - [Architecture Overview](#architecture-overview)
  - [Data Lineage](#data-lineage)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation Guide](#installation-guide)
  - [GPU Setup for Machine Learning](#gpu-setup-for-machine-learning)
- [Running the Project](#running-the-project)
- [Project Structure](#project-structure)
- [Development Team](#development-team)

---

### Dataset

This project uses the **Fake News Detection Dataset** from Kaggle:

**Dataset Source:** [Fake News Detection Datasets on Kaggle](https://www.kaggle.com/datasets/emineyetm/fake-news-detection-datasets/data)

The dataset contains news articles labeled as fake or real, which are used to train and evaluate the ensemble machine learning models in this platform.

---

### Introduction

**EnsemTrust** is a comprehensive fake news detection platform built using modern data engineering practices and machine learning techniques. The project implements a complete data pipeline from ingestion to visualization, leveraging distributed computing, lakehouse architecture, and ensemble learning models to accurately classify news articles as genuine or fake.

This platform demonstrates the integration of cutting-edge technologies including Apache Spark, Delta Lake, Dagster orchestration, and GPU-accelerated machine learning, all containerized using Docker for seamless deployment.

---

### Key Features

**Data Engineering Pipeline:**
- **Multi-layer Data Architecture**: Bronze (raw), Silver (cleaned), Gold (curated) layers following medallion architecture
- **Automated Data Orchestration**: Dagster-based workflow management with dependency tracking and lineage visualization
- **Distributed Processing**: Apache Spark for large-scale data transformation and feature engineering
- **Lakehouse Architecture**: Delta Lake for ACID transactions and time travel capabilities
- **Object Storage**: MinIO S3-compatible storage for scalable data management

**Machine Learning Pipeline:**
- **Ensemble Learning**: Combination of SVM, Logistic Regression, and LightGBM models
- **Advanced Feature Engineering**: TF-IDF, sentence transformers (BERT embeddings), and handcrafted text features
- **GPU Acceleration**: CUDA-enabled training for faster model development
- **Model Versioning**: Automatic model artifact storage in MinIO
- **Real-time Inference**: Streamlit-based interactive web application

**Data Visualization & Analytics:**
- **Interactive Dashboards**: Metabase integration for business intelligence
- **Query Engine**: Trino for fast SQL analytics on lakehouse data
- **Data Catalog**: CloudBeaver for database management and exploration
- **Pipeline Monitoring**: Dagster UI for real-time pipeline observability

---

### Architecture

#### Architecture Overview

![Architecture Overview](./image/architecture_overview.png)

The platform follows a modern lakehouse architecture with the following components:

**Data Ingestion Layer:**
- Files uploaded to MinIO landing zone
- Automated detection via Dagster file sensors
- Raw data ingestion to Bronze layer

**Data Processing Layer:**
- **Bronze Layer**: Raw data storage with minimal transformations
  
  ![Bronze Layer](./image/bronze_layer.svg)

- **Silver Layer**: Data cleaning, deduplication, and schema enforcement using Apache Spark
  
  ![Silver Layer](./image/silver_layer.svg)

- **Gold Layer**: Curated datasets stored as Delta tables for analytics
  
  ![Gold Layer](./image/gold_layer.svg)

**Machine Learning Layer:**
- Feature engineering with handcrafted and deep learning features
- Multi-model training (SVM, Logistic Regression, LightGBM)
- Stacking ensemble for improved accuracy
- Model evaluation and storage

![Machine Learning Layer](./image/machine_learning_layer.svg)

**Serving Layer:**
- Trino query engine for SQL-based analytics
- Metabase for BI dashboards
- Streamlit for real-time predictions
- CloudBeaver for data exploration

#### Data Lineage

![Dagster Lineage](./image/dagster_lineage_overview.svg)

The data lineage graph shows complete traceability from raw data ingestion through transformation to machine learning model deployment, ensuring data quality and reproducibility.

---

### Technology Stack

**Orchestration & Workflow:**
- **Dagster**: Modern data orchestrator for pipeline management
- **Docker & Docker Compose**: Containerization and multi-service orchestration

**Data Storage & Processing:**
- **MinIO**: S3-compatible object storage
- **PostgreSQL**: Metadata storage and Hive Metastore backend
- **Apache Spark 3.5.7**: Distributed data processing
- **Delta Lake**: ACID-compliant data lakehouse storage format
- **Apache Hive Metastore**: Centralized metadata repository

**Query & Analytics:**
- **Trino**: Distributed SQL query engine
- **Metabase**: Business intelligence and visualization
- **CloudBeaver**: Universal database management tool

**Machine Learning:**
- **Python 3.10**: Core programming language
- **PyTorch**: Deep learning framework with CUDA support
- **Transformers**: Hugging Face library for NLP models
- **Sentence-Transformers**: Pre-trained sentence embeddings
- **Scikit-learn**: Classical machine learning algorithms
- **LightGBM**: Gradient boosting framework

**Web Application:**
- **Streamlit**: Interactive web application framework

**Infrastructure:**
- **NVIDIA CUDA 11.8**: GPU acceleration for ML training
- **Poetry**: Python dependency management

---

### Prerequisites

Before installing the project, ensure you have the following:

**Required Software:**
- **Docker Desktop** (with WSL 2 backend on Windows)
- **Docker Compose** v2.0+
- **Git** for version control
- Minimum **16GB RAM** (32GB recommended)
- **50GB free disk space**

**For GPU Support (Optional but Recommended):**
- NVIDIA GPU with CUDA Compute Capability 3.5+
- NVIDIA Docker runtime installed
- Latest NVIDIA drivers

**System Requirements:**
- Windows 10/11, macOS 11+, or Linux (Ubuntu 20.04+)
- Multi-core processor (4+ cores recommended)

---

### Installation Guide

#### Step 1: Clone the Repository

```bash
git clone https://github.com/MinhTuan2405/EnsemTrust.git
cd EnsemTrust
```

#### Step 2: Download Required JAR Files

The project requires specific JAR files for Hadoop AWS integration and PostgreSQL connectivity. Run the appropriate script:

**On Linux/macOS:**
```bash
chmod +x Script/jardownloader.sh
./Script/jardownloader.sh
```

**On Windows (PowerShell):**
```powershell
.\Script\jardownloader.ps1
```

This will download:
- `hadoop-aws-3.3.6.jar`
- `aws-java-sdk-bundle-1.12.262.jar`
- `postgresql-42.7.8.jar`

#### Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your configurations:

```env
# PostgreSQL Configuration
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
POSTGRES_DB=ensemtrust
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# MinIO Configuration
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=admin123
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001

# Dagster Configuration
DAGSTER_PORT=3000
DAGSTER_HOME=/opt/dagster/dagster_home/dagster-project

# Trino Configuration
TRINO_PORT=8090

# Metabase Configuration
METABASE_DB=metabase

# Feature Engineering
TFIDF_MAX_FEATURES=5000
SVD_COMPONENTS=300
RANDOM_STATE=42

# AWS/S3 Configuration (for MinIO)
AWS_ACCESS_KEY_ID=admin
AWS_SECRET_ACCESS_KEY=admin123
AWS_DEFAULT_REGION=us-east-1
AWS_S3_ENDPOINT=http://minio:9000
```

#### Step 4: GPU Setup for Machine Learning

**On Linux:**

1. Install NVIDIA Docker runtime:
```bash
# Add NVIDIA Docker repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install nvidia-docker2
sudo apt-get update
sudo apt-get install -y nvidia-docker2

# Restart Docker
sudo systemctl restart docker
```

2. Verify GPU access:
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

**On Windows with WSL 2:**

1. Install NVIDIA drivers for Windows (support WSL 2)
2. Enable WSL 2 and install Ubuntu distribution
3. Inside WSL 2:
```bash
# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
```

4. Update Docker Desktop settings:
   - Open Docker Desktop → Settings → Resources → WSL Integration
   - Enable integration with your WSL distribution

**Verify GPU Setup:**
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

You should see your GPU information displayed.

#### Step 5: Build and Start Services

```bash
# Build all Docker images
docker-compose build

# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

Wait for all services to be healthy (this may take 5-10 minutes on first run).

#### Step 6: Initialize Data Buckets

The MinIO buckets (landing, bronze, silver, gold, models) are automatically created by the `mc` service. Verify by accessing MinIO console at `http://localhost:9001` with credentials from `.env`.

---

### Running the Project

#### 1. Access Dagster UI

Open `http://localhost:3000` to access the Dagster orchestration interface.

**Run the Complete Pipeline:**

1. Navigate to "Assets" tab
2. Click "Materialize all" to run the entire pipeline, or
3. Select specific assets to run individual components

**Pipeline Execution Order:**
1. **Bronze Layer**: `ingest_new_file` - Upload CSV files to MinIO landing zone first
2. **Silver Layer**: `load_fake_dataset` → `load_true_dataset` → `transform_news_dataset`
3. **Gold Layer**: `gold_news_dataset`
4. **ML Pipeline**: 
   - `load_data_for_ml` → `feature_engineering` → `combine_features`
   - `train_svm` / `train_logistic_regression` / `train_lightgbm`
   - `train_stacking_ensemble`

#### 2. Upload Dataset

Place your CSV files (fake news and real news datasets) in MinIO landing zone:

**Via MinIO Console** (`http://localhost:9001`):
- Login with credentials from `.env`
- Navigate to `landing` bucket
- Upload CSV files

**Via MinIO CLI**:
```bash
docker exec -it mc sh
mc alias set local http://minio:9000 admin admin123
mc cp /path/to/your/dataset.csv local/landing/
```

#### 3. Monitor Pipeline Execution

**Dagster UI** (`http://localhost:3000`):
- View real-time logs
- Check asset materialization status
- Visualize data lineage

**Spark UI** (`http://localhost:8082`):
- Monitor Spark jobs
- View worker nodes and resource usage

#### 4. Query Data with Trino

Access CloudBeaver at `http://localhost:8978`:
1. Create Trino connection:
   - Host: `trino`
   - Port: `8080`
   - Catalog: `delta` or `hive`

2. Query example:
```sql
SELECT label, COUNT(*) as count
FROM delta.default.news_dataset
GROUP BY label;
```

#### 5. Visualize with Metabase

Access Metabase at `http://localhost:3007`:
1. Complete initial setup
2. Add Trino as data source
3. Create dashboards and visualizations

#### 6. Test Predictions with Streamlit

Access the web application at `http://localhost:8501`:
1. Enter news article text
2. Click "Phân tích" (Analyze)
3. View prediction results with confidence scores

**Example Input:**
```
President announces new policy to reduce inflation by 50% next month
```

---

### Project Structure

```
ensemtrust/
├── pipeline/                      # Dagster pipeline code
│   ├── assets/                    # Asset definitions
│   │   ├── bronze/                # Bronze layer ingestion
│   │   ├── silver/                # Silver layer transformation
│   │   ├── gold/                  # Gold layer Delta tables
│   │   └── machine_learning/      # ML training pipeline
│   ├── jobs/                      # Dagster jobs
│   ├── resources/                 # Resource definitions (MinIO, etc.)
│   ├── sensors/                   # File sensors
│   └── utils/                     # Utility functions
│       ├── feature_engineer.py    # Feature engineering logic
│       ├── models.py              # ML model definitions
│       └── spark.py               # Spark session management
├── streamlit/                     # Web application
│   └── app.py                     # Streamlit UI
├── config/                        # Configuration files
│   ├── hive/                      # Hive Metastore config
│   └── trino/                     # Trino catalog config
├── data/                          # Persistent data volumes
│   ├── minio/                     # Object storage
│   ├── postgres/                  # Database storage
│   └── dagster/                   # Dagster storage
├── image/                         # Architecture diagrams
├── init-scripts/                  # Initialization scripts
├── jars/                          # Java dependencies
├── notebooks/                     # Jupyter notebooks for EDA
├── Script/                        # Utility scripts
├── docker-compose.yml             # Service orchestration
├── Dockerfile.dagster             # Dagster container
├── Dockerfile.spark               # Spark container
├── Dockerfile.streamlit           # Streamlit container
├── pyproject.toml                 # Python dependencies
├── workspace.yaml                 # Dagster workspace config
└── README.md                      # This file
```

---

### Development Team

**Project Team:**
- **Nguyễn Hà Minh Tuấn** - Data Engineer & ML Engineer
- **Trần Phan Thanh Tùng** - Data Engineer
- **Trần Nguyễn Đức Trung** - Data Engineer

**Institution:**  
University of Information Technology (UIT) - Vietnam National University Ho Chi Minh City

**Supervisor:**  
**Dr. Hà Minh Tân**  
Lecturer, Faculty of Information Science and Engineering  
University of Information Technology (UIT)

**Contact:**
- GitHub: [MinhTuan2405](https://github.com/MinhTuan2405)
- Email: tuannguyen.02042005@gmail.com

---

### License

This project is developed for educational purposes 

---

### Acknowledgments

Special thanks to Dr. Hà Minh Tân for guidance and mentorship throughout the development of this project.

---

<div align="center">

**Built with ❤️ by UIT Students**

</div>

---
---
---

## Tiếng Việt

### Mục lục
- [Bộ dữ liệu](#bộ-dữ-liệu)
- [Giới thiệu](#giới-thiệu)
- [Các tính năng chính](#các-tính-năng-chính)
- [Kiến trúc](#kiến-trúc)
  - [Kiến trúc tổng quan](#kiến-trúc-tổng-quan)
  - [Data Lineage](#data-lineage-vi)
- [Các công nghệ chính sử dụng](#các-công-nghệ-chính-sử-dụng)
- [Yêu cầu trước khi cài đặt](#yêu-cầu-trước-khi-cài-đặt)
- [Hướng dẫn cài đặt dự án](#hướng-dẫn-cài-đặt-dự-án)
  - [Setup GPU cho Machine Learning](#setup-gpu-cho-machine-learning)
- [Cách chạy dự án](#cách-chạy-dự-án)
- [Cấu trúc dự án](#cấu-trúc-dự-án)
- [Nhóm phát triển](#nhóm-phát-triển)

---

### Bộ dữ liệu

Dự án này sử dụng **Bộ dữ liệu phát hiện tin giả (Fake News Detection Dataset)** từ Kaggle:

**Nguồn dữ liệu:** [Fake News Detection Datasets trên Kaggle](https://www.kaggle.com/datasets/emineyetm/fake-news-detection-datasets/data)

Bộ dữ liệu chứa các bài báo được gắn nhãn là tin giả hoặc tin thật, được sử dụng để huấn luyện và đánh giá các mô hình machine learning ensemble trong nền tảng này.

---

### Giới thiệu

**EnsemTrust** là một nền tảng phát hiện tin giả toàn diện được xây dựng dựa trên các phương pháp data engineering hiện đại và kỹ thuật machine learning. Dự án triển khai một pipeline dữ liệu hoàn chỉnh từ khâu thu thập đến trực quan hóa, tận dụng điện toán phân tán, kiến trúc lakehouse, và các mô hình ensemble learning để phân loại chính xác các bài báo là thật hay giả.

Nền tảng này thể hiện sự tích hợp các công nghệ tiên tiến bao gồm Apache Spark, Delta Lake, Dagster orchestration, và machine learning tăng tốc GPU, tất cả được đóng gói bằng Docker để triển khai dễ dàng.

---

### Các tính năng chính

**Pipeline Data Engineering:**
- **Kiến trúc dữ liệu đa tầng**: Các lớp Bronze (thô), Silver (đã làm sạch), Gold (được tổ chức) theo kiến trúc medallion
- **Tự động hóa luồng dữ liệu**: Quản lý workflow dựa trên Dagster với theo dõi phụ thuộc và trực quan hóa lineage
- **Xử lý phân tán**: Apache Spark cho chuyển đổi dữ liệu quy mô lớn và feature engineering
- **Kiến trúc Lakehouse**: Delta Lake cho ACID transactions và khả năng time travel
- **Object Storage**: MinIO tương thích S3 cho quản lý dữ liệu có khả năng mở rộng

**Pipeline Machine Learning:**
- **Ensemble Learning**: Kết hợp các mô hình SVM, Logistic Regression, và LightGBM
- **Feature Engineering nâng cao**: TF-IDF, sentence transformers (BERT embeddings), và các đặc trưng văn bản thủ công
- **Tăng tốc GPU**: Huấn luyện hỗ trợ CUDA cho phát triển mô hình nhanh hơn
- **Quản lý phiên bản mô hình**: Lưu trữ tự động các artifact mô hình trong MinIO
- **Dự đoán thời gian thực**: Ứng dụng web tương tác dựa trên Streamlit

**Trực quan hóa dữ liệu & Phân tích:**
- **Dashboard tương tác**: Tích hợp Metabase cho business intelligence
- **Query Engine**: Trino cho phân tích SQL nhanh trên dữ liệu lakehouse
- **Data Catalog**: CloudBeaver cho quản lý và khám phá cơ sở dữ liệu
- **Giám sát Pipeline**: Dagster UI cho khả năng quan sát pipeline thời gian thực

---

### Kiến trúc

#### Kiến trúc tổng quan

![Architecture Overview](./image/architecture_overview.png)

Nền tảng tuân theo kiến trúc lakehouse hiện đại với các thành phần sau:

**Lớp thu thập dữ liệu (Data Ingestion Layer):**
- Files được tải lên landing zone của MinIO
- Phát hiện tự động thông qua Dagster file sensors
- Thu thập dữ liệu thô vào lớp Bronze

**Lớp xử lý dữ liệu (Data Processing Layer):**
- **Lớp Bronze**: Lưu trữ dữ liệu thô với chuyển đổi tối thiểu
  
  ![Bronze Layer](./image/bronze_layer.svg)

- **Lớp Silver**: Làm sạch dữ liệu, loại bỏ trùng lặp, và áp dụng schema sử dụng Apache Spark
  
  ![Silver Layer](./image/silver_layer.svg)

- **Lớp Gold**: Datasets được tổ chức lưu trữ dưới dạng Delta tables cho phân tích
  
  ![Gold Layer](./image/gold_layer.svg)

**Lớp Machine Learning:**
- Feature engineering với các đặc trưng thủ công và deep learning
- Huấn luyện nhiều mô hình (SVM, Logistic Regression, LightGBM)
- Stacking ensemble để cải thiện độ chính xác
- Đánh giá và lưu trữ mô hình

![Machine Learning Layer](./image/machine_learning_layer.svg)

**Lớp phục vụ (Serving Layer):**
- Trino query engine cho phân tích dựa trên SQL
- Metabase cho BI dashboards
- Streamlit cho dự đoán thời gian thực
- CloudBeaver cho khám phá dữ liệu

#### Data Lineage (VI)

![Dagster Lineage](./image/dagster_lineage_overview.svg)

Biểu đồ data lineage hiển thị khả năng truy vết hoàn toàn từ thu thập dữ liệu thô qua chuyển đổi đến triển khai mô hình machine learning, đảm bảo chất lượng dữ liệu và khả năng tái tạo.

---

### Các công nghệ chính sử dụng

**Orchestration & Workflow:**
- **Dagster**: Orchestrator dữ liệu hiện đại cho quản lý pipeline
- **Docker & Docker Compose**: Đóng gói container và orchestration nhiều service

**Lưu trữ & Xử lý dữ liệu:**
- **MinIO**: Object storage tương thích S3
- **PostgreSQL**: Lưu trữ metadata và backend cho Hive Metastore
- **Apache Spark 3.5.7**: Xử lý dữ liệu phân tán
- **Delta Lake**: Định dạng lưu trữ data lakehouse tuân thủ ACID
- **Apache Hive Metastore**: Kho metadata tập trung

**Query & Analytics:**
- **Trino**: Distributed SQL query engine
- **Metabase**: Business intelligence và trực quan hóa
- **CloudBeaver**: Công cụ quản lý database đa năng

**Machine Learning:**
- **Python 3.10**: Ngôn ngữ lập trình chính
- **PyTorch**: Framework deep learning với hỗ trợ CUDA
- **Transformers**: Thư viện Hugging Face cho các mô hình NLP
- **Sentence-Transformers**: Pre-trained sentence embeddings
- **Scikit-learn**: Thuật toán machine learning cổ điển
- **LightGBM**: Framework gradient boosting

**Ứng dụng Web:**
- **Streamlit**: Framework ứng dụng web tương tác

**Hạ tầng:**
- **NVIDIA CUDA 11.8**: Tăng tốc GPU cho huấn luyện ML
- **Poetry**: Quản lý dependencies Python

---

### Yêu cầu trước khi cài đặt

Trước khi cài đặt dự án, đảm bảo bạn có:

**Phần mềm bắt buộc:**
- **Docker Desktop** (với WSL 2 backend trên Windows)
- **Docker Compose** v2.0+
- **Git** cho version control
- Tối thiểu **16GB RAM** (khuyến nghị 32GB)
- **50GB dung lượng ổ đĩa trống**

**Để hỗ trợ GPU (Tùy chọn nhưng được khuyến nghị):**
- NVIDIA GPU với CUDA Compute Capability 3.5+
- NVIDIA Docker runtime đã cài đặt
- Driver NVIDIA mới nhất

**Yêu cầu hệ thống:**
- Windows 10/11, macOS 11+, hoặc Linux (Ubuntu 20.04+)
- Bộ xử lý đa lõi (khuyến nghị 4+ lõi)

---

### Hướng dẫn cài đặt dự án

#### Bước 1: Clone Repository

```bash
git clone https://github.com/MinhTuan2405/EnsemTrust.git
cd EnsemTrust
```

#### Bước 2: Tải các file JAR cần thiết

Dự án yêu cầu các file JAR cụ thể cho tích hợp Hadoop AWS và kết nối PostgreSQL. Chạy script phù hợp:

**Trên Linux/macOS:**
```bash
chmod +x Script/jardownloader.sh
./Script/jardownloader.sh
```

**Trên Windows (PowerShell):**
```powershell
.\Script\jardownloader.ps1
```

Script sẽ tải xuống:
- `hadoop-aws-3.3.6.jar`
- `aws-java-sdk-bundle-1.12.262.jar`
- `postgresql-42.7.8.jar`

#### Bước 3: Cấu hình biến môi trường

Tạo file `.env` trong thư mục gốc của dự án:

```bash
cp .env.example .env
```

Chỉnh sửa `.env` với cấu hình của bạn:

```env
# PostgreSQL Configuration
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
POSTGRES_DB=ensemtrust
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# MinIO Configuration
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=admin123
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001

# Dagster Configuration
DAGSTER_PORT=3000
DAGSTER_HOME=/opt/dagster/dagster_home/dagster-project

# Trino Configuration
TRINO_PORT=8090

# Metabase Configuration
METABASE_DB=metabase

# Feature Engineering
TFIDF_MAX_FEATURES=5000
SVD_COMPONENTS=300
RANDOM_STATE=42

# AWS/S3 Configuration (for MinIO)
AWS_ACCESS_KEY_ID=admin
AWS_SECRET_ACCESS_KEY=admin123
AWS_DEFAULT_REGION=us-east-1
AWS_S3_ENDPOINT=http://minio:9000
```

#### Bước 4: Setup GPU cho Machine Learning

**Trên Linux:**

1. Cài đặt NVIDIA Docker runtime:
```bash
# Thêm repository NVIDIA Docker
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Cài đặt nvidia-docker2
sudo apt-get update
sudo apt-get install -y nvidia-docker2

# Khởi động lại Docker
sudo systemctl restart docker
```

2. Xác minh quyền truy cập GPU:
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

**Trên Windows với WSL 2:**

1. Cài đặt driver NVIDIA cho Windows (hỗ trợ WSL 2)
2. Bật WSL 2 và cài đặt bản phân phối Ubuntu
3. Trong WSL 2:
```bash
# Cài đặt NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
```

4. Cập nhật cài đặt Docker Desktop:
   - Mở Docker Desktop → Settings → Resources → WSL Integration
   - Bật tích hợp với bản phân phối WSL của bạn

**Kiểm tra Setup GPU:**
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

Bạn sẽ thấy thông tin GPU của mình được hiển thị.

#### Bước 5: Build và khởi động các services

```bash
# Build tất cả Docker images
docker-compose build

# Khởi động tất cả services
docker-compose up -d

# Kiểm tra trạng thái services
docker-compose ps
```

Chờ tất cả các services ở trạng thái healthy (có thể mất 5-10 phút lần chạy đầu tiên).

#### Bước 6: Khởi tạo Data Buckets

Các buckets MinIO (landing, bronze, silver, gold, models) được tự động tạo bởi service `mc`. Xác minh bằng cách truy cập MinIO console tại `http://localhost:9001` với thông tin đăng nhập từ `.env`.

---

### Cách chạy dự án

#### 1. Truy cập Dagster UI

Mở `http://localhost:3000` để truy cập giao diện orchestration Dagster.

**Chạy Pipeline hoàn chỉnh:**

1. Điều hướng đến tab "Assets"
2. Click "Materialize all" để chạy toàn bộ pipeline, hoặc
3. Chọn các assets cụ thể để chạy từng thành phần riêng lẻ

**Thứ tự thực thi Pipeline:**
1. **Lớp Bronze**: `ingest_new_file` - Tải files CSV lên landing zone của MinIO trước
2. **Lớp Silver**: `load_fake_dataset` → `load_true_dataset` → `transform_news_dataset`
3. **Lớp Gold**: `gold_news_dataset`
4. **ML Pipeline**: 
   - `load_data_for_ml` → `feature_engineering` → `combine_features`
   - `train_svm` / `train_logistic_regression` / `train_lightgbm`
   - `train_stacking_ensemble`

#### 2. Tải Dataset lên

Đặt các file CSV của bạn (datasets tin giả và tin thật) vào landing zone của MinIO:

**Qua MinIO Console** (`http://localhost:9001`):
- Đăng nhập với thông tin từ `.env`
- Điều hướng đến bucket `landing`
- Tải lên các file CSV

**Qua MinIO CLI**:
```bash
docker exec -it mc sh
mc alias set local http://minio:9000 admin admin123
mc cp /path/to/your/dataset.csv local/landing/
```

#### 3. Giám sát thực thi Pipeline

**Dagster UI** (`http://localhost:3000`):
- Xem logs thời gian thực
- Kiểm tra trạng thái materialization của assets
- Trực quan hóa data lineage

**Spark UI** (`http://localhost:8082`):
- Giám sát Spark jobs
- Xem các worker nodes và mức sử dụng tài nguyên

#### 4. Query dữ liệu với Trino

Truy cập CloudBeaver tại `http://localhost:8978`:
1. Tạo kết nối Trino:
   - Host: `trino`
   - Port: `8080`
   - Catalog: `delta` hoặc `hive`

2. Ví dụ query:
```sql
SELECT label, COUNT(*) as count
FROM delta.default.news_dataset
GROUP BY label;
```

#### 5. Trực quan hóa với Metabase

Truy cập Metabase tại `http://localhost:3007`:
1. Hoàn thành thiết lập ban đầu
2. Thêm Trino làm nguồn dữ liệu
3. Tạo dashboards và visualizations

#### 6. Kiểm tra dự đoán với Streamlit

Truy cập ứng dụng web tại `http://localhost:8501`:
1. Nhập văn bản bài báo
2. Click "Phân tích"
3. Xem kết quả dự đoán với điểm confidence

**Ví dụ Input:**
```
Tổng thống công bố chính sách mới giảm lạm phát 50% trong tháng tới
```

---

### Cấu trúc dự án

```
ensemtrust/
├── pipeline/                      # Mã Dagster pipeline
│   ├── assets/                    # Định nghĩa assets
│   │   ├── bronze/                # Thu thập lớp Bronze
│   │   ├── silver/                # Chuyển đổi lớp Silver
│   │   ├── gold/                  # Delta tables lớp Gold
│   │   └── machine_learning/      # Pipeline huấn luyện ML
│   ├── jobs/                      # Dagster jobs
│   ├── resources/                 # Định nghĩa resources (MinIO, etc.)
│   ├── sensors/                   # File sensors
│   └── utils/                     # Hàm tiện ích
│       ├── feature_engineer.py    # Logic feature engineering
│       ├── models.py              # Định nghĩa mô hình ML
│       └── spark.py               # Quản lý Spark session
├── streamlit/                     # Ứng dụng web
│   └── app.py                     # Streamlit UI
├── config/                        # Files cấu hình
│   ├── hive/                      # Cấu hình Hive Metastore
│   └── trino/                     # Cấu hình catalog Trino
├── data/                          # Persistent data volumes
│   ├── minio/                     # Object storage
│   ├── postgres/                  # Database storage
│   └── dagster/                   # Dagster storage
├── image/                         # Sơ đồ kiến trúc
├── init-scripts/                  # Scripts khởi tạo
├── jars/                          # Dependencies Java
├── notebooks/                     # Jupyter notebooks cho EDA
├── Script/                        # Utility scripts
├── docker-compose.yml             # Orchestration services
├── Dockerfile.dagster             # Container Dagster
├── Dockerfile.spark               # Container Spark
├── Dockerfile.streamlit           # Container Streamlit
├── pyproject.toml                 # Dependencies Python
├── workspace.yaml                 # Cấu hình Dagster workspace
└── README.md                      # File này
```

---

### Nhóm phát triển

**Nhóm dự án:**
- **Nguyễn Hà Minh Tuấn** - Data Engineer & ML Engineer
- **Trần Phan Thanh Tùng** - Data Engineer
- **Trần Nguyễn Đức Trung** - Data Engineer

**Đơn vị:**  
Trường Đại học Công nghệ Thông tin (UIT) - Đại học Quốc gia Thành phố Hồ Chí Minh

**Giảng viên hướng dẫn:**  
**Tiến sĩ Hà Minh Tân**  
Giảng viên, Khoa Khoa học và Kỹ thuật Thông tin  
Trường Đại học Công nghệ Thông tin (UIT)

**Liên hệ:**
- GitHub: [MinhTuan2405](https://github.com/MinhTuan2405)
- Email: tuannguyen.02042005@gmail.com

---

### Giấy phép

Dự án này được phát triển cho mục đích giáo dục 

---

### Lời cảm ơn

Xin chân thành cảm ơn Tiến sĩ Hà Minh Tân đã hướng dẫn và hỗ trợ trong suốt quá trình phát triển dự án này.

---

<div align="center">

**Được xây dựng với ❤️ bởi sinh viên UIT**

</div>
