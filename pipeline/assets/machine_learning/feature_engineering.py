from dagster import AssetCheckEvaluation, AssetIn, asset, AssetExecutionContext, Output
from pipeline.utils.spark import create_spark_session
from datetime import datetime
from pyspark.sql.functions import col, coalesce, lit, concat_ws
from sklearn.model_selection import train_test_split
from pipeline.utils.feature_engineer import handcrafted_features, encode_texts_st, combine, create_tfidf_vectorizer, create_svd_transformer
import pickle
from io import BytesIO

@asset(
    description='Feature engineering and split data into train/test sets',
    compute_kind='Spark',
    required_resource_keys={'minio_resource'},
    group_name='ML_pipeline',
    ins={
        'load_data_from_silver': AssetIn('load_data_from_silver')
    }
)
def split_data(context: AssetExecutionContext, load_data_from_silver):

    timestamp = datetime.now()
    app_name = f'split_data{timestamp.strftime("%Y%m%d_%H%M%S")}'

    spark = create_spark_session(app_name)
    spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "false")
    context.log.info(f'SparkSession created: {app_name}')

    # Tắt Arrow để tránh lỗi ArrowInvalid khi toPandas
    spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "false")
    spark.conf.set("spark.sql.execution.arrow.pyspark.fallback.enabled", "true")

    # Convert Pandas to Spark DataFrame
    df = spark.createDataFrame(load_data_from_silver)
    
    initial_count = df.count()
    context.log.info(f"Initial records: {initial_count}")

    # Drop duplicates
    df = df.dropDuplicates()
    dedup_count = df.count()
    context.log.info(f"After deduplication: {dedup_count} (removed {initial_count - dedup_count})")


    # Create content = title + text + subject, replace null by ''
    df = df.withColumn(
        "content",
        concat_ws(" ", 
                  coalesce(col("title"), lit("")), 
                  coalesce(col("text"), lit("")),
                  coalesce(col("subject"), lit(""))
        )
    )
    context.log.info("Created 'content' column by concatenating title, text and subject")

    # Select final columns for ML
    df = df.select("content", "label")
    
    # Show sample
    context.log.info("Sample data after feature engineering:")
    df.show(3, truncate=50)

    # Convert to Pandas for train/test split
    pd_df = df.toPandas()
    
    spark.stop()
    context.log.info("SparkSession stopped, converted to Pandas DataFrame")
    
    # Split data: 60% train, 20% validation, 20% test, stratify by label
    # Only use 'content' column as feature 
    X = pd_df['content']
    y = pd_df['label']
    
    # First split: 80% temp (train+val), 20% test
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, 
        test_size=0.2, 
        random_state=42, 
        stratify=y
    )
    
    # Second split: 75% train, 25% val (from temp = 60% and 20% of total)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, 
        test_size=0.25, 
        random_state=42, 
        stratify=y_temp
    )
    
    context.log.info(f"Train set: {len(X_train)} samples ({len(X_train)/len(pd_df)*100:.1f}%)")
    context.log.info(f"Validation set: {len(X_val)} samples ({len(X_val)/len(pd_df)*100:.1f}%)")
    context.log.info(f"Test set: {len(X_test)} samples ({len(X_test)/len(pd_df)*100:.1f}%)")
    context.log.info(f"Shapes: train={X_train.shape}, val={X_val.shape}, test={X_test.shape}")
    context.log.info(f"Train label distribution:\n{y_train.value_counts()}")
    context.log.info(f"Validation label distribution:\n{y_val.value_counts()}")
    context.log.info(f"Test label distribution:\n{y_test.value_counts()}")
    
    return Output(
        value={
            "X_train": X_train,
            "y_train": y_train,
            "X_val": X_val,
            "y_val": y_val,
            "X_test": X_test,
            "y_test": y_test
        },
        metadata={
            "total_records": len(pd_df),
            "train_records": len(X_train),
            "validation_records": len(X_val),
            "test_records": len(X_test),
            "train_split": 0.6,
            "validation_split": 0.2,
            "test_split": 0.2,
            "feature": "content",
            "train_fake": int((y_train == 0).sum()),
            "train_real": int((y_train == 1).sum()),
            "val_fake": int((y_val == 0).sum()),
            "val_real": int((y_val == 1).sum()),
            "test_fake": int((y_test == 0).sum()),
            "test_real": int((y_test == 1).sum())
        }
    )


