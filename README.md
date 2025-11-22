# EnsemTrust

## 1. Introduction
EnsemTrust is an end-to-end fake news detection platform combining modern data engineering, lakehouse querying, scalable feature engineering, and ensemble machine learning. The system ingests raw textual news data, processes and enriches it into structured multi-layer datasets (bronze → silver → gold), and trains several base classifiers plus a stacking ensemble. A Streamlit application exposes real-time inference with calibrated confidence scoring. The architecture emphasizes reproducible lineage, modular assets, GPU-accelerated training (LightGBM, embeddings), and transparent model evaluation.

## 2. Key Features
- Multi-layer data lake design (landing, bronze, silver, gold) on MinIO object storage.
- Orchestrated pipelines using Dagster assets with clear lineage and metadata.
- Spark-based scalable preprocessing and feature splitting.
- Rich feature engineering: handcrafted linguistic metrics, TF-IDF + SVD dimensionality reduction, SentenceTransformer embeddings (all-MiniLM-L6-v2).
- Multiple ML models: Logistic Regression, Linear SVM (Calibrated), LightGBM (GPU optional), Stacking Ensemble meta-classifier.
- GPU-aware training with graceful CPU fallback for LightGBM.
- Centralized artifact management (models, transformers, plots) stored in MinIO bucket `models`.
- Automated evaluation (Accuracy, ROC AUC, classification report) across train/validation/test splits.
- Visualization assets: confusion matrices, ROC curves, comparative accuracy/AUC panels, inference distributions.
- Real-time inference UI built with Streamlit (probability of class 1 = Real News confidence).
- Query and exploration stack (Trino + Hive Metastore + CloudBeaver + Metabase) for analytical/BI workflows.
- Modular, reproducible, containerized deployment (Docker + docker-compose) with optional NVIDIA GPU acceleration.

## 3. Architecture
### 3.1 Overview
![Architecture Overview](image/architecture_overview.png)

Components:
- Dagster orchestrates asset-based pipelines (data preparation, feature engineering, model training, inference validation).
- MinIO provides layered lake storage (landing, bronze, silver, gold) and model artifacts.
- Postgres stores Dagster metadata and Hive/Metabase schemas.
- Hive Metastore + Trino expose SQL access over object storage.
- Spark executes distributed transformations and dataset splits.
- ML layer performs feature engineering, training, evaluation.
- Streamlit serves interactive inference.
- Metabase / CloudBeaver enable BI exploration.

### 3.2 Data Lineage
![Dagster Lineage Overview](image/dagster_lineage_overview.svg)
![Bronze Layer](image/bronze_layer.svg) ![Silver Layer](image/silver_layer.svg) ![Gold Layer](image/gold_layer.svg)

Flow:
1. Landing → Bronze: raw records versioned.
2. Bronze → Silver: cleaning, deduplication, unified `content` field.
3. Silver → Feature: stratified split (60/20/20) + multi-feature extraction (handcrafted, TF-IDF+SVD, embeddings).
4. Combination: concatenate embeddings + reduced TF-IDF + handcrafted.
5. Training: base models (LogReg, Linear SVM calibrated, LightGBM) + stacking ensemble.
6. Inference: test cases & comparative plots.
7. Serving: stacking ensemble persisted as `stacking_ensemble.pkl` for Streamlit.

### 3.3 Machine Learning Layer
![Machine Learning Layer](image/machine_learning_layer.svg)
- Calibration: LinearSVC + `CalibratedClassifierCV` for probabilities.
- Validation: LightGBM uses `eval_set` (GPU with CPU fallback).
- Artifacts:
  - Models: `models/model/*.pkl`
  - Transformers: `models/transformers/tfidf_vectorizer.pkl`, `models/transformers/svd_transformer.pkl`
  - Plots: `models/plots/*performance.png`, `models/plots/inference_*.png`

