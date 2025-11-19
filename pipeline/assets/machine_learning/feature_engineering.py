from dagster import AssetCheckEvaluation, AssetIn, asset, AssetExecutionContext, Output
from pipeline.utils.spark import create_spark_session
from datetime import datetime
from pyspark.sql.functions import col, coalesce, lit, concat_ws
from sklearn.model_selection import train_test_split


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
    context.log.info(f'SparkSession created: {app_name}')

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
    
    # Combine back for downstream
    train_df = X_train.copy()
    train_df['label'] = y_train
    
    val_df = X_val.copy()
    val_df['label'] = y_val
    
    test_df = X_test.copy()
    test_df['label'] = y_test
    
    return Output(
        value={
            "train": train_df,
            "validation": val_df,
            "test": test_df,
            "full_data": pd_df
        },
        metadata={
            "total_records": len(pd_df),
            "train_records": len(train_df),
            "validation_records": len(val_df),
            "test_records": len(test_df),
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
    
    if split_data is None or 'train' not in split_data:
        context.log.error("Train data not available in split_data")
        return None
    
    train_df = split_data['train']
    
    context.log.info(f"Train data loaded: {len(train_df)} samples")
    context.log.info(f"Columns: {train_df.columns.tolist()}")
    context.log.info(f"Label distribution:\n{train_df['label'].value_counts()}")
    
    return Output(
        value=train_df,
        metadata={
            "records": len(train_df),
            "columns": train_df.columns.tolist(),
            "fake_count": int((train_df['label'] == 0).sum()),
            "real_count": int((train_df['label'] == 1).sum())
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
    
    if split_data is None or 'validation' not in split_data:
        context.log.error("Validation data not available in split_data")
        return None
    
    val_df = split_data['validation']
    
    context.log.info(f"Validation data loaded: {len(val_df)} samples")
    context.log.info(f"Columns: {val_df.columns.tolist()}")
    context.log.info(f"Label distribution:\n{val_df['label'].value_counts()}")
    
    return Output(
        value=val_df,
        metadata={
            "records": len(val_df),
            "columns": val_df.columns.tolist(),
            "fake_count": int((val_df['label'] == 0).sum()),
            "real_count": int((val_df['label'] == 1).sum())
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
    
    if split_data is None or 'test' not in split_data:
        context.log.error("Test data not available in split_data")
        return None
    
    test_df = split_data['test']
    
    context.log.info(f"Test data loaded: {len(test_df)} samples")
    context.log.info(f"Columns: {test_df.columns.tolist()}")
    context.log.info(f"Label distribution:\n{test_df['label'].value_counts()}")
    
    return Output(
        value=test_df,
        metadata={
            "records": len(test_df),
            "columns": test_df.columns.tolist(),
            "fake_count": int((test_df['label'] == 0).sum()),
            "real_count": int((test_df['label'] == 1).sum())
        }
    )