@asset(
    description='Load train dataset from split_data',
    compute_kind='Python',
    group_name='ML_pipeline',
    ins={
        'split_data': AssetIn('split_data')
    }
)
def load_train_data(context: AssetExecutionContext, split_data):
    
    if split_data is None or 'X_train' not in split_data or 'y_train' not in split_data:
        context.log.error("Train data not available in split_data")
        return None
    
    X_train = split_data['X_train']
    y_train = split_data['y_train']
    
    context.log.info(f"Train data loaded: {len(X_train)} samples")
    context.log.info(f"X_train type: {type(X_train)}, shape: {X_train.shape}")
    context.log.info(f"y_train type: {type(y_train)}, shape: {y_train.shape}")
    context.log.info(f"Label distribution:\n{y_train.value_counts()}")
    
    return Output(
        value={
            'content': X_train,
            'label': y_train
        },
        metadata={
            "records": len(X_train),
            "fake_count": int((y_train == 0).sum()),
            "real_count": int((y_train == 1).sum())
        }
    )


@asset(
    description='Load validation dataset from split_data',
    compute_kind='Python',
    group_name='ML_pipeline',
    ins={
        'split_data': AssetIn('split_data')
    }
)
def load_validation_data(context: AssetExecutionContext, split_data):
    
    if split_data is None or 'X_val' not in split_data or 'y_val' not in split_data:
        context.log.error("Validation data not available in split_data")
        return None
    
    X_val = split_data['X_val']
    y_val = split_data['y_val']
    
    context.log.info(f"Validation data loaded: {len(X_val)} samples")
    context.log.info(f"X_val type: {type(X_val)}, shape: {X_val.shape}")
    context.log.info(f"y_val type: {type(y_val)}, shape: {y_val.shape}")
    context.log.info(f"Label distribution:\n{y_val.value_counts()}")
    
    return Output(
        value={
            'content': X_val,
            'label': y_val
        },
        metadata={
            "records": len(X_val),
            "fake_count": int((y_val == 0).sum()),
            "real_count": int((y_val == 1).sum())
        }
    )


@asset(
    description='Load test dataset from split_data',
    compute_kind='Python',
    group_name='ML_pipeline',
    ins={
        'split_data': AssetIn('split_data')
    }
)
def load_test_data(context: AssetExecutionContext, split_data):
    
    if split_data is None or 'X_test' not in split_data or 'y_test' not in split_data:
        context.log.error("Test data not available in split_data")
        return None
    
    X_test = split_data['X_test']
    y_test = split_data['y_test']
    
    context.log.info(f"Test data loaded: {len(X_test)} samples")
    context.log.info(f"X_test type: {type(X_test)}, shape: {X_test.shape}")
    context.log.info(f"y_test type: {type(y_test)}, shape: {y_test.shape}")
    context.log.info(f"Label distribution:\n{y_test.value_counts()}")
    
    return Output(
        value={
            'content': X_test,
            'label': y_test
        },
        metadata={
            "records": len(X_test),
            "fake_count": int((y_test == 0).sum()),
            "real_count": int((y_test == 1).sum())
        }
    )