## 4. Core Technologies
Category | Stack
---------|------
Orchestration | Dagster
Storage & Lake | MinIO (object store), versioned buckets
Metadata / Relational | Postgres
Query Engine | Trino + Hive Metastore
Distributed Processing | Apache Spark (Master + Workers)
ML / NLP | scikit-learn, LightGBM, SentenceTransformers, PyTorch
Feature Extraction | TF-IDF, SVD, handcrafted metrics, MiniLM embeddings
Visualization | Matplotlib, Seaborn, Streamlit UI, Metabase dashboards
BI & Exploration | CloudBeaver, Metabase
Infrastructure | Docker, docker-compose, optional NVIDIA GPU runtime
```bash
<!-- Roadmap and License sections intentionally removed per project owner request -->
# Install container toolkit
### 3.1 Tổng Quan
![Tổng quan kiến trúc](image/architecture_overview.png)
sudo apt-get install -y nvidia-driver-535
### 3.2 Data Lineage
![Tổng quan lineage Dagster](image/dagster_lineage_overview.svg)
![Lớp Bronze](image/bronze_layer.svg) ![Lớp Silver](image/silver_layer.svg) ![Lớp Gold](image/gold_layer.svg)
curl -fsSL https://nvidia.github.io/libnvidia-container/ubuntu/$(. /etc/os-release; echo $VERSION_ID)/libnvidia-container.list | \
### 3.3 Lớp Học Máy
![Lớp học máy](image/machine_learning_layer.svg)
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
5. Ensemble: `train_stacking_ensemble` (lưu `stacking_ensemble.pkl`).
sudo apt-get install -y nvidia-container-toolkit
- Tải `stacking_ensemble.pkl`.
sudo systemctl restart docker
Nhóm phát triển:
- **Nguyễn Hà Minh Tuấn**
- **Trần Phan Thanh Tùng**
- **Trần Nguyễn Đức Trung**

Thuộc **Trường Đại học Công nghệ Thông tin (UIT)** – **Khoa Khoa học Kĩ thuật Thông tin**.

Người hướng dẫn:
- **Tiến sĩ Hà Minh Tân** (Giảng viên Khoa Khoa học Kĩ thuật Thông tin)
1. Enable WSL2 and install Ubuntu distribution.
<!-- Đã loại bỏ các mục Định Hướng Tương Lai và Giấy Phép theo yêu cầu -->
```
Dagster image already includes CUDA base for LightGBM / PyTorch acceleration.

### 6.5 Start Services
```bash
docker compose up -d
```

### 6.6 Verify Health
- Dagster UI: http://localhost:3000
- MinIO Console: http://localhost:9001 (login with root credentials)
- Trino UI: http://localhost:8090
- Spark Master UI: http://localhost:8082
- Streamlit App: http://localhost:8501
- Metabase: http://localhost:3007
- CloudBeaver: http://localhost:8978

## 7. Running the Project
### 7.1 Materialize Pipelines
Open Dagster UI → select ML asset group (`ML_pipeline`) → materialize assets sequentially:
1. Data loading & splitting (Spark) → `split_data`
2. Feature engineering assets: `handcrafted_feature_engineering`, `tfidf_svd_feature_engineering`, `sentence_transformer_feature_engineering`
3. Combine features → `combine_features`
4. Train models: `train_logistic_regression`, `train_svm`, `train_lightgbm`
5. Train ensemble: `train_stacking_ensemble` (produces `stacking_ensemble.pkl`)
6. Inference assets: `inference_logistic_regression`, `inference_svm`, `inference_lightgbm`, `inference_stacking_ensemble`, `compare_model_inference`

### 7.2 Inspect Artifacts
In MinIO bucket `models`:
- `model/` (individual and ensemble models)
- `transformers/` (TF-IDF + SVD fitted objects)
- `plots/` (performance and inference visualizations)

### 7.3 Use Streamlit Application
Navigate to http://localhost:8501 and input any news text. The app:
- Loads `stacking_ensemble.pkl`.
- Computes features using saved transformers.
- Returns prediction: class 1 = Real, class 0 = Fake.
- Displays calibrated confidence (probability of Real News).

### 7.4 GPU Behavior
- LightGBM attempts GPU when `torch.cuda.is_available()`.
- On failure (e.g., OpenCL errors), it transparently falls back to CPU.
- SentenceTransformer embeddings utilize CUDA if available.

### 7.5 Updating Models
Retrain by re-materializing training assets. The ensemble asset updates `stacking_ensemble.pkl` consumed by Streamlit.

## 8. Authors & Acknowledgements
### Development Team
- **Nguyễn Hà Minh Tuấn**
- **Trần Phan Thanh Tùng**
- **Trần Nguyễn Đức Trung**

Affiliation: **University of Information Technology (UIT)** – **Faculty of Information Engineering & Sciences**.

### Advisor
- **Dr. Hà Minh Tân** (Faculty of Information Engineering and Sciences)

## 9. Roadmap (Potential Enhancements)
- Add Kafka ingestion back (currently commented) for streaming pipelines.
- Implement model drift monitoring and scheduled retraining.
- Extend feature store abstraction and add real-time API gateway.
- Integrate model explainability (SHAP) and bias analysis.
- Add automated benchmarking across models with historical tracking.

