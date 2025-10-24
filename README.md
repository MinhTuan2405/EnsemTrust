# End-to-End Fake News Detection Platform

This project is a comprehensive, end-to-end platform for detecting fake news. It implements a modern data stack (Lakehouse architecture) and an MLOps pipeline to ingest, process, analyze, and serve predictions on news data.

## Problem Statement

The rapid spread of misinformation poses a significant challenge. This project aims to build a scalable and reliable system that can ingest news articles from various sources, process them in near real-time, and accurately classify them as 'real' or 'fake' using advanced ensemble learning models.

## Architecture

The system is designed as a modular, containerized application orchestrated by Docker Compose. It follows a Data Lakehouse (Medallion) architecture for data processing and an end-to-end MLOps pipeline for machine learning.

![Project Architecture Diagram](./image/architecture.png)


## Key Features

* **Real-time Data Ingestion:** Uses **Kafka** to handle streaming data from various sources (CSVs, Kaggle datasets).
* **Data Lakehouse:** Implements a Medallion Architecture (**Raw**, **Silver**, **Gold** layers) on **MinIO** for scalable object storage.
* **Large-Scale Processing:** Leverages **Apache Spark** for transforming data between lake layers.
* **Centralized Metadata:** Uses **Hive Metastore** to manage schemas for the data lake.
* **High-Performance Querying:** Employs **Trino** as the query engine to analyze data directly from MinIO.
* **Metric Transformation:** Uses **dbt** for robust, SQL-based metric and business logic transformations on the Gold layer.
* **Advanced AI/ML:**
    * Features an **Ensemble Learning** pipeline using a Voting classifier.
    * Combines three powerful transformer models: `phobert-base`, `velectra-base-discriminator-cased`, and `distilbert-base-multilingual-cased`.
    * Includes a **Model Registry** for versioning and managing ML models.
* **Orchestration:** All data and AI pipelines are orchestrated and monitored by **Dagster**.
* **Visualization & UI:**
    * **Metabase** provides BI dashboards and visualizations by querying Trino.
    * **Streamlit** serves as the front-end application for user interaction.
* **Containerization:** The entire stack is containerized with **Docker** and managed via **Docker Compose** for easy setup and portability.

## Technology Stack

| Category | Technology |
| :--- | :--- |
| **Orchestration** | Dagster |
| **Data Ingestion** | Kafka |
| **Data Lake Storage** | MinIO |
| **Data Processing** | Apache Spark |
| **Query Engine** | Trino (formerly PrestoSQL) |
| **Metadata Store** | Hive Metastore |
| **Transformation** | dbt (Data Build Tool) |
| **ML Pipeline** | Hugging Face Transformers, scikit-learn |
| **Visualization** | Metabase |
| **Front-end App** | Streamlit |
| **Database Admin** | CloudBeaver |
| **Containerization** | Docker, Docker Compose |

## How It Works: Pipeline Overview

The system is divided into two main pipelines, both orchestrated by Dagster:

### 1. Data Warehouse Pipeline (ELT)

1.  **Ingest:** Data sources (CSVs, etc.) are streamed into **Kafka** topics.
2.  **Land (Raw):** A Spark job consumes from Kafka and lands the raw, unchanged data into the **Raw Layer** in MinIO.
3.  **Process (Silver):** Another Spark job reads from the Raw Layer, applies cleaning, deduplication, and standardization, and saves the result to the **Silver Layer**.
4.  **Enrich (Gold):** A final Spark job (or dbt model) aggregates data, joins it with other sources, and creates the analysis-ready **Gold Layer**.
5.  **Query:** **Trino** uses the **Hive Metastore** to query this data across all layers. **dbt** builds final metric tables on the Gold layer.

### 2. AI Pipeline (MLOps)

1.  **Trigger:** A Kafka topic (or a Dagster schedule) triggers the AI pipeline.
2.  **Tokenize:** Input text data is passed through a **Tokenizer**.
3.  **Ensemble Predict:** The tokens are fed into the three parallel transformer models (PhoBERT, Electra, DistilBERT).
4.  **Vote:** A **Voting** mechanism combines the three predictions to produce a final, more robust classification (real/fake).
5.  **Store Result:** The final prediction (**"store voting result"**) is written back into the **Gold Layer** of the Data Warehouse.
6.  **Analyze:** With the predictions now in the Gold Layer, **Metabase** and **Streamlit** can query them via Trino to display results and insights.

## Getting Started

### Prerequisites

* [Docker](https://www.docker.com/get-started)
* [Docker Compose](https://docs.docker.com/compose/install/)

### Installation

1.  Clone the repository:
    ```bash
    git clone [YOUR_REPOSITORY_URL]
    cd [YOUR_PROJECT_DIRECTORY]
    ```

2.  (Optional) Configure environment variables. You may need to create a `.env` file based on a provided `.template.env`.

3.  Build and run all services:
    ```bash
    docker compose up --build -d
    ```

## Usage

Once all containers are running, you can access the different services:

* **Dagster UI (Orchestration):** `http://localhost:3000`
* **Streamlit App (Front-end):** `http://localhost:8501`
* **Metabase (BI Dashboard):** `http://localhost:3030`
* **MinIO Console (Data Lake):** `http://localhost:9001`
* **CloudBeaver (DB Admin):** `http://localhost:8978`
* *(Note: Ports may vary based on your `docker-compose.yml` configuration.)*

## Future Work

* **Model Serving API:** Implement a dedicated API (e.g., using FastAPI) to serve the model from the Model Registry for real-time, on-demand predictions in Streamlit.
* **Automated Retraining:** Build a Dagster pipeline that periodically retrains the ensemble model on new data from the Gold Layer.
* **Web Scraper:** Integrate a web scraping component (e.g., Scrapy) to continuously feed new articles into the Kafka pipeline.