@asset(
    description='Extract handcrafted linguistic features from text',
    compute_kind='Python',
    group_name='ML_pipeline',
    ins={
        'load_test_data': AssetIn('load_test_data'),
        'load_validation_data': AssetIn('load_validation_data'),
        'load_train_data': AssetIn('load_train_data')
    }
)
def handcrafted_feature_engineering(context: AssetExecutionContext,
                                    load_test_data,
                                    load_validation_data,
                                    load_train_data):
    
    # Validate input data
    if load_train_data is None or load_validation_data is None or load_test_data is None:
        context.log.error("One or more input datasets are None")
        return None
    
    # Extract content text from each split (as Series)
    X_train = load_train_data['content']
    X_val = load_validation_data['content']
    X_test = load_test_data['content']
    
    context.log.info('Starting handcrafted feature engineering')
    context.log.info(f'Train shape: {X_train.shape}, Val shape: {X_val.shape}, Test shape: {X_test.shape}')
    context.log.info(f'Extracted text content: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}')
    
    # Compute handcrafted features (pass Series directly)
    context.log.info('Computing handcrafted linguistic features...')
    X_train_hand = handcrafted_features(X_train)
    X_val_hand = handcrafted_features(X_val)
    X_test_hand = handcrafted_features(X_test)
    
    context.log.info(f'Handcrafted features shapes: train={X_train_hand.shape}, val={X_val_hand.shape}, test={X_test_hand.shape}')
    
    # Extract labels and text
    y_train = load_train_data['label']
    y_val = load_validation_data['label']
    y_test = load_test_data['label']
    
    return Output(
        value={
            'train': {
                'X': X_train_hand,
                'y': y_train
            },
            'validation': {
                'X': X_val_hand,
                'y': y_val
            },
            'test': {
                'X': X_test_hand,
                'y': y_test
            }
        },
        metadata={
            "train_samples": int(X_train_hand.shape[0]),
            "validation_samples": int(X_val_hand.shape[0]),
            "test_samples": int(X_test_hand.shape[0]),
            "num_features": int(X_train_hand.shape[1]),
            "feature_names": X_train_hand.columns.tolist(),
            "train_fake": int((y_train == 0).sum()),
            "train_real": int((y_train == 1).sum()),
            "val_fake": int((y_val == 0).sum()),
            "val_real": int((y_val == 1).sum()),
            "test_fake": int((y_test == 0).sum()),
            "test_real": int((y_test == 1).sum())
        }
    )


@asset(
    description='Extract TF-IDF features and apply SVD dimensionality reduction',
    compute_kind='Python',
    required_resource_keys={'minio_resource'},
    group_name='ML_pipeline',
    ins={
        'load_test_data': AssetIn('load_test_data'),
        'load_validation_data': AssetIn('load_validation_data'),
        'load_train_data': AssetIn('load_train_data')
    }
)
def tfidf_svd_feature_engineering(context: AssetExecutionContext,
                                  load_test_data,
                                  load_validation_data,
                                  load_train_data):
    
    # Validate input data
    if load_train_data is None or load_validation_data is None or load_test_data is None:
        context.log.error("One or more input datasets are None")
        return None
    
    context.log.info('Starting TF-IDF + SVD feature engineering')

    # Create new instances for each run (from factory functions)
    tfidf = create_tfidf_vectorizer()
    svd = create_svd_transformer()
    
    # Extract content text from each split
    X_train = load_train_data['content']
    X_val = load_validation_data['content']
    X_test = load_test_data['content']
    
    context.log.info(f'Extracted text content: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}')
    
    # Step 1: TF-IDF Vectorization
    context.log.info('Step 1: Computing TF-IDF features')
    X_train_tfidf = tfidf.fit_transform(X_train)
    X_val_tfidf = tfidf.transform(X_val)
    X_test_tfidf = tfidf.transform(X_test)
    
    context.log.info(f'TF-IDF shapes: train={X_train_tfidf.shape}, val={X_val_tfidf.shape}, test={X_test_tfidf.shape}')
    
    # Step 2: SVD Dimensionality Reduction
    context.log.info('Step 2: Applying SVD dimensionality reduction')
    X_train_tfidf_svd = svd.fit_transform(X_train_tfidf)
    X_val_tfidf_svd = svd.transform(X_val_tfidf)
    X_test_tfidf_svd = svd.transform(X_test_tfidf)
    
    context.log.info(f'TF-IDF+SVD shapes: train={X_train_tfidf_svd.shape}, val={X_val_tfidf_svd.shape}, test={X_test_tfidf_svd.shape}')
    
    # Step 3: Save fitted transformers to MinIO
    context.log.info('Step 3: Saving fitted transformers to MinIO')
    
    minio_client = context.resources.minio_resource
    bucket_name = "models"
    
    # Ensure bucket exists
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
        context.log.info(f"Created bucket: {bucket_name}")
    
    # Save TF-IDF vectorizer
    tfidf_buffer = BytesIO()
    pickle.dump(tfidf, tfidf_buffer)
    tfidf_buffer.seek(0)
    
    tfidf_path = "transformers/tfidf_vectorizer.pkl"
    minio_client.put_object(
        bucket_name,
        tfidf_path,
        tfidf_buffer,
        length=tfidf_buffer.getbuffer().nbytes,
        content_type="application/octet-stream"
    )
    context.log.info(f"Saved TF-IDF vectorizer to s3://{bucket_name}/{tfidf_path}")
    
    # Save SVD transformer
    svd_buffer = BytesIO()
    pickle.dump(svd, svd_buffer)
    svd_buffer.seek(0)
    
    svd_path = "transformers/svd_transformer.pkl"
    minio_client.put_object(
        bucket_name,
        svd_path,
        svd_buffer,
        length=svd_buffer.getbuffer().nbytes,
        content_type="application/octet-stream"
    )
    context.log.info(f"Saved SVD transformer to s3://{bucket_name}/{svd_path}")
    
    # Extract labels and text
    y_train = load_train_data['label']
    y_val = load_validation_data['label']
    y_test = load_test_data['label']
    
    return Output(
        value={
            'train': {
                'X': X_train_tfidf_svd,
                'y': y_train
            },
            'validation': {
                'X': X_val_tfidf_svd,
                'y': y_val
            },
            'test': {
                'X': X_test_tfidf_svd,
                'y': y_test
            }
        },
        metadata={
            "train_samples": int(X_train_tfidf_svd.shape[0]),
            "validation_samples": int(X_val_tfidf_svd.shape[0]),
            "test_samples": int(X_test_tfidf_svd.shape[0]),
            "num_features": int(X_train_tfidf_svd.shape[1]),
            "tfidf_vectorizer_path": f"s3://{bucket_name}/{tfidf_path}",
            "svd_transformer_path": f"s3://{bucket_name}/{svd_path}",
            "train_fake": int((y_train == 0).sum()),
            "train_real": int((y_train == 1).sum()),
            "val_fake": int((y_val == 0).sum()),
            "val_real": int((y_val == 1).sum()),
            "test_fake": int((y_test == 0).sum()),
            "test_real": int((y_test == 1).sum())
        }
    )