## 10. License
(Define license terms here if applicable.)

---

# EnsemTrust (Phiên bản Tiếng Việt)

## 1. Giới Thiệu
EnsemTrust là nền tảng phát hiện tin giả toàn diện, kết hợp kỹ thuật dữ liệu hiện đại, truy vấn lakehouse, trích xuất đặc trưng đa tầng và mô hình học máy dạng ensemble. Hệ thống tiếp nhận dữ liệu văn bản thô, xử lý và làm giàu thành tập dữ liệu nhiều lớp (bronze → silver → gold), sau đó huấn luyện các mô hình cơ sở và một mô hình stacking ensemble. Ứng dụng Streamlit cung cấp suy luận thời gian thực với điểm tin cậy đã được hiệu chỉnh. Kiến trúc nhấn mạnh khả năng truy vết lineage, tính mô-đun, huấn luyện tăng tốc GPU (LightGBM, embeddings) và minh bạch đánh giá mô hình.

## 2. Các Tính Năng Chính
- Thiết kế data lake nhiều lớp (landing, bronze, silver, gold) trên MinIO.
- Pipeline tài sản Dagster có lineage rõ ràng và metadata chi tiết.
- Xử lý mở rộng bằng Spark cho tiền xử lý và tách tập.
- Trích xuất đặc trưng phong phú: đặc trưng ngôn ngữ thủ công, TF-IDF + SVD, embeddings SentenceTransformer.
- Nhiều mô hình ML: Logistic Regression, Linear SVM (Calibrated), LightGBM (hỗ trợ GPU), Stacking Ensemble.
- Huấn luyện nhận biết GPU với cơ chế fallback an toàn sang CPU.
- Quản lý tập trung artifacts (model, transformer, biểu đồ) trong bucket MinIO `models`.
- Tự động đánh giá: Accuracy, ROC AUC, classification report trên train/validation/test.
- Biểu đồ trực quan: confusion matrix, ROC curve, so sánh Accuracy/AUC, phân bố suy luận.
- Ứng dụng Streamlit suy luận thời gian thực (xác suất lớp 1 = độ tin cậy Tin Thật).
- Hệ thống truy vấn và khảo sát (Trino + Hive Metastore + CloudBeaver + Metabase).
- Triển khai mô-đun bằng Docker + docker-compose, hỗ trợ GPU NVIDIA tùy chọn.

## 3. Kiến Trúc
### 3.1 Tổng Quan
![Tổng quan kiến trúc](image/architecture_overview.png)

Thành phần:
- Dagster: điều phối pipeline dạng asset.
- MinIO: lưu trữ đối tượng và data lake phân lớp.
- Postgres: metadata Dagster, metastore Hive/Metabase.
- Hive Metastore + Trino: lớp truy vấn SQL.
- Spark: xử lý phân tán và tách dữ liệu.
- Lớp ML: trích xuất đặc trưng, huấn luyện, đánh giá.
- Streamlit: giao diện suy luận tương tác.
- Metabase / CloudBeaver: phân tích và khám phá dữ liệu.

### 3.2 Data Lineage
![Tổng quan lineage Dagster](image/dagster_lineage_overview.svg)
![Lớp Bronze](image/bronze_layer.svg) ![Lớp Silver](image/silver_layer.svg) ![Lớp Gold](image/gold_layer.svg)

Luồng:
1. Landing → Bronze: dữ liệu thô (title, text, subject, label) được version hóa.
2. Bronze → Silver: làm sạch, loại trùng, hợp nhất trường `content`.
3. Silver → Feature: chia train/validation/test (60/20/20) + trích xuất đặc trưng (handcrafted, TF-IDF+SVD, embeddings).
4. Kết Hợp Đặc Trưng: ghép embeddings + TF-IDF giảm chiều + handcrafted.
5. Huấn Luyện: Logistic Regression, Linear SVM (calibrated), LightGBM, sau đó Stacking Ensemble.
6. Suy Luận: các asset inference kiểm thử kịch bản mẫu và tạo biểu đồ.
7. Phục Vụ: `best_model.pkl` cho ứng dụng Streamlit.