@asset(
    description='Extract sentence embeddings using SentenceTransformer',
    compute_kind='Python',
    group_name='ML_pipeline',
    ins={
        'load_test_data': AssetIn('load_test_data'),
        'load_validation_data': AssetIn('load_validation_data'),
        'load_train_data': AssetIn('load_train_data')
    }
)
def sentence_transformer_feature_engineering(context: AssetExecutionContext,
                                            load_test_data,
                                            load_validation_data,
                                            load_train_data):
    
    # Validate input data
    if load_train_data is None or load_validation_data is None or load_test_data is None:
        context.log.error("One or more input datasets are None")
        return None
    
    context.log.info('Starting Sentence Transformer feature engineering')
    
    # Extract content text from each split
    X_train = load_train_data['content']
    X_val = load_validation_data['content']
    X_test = load_test_data['content']
    
    context.log.info(f'Extracted text content: train={len(X_train)}, val={len(X_val)}, test={len(X_test)}')
    
    # Compute sentence embeddings
    context.log.info('Computing Sentence Transformer embeddings...')
    X_train_st = encode_texts_st(X_train.tolist(), batch_size=32)
    X_val_st = encode_texts_st(X_val.tolist(), batch_size=32)
    X_test_st = encode_texts_st(X_test.tolist(), batch_size=32)
    
    context.log.info(f'SentenceTransformer shapes: train={X_train_st.shape}, val={X_val_st.shape}, test={X_test_st.shape}')
    
    # Extract labels and text
    y_train = load_train_data['label']
    y_val = load_validation_data['label']
    y_test = load_test_data['label']
    
    return Output(
        value={
            'train': {
                'X': X_train_st,
                'y': y_train
            },
            'validation': {
                'X': X_val_st,
                'y': y_val
            },
            'test': {
                'X': X_test_st,
                'y': y_test
            }
        },
        metadata={
            "train_samples": int(X_train_st.shape[0]),
            "validation_samples": int(X_val_st.shape[0]),
            "test_samples": int(X_test_st.shape[0]),
            "num_features": int(X_train_st.shape[1]),
            "model": "all-MiniLM-L6-v2",
            "train_fake": int((y_train == 0).sum()),
            "train_real": int((y_train == 1).sum()),
            "val_fake": int((y_val == 0).sum()),
            "val_real": int((y_val == 1).sum()),
            "test_fake": int((y_test == 0).sum()),
            "test_real": int((y_test == 1).sum())
        }
    )


@asset(
    description='Combine all feature types into final feature matrix',
    compute_kind='Python',
    group_name='ML_pipeline',
    ins={
        'handcrafted_feature_engineering': AssetIn('handcrafted_feature_engineering'),
        'tfidf_svd_feature_engineering': AssetIn('tfidf_svd_feature_engineering'),
        'sentence_transformer_feature_engineering': AssetIn('sentence_transformer_feature_engineering')
    }
)
def combine_features(context: AssetExecutionContext,
                    handcrafted_feature_engineering,
                    tfidf_svd_feature_engineering,
                    sentence_transformer_feature_engineering):
    
    context.log.info('Starting feature combination')
    
    # Get feature arrays and labels from each engineering asset
    X_train_hand = handcrafted_feature_engineering['train']['X']
    X_val_hand = handcrafted_feature_engineering['validation']['X']
    X_test_hand = handcrafted_feature_engineering['test']['X']
    
    X_train_tfidf_svd = tfidf_svd_feature_engineering['train']['X']
    X_val_tfidf_svd = tfidf_svd_feature_engineering['validation']['X']
    X_test_tfidf_svd = tfidf_svd_feature_engineering['test']['X']
    
    X_train_st = sentence_transformer_feature_engineering['train']['X']
    X_val_st = sentence_transformer_feature_engineering['validation']['X']
    X_test_st = sentence_transformer_feature_engineering['test']['X']
    
    # Get labels (same across all feature engineering assets)
    y_train = handcrafted_feature_engineering['train']['y']
    y_val = handcrafted_feature_engineering['validation']['y']
    y_test = handcrafted_feature_engineering['test']['y']
    
    context.log.info(f'Feature shapes before combination:')
    context.log.info(f'  Handcrafted: train={X_train_hand.shape}, val={X_val_hand.shape}, test={X_test_hand.shape}')
    context.log.info(f'  TF-IDF+SVD: train={X_train_tfidf_svd.shape}, val={X_val_tfidf_svd.shape}, test={X_test_tfidf_svd.shape}')
    context.log.info(f'  SentenceTransformer: train={X_train_st.shape}, val={X_val_st.shape}, test={X_test_st.shape}')
    
    # Combine all features using combine() function: emb, tfidf_svd, hand
    # Order: SentenceTransformer embeddings + TF-IDF+SVD + Handcrafted
    X_train_combined = combine(X_train_st, X_train_tfidf_svd, X_train_hand)
    X_val_combined = combine(X_val_st, X_val_tfidf_svd, X_val_hand)
    X_test_combined = combine(X_test_st, X_test_tfidf_svd, X_test_hand)
    
    context.log.info(f'Combined feature shapes: train={X_train_combined.shape}, val={X_val_combined.shape}, test={X_test_combined.shape}')
    context.log.info('Feature combination completed successfully')
    
    return Output(
        value={
            'train': {
                'X': X_train_combined,
                'y': y_train
            },
            'validation': {
                'X': X_val_combined,
                'y': y_val
            },
            'test': {
                'X': X_test_combined,
                'y': y_test
            }
        },
        metadata={
            "train_samples": int(X_train_combined.shape[0]),
            "validation_samples": int(X_val_combined.shape[0]),
            "test_samples": int(X_test_combined.shape[0]),
            "total_features": int(X_train_combined.shape[1]),
            "tfidf_svd_features": int(X_train_tfidf_svd.shape[1]),
            "sentence_transformer_features": int(X_train_st.shape[1]),
            "handcrafted_features": int(X_train_hand.shape[1]),
            "train_fake": int((y_train == 0).sum()),
            "train_real": int((y_train == 1).sum()),
            "val_fake": int((y_val == 0).sum()),
            "val_real": int((y_val == 1).sum()),
            "test_fake": int((y_test == 0).sum()),
            "test_real": int((y_test == 1).sum())
        }
    )