### 3.3 Lớp Học Máy
![Lớp học máy](image/machine_learning_layer.svg)
- Calibration: LinearSVC bọc bởi `CalibratedClassifierCV` trả xác suất tin cậy.
- LightGBM: dùng tập validation (`eval_set`) chống overfitting, tự nhận GPU.
- Artifact:
  - Model: `models/model/*.pkl`
  - Transformer: `models/transformers/tfidf_vectorizer.pkl`, `svd_transformer.pkl`
  - Biểu đồ: `models/plots/*performance.png`, `inference_*.png`

## 4. Công Nghệ Sử Dụng
Danh mục | Công nghệ
---------|-----------
Điều phối | Dagster
Lưu trữ | MinIO
Cơ sở dữ liệu | Postgres
Truy vấn | Trino + Hive Metastore
Xử lý phân tán | Spark
ML/NLP | scikit-learn, LightGBM, SentenceTransformers, PyTorch
Đặc trưng | TF-IDF, SVD, handcrafted, embeddings MiniLM
Trực quan | Matplotlib, Seaborn, Streamlit, Metabase
Khám phá | CloudBeaver
Hạ tầng | Docker, docker-compose, GPU NVIDIA tùy chọn

## 5. Yêu Cầu Trước Khi Cài Đặt
- Docker và Docker Compose.
- Driver NVIDIA + NVIDIA Container Toolkit (nếu dùng GPU).
- Tài nguyên: khuyến nghị ≥16GB RAM.
- Mở các port dịch vụ (3000, 8501, 9000/9001, 8082, 8090, 8978, 3007).

## 6. Hướng Dẫn Cài Đặt
### 6.1 Clone Dự Án
```bash
git clone https://github.com/MinhTuan2405/EnsemTrust.git
cd EnsemTrust
```

### 6.2 Thiết Lập Biến Môi Trường
```bash
cp .example.env .env
```
Chỉnh sửa: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, RANDOM_STATE.

### 6.3 Thiết Lập GPU (Tuỳ Chọn)
#### Linux
Thực hiện các lệnh cài driver và toolkit giống phần tiếng Anh.

#### Windows (WSL2)
Cài driver NVIDIA Windows, cập nhật WSL2, thực hiện lệnh Linux bên trong WSL.

### 6.4 Build Image
```bash
docker compose build
```

### 6.5 Khởi Chạy Dịch Vụ
```bash
docker compose up -d
```

### 6.6 Kiểm Tra
- Dagster: http://localhost:3000
- MinIO: http://localhost:9001
- Trino: http://localhost:8090
- Spark: http://localhost:8082
- Streamlit: http://localhost:8501
- Metabase: http://localhost:3007
- CloudBeaver: http://localhost:8978

## 7. Cách Chạy Pipeline
1. Materialize `split_data`.
2. Chạy các asset đặc trưng: `handcrafted_feature_engineering`, `tfidf_svd_feature_engineering`, `sentence_transformer_feature_engineering`.
3. Kết hợp: `combine_features`.
4. Huấn luyện: `train_logistic_regression`, `train_svm`, `train_lightgbm`.
5. Ensemble: `train_stacking_ensemble` (lưu `stacking_ensemble.pkl`).
6. Suy luận: `inference_*` và `compare_model_inference`.

## 8. Ứng Dụng Streamlit
Truy cập http://localhost:8501, nhập văn bản. Hệ thống:
- Tải `stacking_ensemble.pkl`.
- Dùng transformer đã lưu để trích xuất đặc trưng.
- Trả kết quả: lớp 1 = Tin Thật, lớp 0 = Tin Giả.
- Hiển thị độ tin cậy (xác suất tin thật).

## 9. GPU Hoạt Động
- LightGBM thử GPU; nếu lỗi sẽ fallback CPU.
- Embeddings dùng CUDA nếu có.

## 10. Tác Giả & Cố Vấn
Nhóm phát triển:
- **Nguyễn Hà Minh Tuấn**
- **Trần Phan Thanh Tùng**
- **Trần Nguyễn Đức Trung**

Thuộc **Trường Đại học Công nghệ Thông tin (UIT)** – **Khoa Khoa học Kĩ thuật Thông tin**.

Người hướng dẫn:
- **Tiến sĩ Hà Minh Tân** (Giảng viên Khoa Khoa học Kĩ thuật Thông tin)

## 11. Định Hướng Tương Lai
- Khôi phục pipeline streaming Kafka.
- Giám sát drift và tái huấn luyện định kỳ.
- Bổ sung Explainability (SHAP) và phân tích thiên lệch.
- Thêm benchmark lịch sử và cảnh báo suy thoái mô hình.

## 12. Giấy Phép
(Bổ sung nếu cần.)

---

End of README.
