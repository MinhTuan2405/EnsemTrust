from dagster import asset, AssetExecutionContext, AssetIn, Output, MetadataValue
from pipeline.utils.models import predict_fake_news
import pickle
from io import BytesIO
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# Test cases for inference
TEST_CASES = [
    # Tin giả giật gân
    ("Aliens have landed in New York City and are communicating with the mayor.", "fake"),
    ("Vaccines cause autism according to a leaked government report.", "fake"),
    ("Donald Trump will be the king of the world next year.", "fake"),

    # Tin thật
    ("NASA successfully launched the James Webb Space Telescope into orbit.", "real"),
    ("The European Union agreed on new climate change targets for 2030.", "real"),
    ("The World Health Organization recommends wearing masks during flu season.", "real"),

    # Tin trung lập hoặc nửa thật
    ("France is part of the European Union and has Paris as its capital.", "neutral"),
    ("The stock market closed higher today after the Federal Reserve announcement.", "neutral"),
    ("Scientists discovered a new species of frog in the Amazon rainforest.", "neutral"),

    # Tin giật gân nhưng có thể thật (kiểm tra model không quá nhạy)
    ("Bitcoin price reaches an all-time high of $100,000.", "borderline"),
    ("Elon Musk announces a new plan to colonize Mars in the next decade.", "borderline")
]


@asset(
    description='Test Logistic Regression model with inference test cases',
    compute_kind='Python',
    required_resource_keys={'minio_resource'},
    group_name='ML_pipeline',
    ins={
        'train_logistic_regression': AssetIn('train_logistic_regression')
    }
)
def inference_logistic_regression(context: AssetExecutionContext, train_logistic_regression):
    """Load trained Logistic Regression model and test with sample cases."""
    
    context.log.info('Running inference with Logistic Regression model')
    
    # Use the trained model passed from training asset
    model = train_logistic_regression
    
    # Get MinIO client
    minio_client = context.resources.minio_resource
    
    # Prepare results
    results = []
    
    for i, (text, expected_type) in enumerate(TEST_CASES, 1):
        context.log.info(f"Case {i}: {text[:50]}...")
        
        # Predict
        pred, prob = predict_fake_news([text], model, minio_client)
        prediction = "REAL" if pred[0] == 1 else "FAKE"
        probability = float(prob[0])
        
        context.log.info(f"  Prediction: {prediction}, Probability (real): {probability:.4f}")
        
        results.append({
            "case": i,
            "text": text,
            "expected_type": expected_type,
            "prediction": prediction,
            "predicted_label": int(pred[0]),
            "probability_real": probability,
            "probability_fake": 1 - probability
        })
    
    # Create results DataFrame
    df = pd.DataFrame(results)
    
    # Create visualization
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle('Logistic Regression Inference Results', fontsize=16, fontweight='bold')
    
    # 1. Probability distribution
    x_pos = range(len(df))
    colors = ['#FF5252' if p == 'FAKE' else '#4CAF50' for p in df['prediction']]
    
    bars = axes[0].bar(x_pos, df['probability_real'], color=colors, alpha=0.7, edgecolor='black')
    axes[0].axhline(y=0.5, color='gray', linestyle='--', linewidth=2, label='Threshold (0.5)')
    axes[0].set_xlabel('Test Case')
    axes[0].set_ylabel('Probability (Real)')
    axes[0].set_title('Probability Distribution Across Test Cases')
    axes[0].set_xticks(x_pos)
    axes[0].set_xticklabels([f"Case {i}" for i in df['case']], rotation=45)
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar, prob in zip(bars, df['probability_real']):
        height = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2., height,
                    f'{prob:.3f}', ha='center', va='bottom', fontsize=9)
    
    # 2. Prediction summary by expected type
    type_counts = df.groupby(['expected_type', 'prediction']).size().unstack(fill_value=0)
    type_counts.plot(kind='bar', ax=axes[1], color=['#FF5252', '#4CAF50'], alpha=0.7, edgecolor='black')
    axes[1].set_xlabel('Expected Type')
    axes[1].set_ylabel('Count')
    axes[1].set_title('Prediction Distribution by Expected Type')
    axes[1].legend(title='Prediction', labels=['FAKE', 'REAL'])
    axes[1].set_xticklabels(axes[1].get_xticklabels(), rotation=45)
    axes[1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot to buffer and MinIO
    minio_client = context.resources.minio_resource
    bucket_name = "models"
    
    plot_buffer = BytesIO()
    plt.savefig(plot_buffer, format='png', dpi=150, bbox_inches='tight')
    plot_buffer.seek(0)
    
    # Save to MinIO
    plot_path = "plots/inference_logistic_regression.png"
    minio_client.put_object(
        bucket_name,
        plot_path,
        plot_buffer,
        length=plot_buffer.getbuffer().nbytes,
        content_type="image/png"
    )
    context.log.info(f"Saved plot to s3://{bucket_name}/{plot_path}")
    
    plot_buffer.seek(0)
    plt.close()
    
    # Calculate summary statistics
    avg_prob_fake = df[df['expected_type'] == 'fake']['probability_real'].mean()
    avg_prob_real = df[df['expected_type'] == 'real']['probability_real'].mean()
    avg_prob_neutral = df[df['expected_type'] == 'neutral']['probability_real'].mean()
    avg_prob_borderline = df[df['expected_type'] == 'borderline']['probability_real'].mean()
    
    context.log.info(f"Average probability (real) for expected FAKE news: {avg_prob_fake:.4f}")
    context.log.info(f"Average probability (real) for expected REAL news: {avg_prob_real:.4f}")
    context.log.info(f"Average probability (real) for NEUTRAL news: {avg_prob_neutral:.4f}")
    context.log.info(f"Average probability (real) for BORDERLINE news: {avg_prob_borderline:.4f}")
    
    return Output(
        value=df.to_dict('records'),
        metadata={
            "model_type": "LogisticRegression",
            "total_cases": len(df),
            "fake_predictions": int((df['prediction'] == 'FAKE').sum()),
            "real_predictions": int((df['prediction'] == 'REAL').sum()),
            "avg_prob_fake_cases": float(avg_prob_fake),
            "avg_prob_real_cases": float(avg_prob_real),
            "avg_prob_neutral_cases": float(avg_prob_neutral),
            "avg_prob_borderline_cases": float(avg_prob_borderline),
            "plot_path": f"s3://{bucket_name}/{plot_path}",
            "plot": MetadataValue.md(f"![Logistic Regression Inference](data:image/png;base64,{__import__('base64').b64encode(plot_buffer.getvalue()).decode()})")
        }
    )


@asset(
    description='Test SVM model with inference test cases',
    compute_kind='Python',
    required_resource_keys={'minio_resource'},
    group_name='ML_pipeline',
    ins={
        'train_svm': AssetIn('train_svm')
    }
)
def inference_svm(context: AssetExecutionContext, train_svm):
    """Load trained SVM model and test with sample cases."""
    
    context.log.info('Running inference with SVM model')
    
    # Use the trained model passed from training asset
    model = train_svm
    
    # Get MinIO client
    minio_client = context.resources.minio_resource
    
    # Prepare results
    results = []
    
    for i, (text, expected_type) in enumerate(TEST_CASES, 1):
        context.log.info(f"Case {i}: {text[:50]}...")
        
        # Predict
        pred, prob = predict_fake_news([text], model, minio_client)
        prediction = "REAL" if pred[0] == 1 else "FAKE"
        probability = float(prob[0])
        
        context.log.info(f"  Prediction: {prediction}, Probability (real): {probability:.4f}")
        
        results.append({
            "case": i,
            "text": text,
            "expected_type": expected_type,
            "prediction": prediction,
            "predicted_label": int(pred[0]),
            "probability_real": probability,
            "probability_fake": 1 - probability
        })
    
    # Create results DataFrame
    df = pd.DataFrame(results)
    
    # Create visualization
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle('SVM Inference Results', fontsize=16, fontweight='bold')
    
    # 1. Probability distribution
    x_pos = range(len(df))
    colors = ['#FF5252' if p == 'FAKE' else '#4CAF50' for p in df['prediction']]
    
    bars = axes[0].bar(x_pos, df['probability_real'], color=colors, alpha=0.7, edgecolor='black')
    axes[0].axhline(y=0.5, color='gray', linestyle='--', linewidth=2, label='Threshold (0.5)')
    axes[0].set_xlabel('Test Case')
    axes[0].set_ylabel('Probability (Real)')
    axes[0].set_title('Probability Distribution Across Test Cases')
    axes[0].set_xticks(x_pos)
    axes[0].set_xticklabels([f"Case {i}" for i in df['case']], rotation=45)
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar, prob in zip(bars, df['probability_real']):
        height = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2., height,
                    f'{prob:.3f}', ha='center', va='bottom', fontsize=9)
    
    # 2. Prediction summary by expected type
    type_counts = df.groupby(['expected_type', 'prediction']).size().unstack(fill_value=0)
    type_counts.plot(kind='bar', ax=axes[1], color=['#FF5252', '#4CAF50'], alpha=0.7, edgecolor='black')
    axes[1].set_xlabel('Expected Type')
    axes[1].set_ylabel('Count')
    axes[1].set_title('Prediction Distribution by Expected Type')
    axes[1].legend(title='Prediction', labels=['FAKE', 'REAL'])
    axes[1].set_xticklabels(axes[1].get_xticklabels(), rotation=45)
    axes[1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot to buffer and MinIO
    minio_client = context.resources.minio_resource
    bucket_name = "models"
    
    plot_buffer = BytesIO()
    plt.savefig(plot_buffer, format='png', dpi=150, bbox_inches='tight')
    plot_buffer.seek(0)
    
    # Save to MinIO
    plot_path = "plots/inference_svm.png"
    minio_client.put_object(
        bucket_name,
        plot_path,
        plot_buffer,
        length=plot_buffer.getbuffer().nbytes,
        content_type="image/png"
    )
    context.log.info(f"Saved plot to s3://{bucket_name}/{plot_path}")
    
    plot_buffer.seek(0)
    plt.close()
    
    # Calculate summary statistics
    avg_prob_fake = df[df['expected_type'] == 'fake']['probability_real'].mean()
    avg_prob_real = df[df['expected_type'] == 'real']['probability_real'].mean()
    avg_prob_neutral = df[df['expected_type'] == 'neutral']['probability_real'].mean()
    avg_prob_borderline = df[df['expected_type'] == 'borderline']['probability_real'].mean()
    
    context.log.info(f"Average probability (real) for expected FAKE news: {avg_prob_fake:.4f}")
    context.log.info(f"Average probability (real) for expected REAL news: {avg_prob_real:.4f}")
    context.log.info(f"Average probability (real) for NEUTRAL news: {avg_prob_neutral:.4f}")
    context.log.info(f"Average probability (real) for BORDERLINE news: {avg_prob_borderline:.4f}")
    
    return Output(
        value=df.to_dict('records'),
        metadata={
            "model_type": "SVM",
            "total_cases": len(df),
            "fake_predictions": int((df['prediction'] == 'FAKE').sum()),
            "real_predictions": int((df['prediction'] == 'REAL').sum()),
            "avg_prob_fake_cases": float(avg_prob_fake),
            "avg_prob_real_cases": float(avg_prob_real),
            "avg_prob_neutral_cases": float(avg_prob_neutral),
            "avg_prob_borderline_cases": float(avg_prob_borderline),
            "plot_path": f"s3://{bucket_name}/{plot_path}",
            "plot": MetadataValue.md(f"![SVM Inference](data:image/png;base64,{__import__('base64').b64encode(plot_buffer.getvalue()).decode()})")
        }
    )


@asset(
    description='Test LightGBM model with inference test cases',
    compute_kind='Python',
    required_resource_keys={'minio_resource'},
    group_name='ML_pipeline',
    ins={
        'train_lightgbm': AssetIn('train_lightgbm')
    }
)
def inference_lightgbm(context: AssetExecutionContext, train_lightgbm):
    """Load trained LightGBM model and test with sample cases."""
    
    context.log.info('Running inference with LightGBM model')
    
    # Use the trained model passed from training asset
    model = train_lightgbm
    
    # Get MinIO client
    minio_client = context.resources.minio_resource
    
    # Prepare results
    results = []
    
    for i, (text, expected_type) in enumerate(TEST_CASES, 1):
        context.log.info(f"Case {i}: {text[:50]}...")
        
        # Predict
        pred, prob = predict_fake_news([text], model, minio_client)
        prediction = "REAL" if pred[0] == 1 else "FAKE"
        probability = float(prob[0])
        
        context.log.info(f"  Prediction: {prediction}, Probability (real): {probability:.4f}")
        
        results.append({
            "case": i,
            "text": text,
            "expected_type": expected_type,
            "prediction": prediction,
            "predicted_label": int(pred[0]),
            "probability_real": probability,
            "probability_fake": 1 - probability
        })
    
    # Create results DataFrame
    df = pd.DataFrame(results)
    
    # Create visualization
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle('LightGBM Inference Results', fontsize=16, fontweight='bold')
    
    # 1. Probability distribution
    x_pos = range(len(df))
    colors = ['#FF5252' if p == 'FAKE' else '#4CAF50' for p in df['prediction']]
    
    bars = axes[0].bar(x_pos, df['probability_real'], color=colors, alpha=0.7, edgecolor='black')
    axes[0].axhline(y=0.5, color='gray', linestyle='--', linewidth=2, label='Threshold (0.5)')
    axes[0].set_xlabel('Test Case')
    axes[0].set_ylabel('Probability (Real)')
    axes[0].set_title('Probability Distribution Across Test Cases')
    axes[0].set_xticks(x_pos)
    axes[0].set_xticklabels([f"Case {i}" for i in df['case']], rotation=45)
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar, prob in zip(bars, df['probability_real']):
        height = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2., height,
                    f'{prob:.3f}', ha='center', va='bottom', fontsize=9)
    
    # 2. Prediction summary by expected type
    type_counts = df.groupby(['expected_type', 'prediction']).size().unstack(fill_value=0)
    type_counts.plot(kind='bar', ax=axes[1], color=['#FF5252', '#4CAF50'], alpha=0.7, edgecolor='black')
    axes[1].set_xlabel('Expected Type')
    axes[1].set_ylabel('Count')
    axes[1].set_title('Prediction Distribution by Expected Type')
    axes[1].legend(title='Prediction', labels=['FAKE', 'REAL'])
    axes[1].set_xticklabels(axes[1].get_xticklabels(), rotation=45)
    axes[1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot to buffer and MinIO
    minio_client = context.resources.minio_resource
    bucket_name = "models"
    
    plot_buffer = BytesIO()
    plt.savefig(plot_buffer, format='png', dpi=150, bbox_inches='tight')
    plot_buffer.seek(0)
    
    # Save to MinIO
    plot_path = "plots/inference_lightgbm.png"
    minio_client.put_object(
        bucket_name,
        plot_path,
        plot_buffer,
        length=plot_buffer.getbuffer().nbytes,
        content_type="image/png"
    )
    context.log.info(f"Saved plot to s3://{bucket_name}/{plot_path}")
    
    plot_buffer.seek(0)
    plt.close()
    
    # Calculate summary statistics
    avg_prob_fake = df[df['expected_type'] == 'fake']['probability_real'].mean()
    avg_prob_real = df[df['expected_type'] == 'real']['probability_real'].mean()
    avg_prob_neutral = df[df['expected_type'] == 'neutral']['probability_real'].mean()
    avg_prob_borderline = df[df['expected_type'] == 'borderline']['probability_real'].mean()
    
    context.log.info(f"Average probability (real) for expected FAKE news: {avg_prob_fake:.4f}")
    context.log.info(f"Average probability (real) for expected REAL news: {avg_prob_real:.4f}")
    context.log.info(f"Average probability (real) for NEUTRAL news: {avg_prob_neutral:.4f}")
    context.log.info(f"Average probability (real) for BORDERLINE news: {avg_prob_borderline:.4f}")
    
    return Output(
        value=df.to_dict('records'),
        metadata={
            "model_type": "LightGBM",
            "total_cases": len(df),
            "fake_predictions": int((df['prediction'] == 'FAKE').sum()),
            "real_predictions": int((df['prediction'] == 'REAL').sum()),
            "avg_prob_fake_cases": float(avg_prob_fake),
            "avg_prob_real_cases": float(avg_prob_real),
            "avg_prob_neutral_cases": float(avg_prob_neutral),
            "avg_prob_borderline_cases": float(avg_prob_borderline),
            "plot_path": f"s3://{bucket_name}/{plot_path}",
            "plot": MetadataValue.md(f"![LightGBM Inference](data:image/png;base64,{__import__('base64').b64encode(plot_buffer.getvalue()).decode()})")
        }
    )


@asset(
    description='Test Stacking Ensemble model with inference test cases',
    compute_kind='Python',
    required_resource_keys={'minio_resource'},
    group_name='ML_pipeline',
    ins={
        'train_stacking_ensemble': AssetIn('train_stacking_ensemble')
    }
)
def inference_stacking_ensemble(context: AssetExecutionContext, train_stacking_ensemble):
    """Load trained Stacking Ensemble model and test with sample cases."""
    
    context.log.info('Running inference with Stacking Ensemble model')
    
    # Use the trained model passed from training asset
    model = train_stacking_ensemble
    
    # Get MinIO client
    minio_client = context.resources.minio_resource
    
    # Prepare results
    results = []
    
    for i, (text, expected_type) in enumerate(TEST_CASES, 1):
        context.log.info(f"Case {i}: {text[:50]}...")
        
        # Predict
        pred, prob = predict_fake_news([text], model, minio_client)
        prediction = "REAL" if pred[0] == 1 else "FAKE"
        probability = float(prob[0])
        
        context.log.info(f"  Prediction: {prediction}, Probability (real): {probability:.4f}")
        
        results.append({
            "case": i,
            "text": text,
            "expected_type": expected_type,
            "prediction": prediction,
            "predicted_label": int(pred[0]),
            "probability_real": probability,
            "probability_fake": 1 - probability
        })
    
    # Create results DataFrame
    df = pd.DataFrame(results)
    
    # Create visualization
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle('Stacking Ensemble Inference Results', fontsize=16, fontweight='bold')
    
    # 1. Probability distribution
    x_pos = range(len(df))
    colors = ['#FF5252' if p == 'FAKE' else '#4CAF50' for p in df['prediction']]
    
    bars = axes[0].bar(x_pos, df['probability_real'], color=colors, alpha=0.7, edgecolor='black')
    axes[0].axhline(y=0.5, color='gray', linestyle='--', linewidth=2, label='Threshold (0.5)')
    axes[0].set_xlabel('Test Case')
    axes[0].set_ylabel('Probability (Real)')
    axes[0].set_title('Probability Distribution Across Test Cases')
    axes[0].set_xticks(x_pos)
    axes[0].set_xticklabels([f"Case {i}" for i in df['case']], rotation=45)
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar, prob in zip(bars, df['probability_real']):
        height = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2., height,
                    f'{prob:.3f}', ha='center', va='bottom', fontsize=9)
    
    # 2. Prediction summary by expected type
    type_counts = df.groupby(['expected_type', 'prediction']).size().unstack(fill_value=0)
    type_counts.plot(kind='bar', ax=axes[1], color=['#FF5252', '#4CAF50'], alpha=0.7, edgecolor='black')
    axes[1].set_xlabel('Expected Type')
    axes[1].set_ylabel('Count')
    axes[1].set_title('Prediction Distribution by Expected Type')
    axes[1].legend(title='Prediction', labels=['FAKE', 'REAL'])
    axes[1].set_xticklabels(axes[1].get_xticklabels(), rotation=45)
    axes[1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot to buffer and MinIO
    minio_client = context.resources.minio_resource
    bucket_name = "models"
    
    plot_buffer = BytesIO()
    plt.savefig(plot_buffer, format='png', dpi=150, bbox_inches='tight')
    plot_buffer.seek(0)
    
    # Save to MinIO
    plot_path = "plots/inference_stacking_ensemble.png"
    minio_client.put_object(
        bucket_name,
        plot_path,
        plot_buffer,
        length=plot_buffer.getbuffer().nbytes,
        content_type="image/png"
    )
    context.log.info(f"Saved plot to s3://{bucket_name}/{plot_path}")
    
    plot_buffer.seek(0)
    plt.close()
    
    # Calculate summary statistics
    avg_prob_fake = df[df['expected_type'] == 'fake']['probability_real'].mean()
    avg_prob_real = df[df['expected_type'] == 'real']['probability_real'].mean()
    avg_prob_neutral = df[df['expected_type'] == 'neutral']['probability_real'].mean()
    avg_prob_borderline = df[df['expected_type'] == 'borderline']['probability_real'].mean()
    
    context.log.info(f"Average probability (real) for expected FAKE news: {avg_prob_fake:.4f}")
    context.log.info(f"Average probability (real) for expected REAL news: {avg_prob_real:.4f}")
    context.log.info(f"Average probability (real) for NEUTRAL news: {avg_prob_neutral:.4f}")
    context.log.info(f"Average probability (real) for BORDERLINE news: {avg_prob_borderline:.4f}")
    
    return Output(
        value=df.to_dict('records'),
        metadata={
            "model_type": "StackingEnsemble",
            "total_cases": len(df),
            "fake_predictions": int((df['prediction'] == 'FAKE').sum()),
            "real_predictions": int((df['prediction'] == 'REAL').sum()),
            "avg_prob_fake_cases": float(avg_prob_fake),
            "avg_prob_real_cases": float(avg_prob_real),
            "avg_prob_neutral_cases": float(avg_prob_neutral),
            "avg_prob_borderline_cases": float(avg_prob_borderline),
            "plot_path": f"s3://{bucket_name}/{plot_path}",
            "plot": MetadataValue.md(f"![Stacking Ensemble Inference](data:image/png;base64,{__import__('base64').b64encode(plot_buffer.getvalue()).decode()})")
        }
    )


@asset(
    description='Compare all models inference results',
    compute_kind='Python',
    group_name='ML_pipeline',
    required_resource_keys={'minio_resource'},
    ins={
        'inference_logistic_regression': AssetIn('inference_logistic_regression'),
        'inference_svm': AssetIn('inference_svm'),
        'inference_lightgbm': AssetIn('inference_lightgbm'),
        'inference_stacking_ensemble': AssetIn('inference_stacking_ensemble')
    }
)
def compare_model_inference(context: AssetExecutionContext,
                           inference_logistic_regression,
                           inference_svm,
                           inference_lightgbm,
                           inference_stacking_ensemble):
    """Compare inference results across all models."""
    
    context.log.info('Comparing inference results across all models')
    
    # Convert to DataFrames
    df_lr = pd.DataFrame(inference_logistic_regression)
    df_svm = pd.DataFrame(inference_svm)
    df_lgb = pd.DataFrame(inference_lightgbm)
    df_stack = pd.DataFrame(inference_stacking_ensemble)
    
    # Create comparison visualization
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Model Inference Comparison', fontsize=18, fontweight='bold')
    
    # 1. Probability comparison for each test case
    x_pos = range(len(df_lr))
    width = 0.2
    
    axes[0, 0].bar([x - 1.5*width for x in x_pos], df_lr['probability_real'], width, 
                   label='LogReg', alpha=0.8, color='#2196F3')
    axes[0, 0].bar([x - 0.5*width for x in x_pos], df_svm['probability_real'], width,
                   label='SVM', alpha=0.8, color='#4CAF50')
    axes[0, 0].bar([x + 0.5*width for x in x_pos], df_lgb['probability_real'], width,
                   label='LightGBM', alpha=0.8, color='#9C27B0')
    axes[0, 0].bar([x + 1.5*width for x in x_pos], df_stack['probability_real'], width,
                   label='Stacking', alpha=0.8, color='#FF5722')
    
    axes[0, 0].axhline(y=0.5, color='gray', linestyle='--', linewidth=2)
    axes[0, 0].set_xlabel('Test Case')
    axes[0, 0].set_ylabel('Probability (Real)')
    axes[0, 0].set_title('Probability Comparison Across Models')
    axes[0, 0].set_xticks(x_pos)
    axes[0, 0].set_xticklabels([f"C{i}" for i in df_lr['case']], rotation=0)
    axes[0, 0].legend()
    axes[0, 0].grid(axis='y', alpha=0.3)
    
    # 2. Agreement rate heatmap
    agreement_matrix = []
    models = ['LogReg', 'SVM', 'LightGBM', 'Stacking']
    dfs = [df_lr, df_svm, df_lgb, df_stack]
    
    for i, df1 in enumerate(dfs):
        row = []
        for j, df2 in enumerate(dfs):
            agreement = (df1['predicted_label'] == df2['predicted_label']).sum() / len(df1) * 100
            row.append(agreement)
        agreement_matrix.append(row)
    
    sns.heatmap(agreement_matrix, annot=True, fmt='.1f', cmap='RdYlGn', 
                xticklabels=models, yticklabels=models, ax=axes[0, 1],
                vmin=0, vmax=100, cbar_kws={'label': 'Agreement %'})
    axes[0, 1].set_title('Model Agreement Rate (%)')
    
    # 3. Average probability by expected type
    types = ['fake', 'real', 'neutral', 'borderline']
    lr_avgs = [df_lr[df_lr['expected_type'] == t]['probability_real'].mean() for t in types]
    svm_avgs = [df_svm[df_svm['expected_type'] == t]['probability_real'].mean() for t in types]
    lgb_avgs = [df_lgb[df_lgb['expected_type'] == t]['probability_real'].mean() for t in types]
    stack_avgs = [df_stack[df_stack['expected_type'] == t]['probability_real'].mean() for t in types]
    
    x_pos_types = range(len(types))
    width = 0.2
    
    axes[1, 0].bar([x - 1.5*width for x in x_pos_types], lr_avgs, width,
                   label='LogReg', alpha=0.8, color='#2196F3')
    axes[1, 0].bar([x - 0.5*width for x in x_pos_types], svm_avgs, width,
                   label='SVM', alpha=0.8, color='#4CAF50')
    axes[1, 0].bar([x + 0.5*width for x in x_pos_types], lgb_avgs, width,
                   label='LightGBM', alpha=0.8, color='#9C27B0')
    axes[1, 0].bar([x + 1.5*width for x in x_pos_types], stack_avgs, width,
                   label='Stacking', alpha=0.8, color='#FF5722')
    
    axes[1, 0].axhline(y=0.5, color='gray', linestyle='--', linewidth=2)
    axes[1, 0].set_xlabel('Expected Type')
    axes[1, 0].set_ylabel('Average Probability (Real)')
    axes[1, 0].set_title('Average Probability by Expected Type')
    axes[1, 0].set_xticks(x_pos_types)
    axes[1, 0].set_xticklabels(types, rotation=45)
    axes[1, 0].legend()
    axes[1, 0].grid(axis='y', alpha=0.3)
    
    # 4. Prediction distribution
    pred_counts = {
        'LogReg FAKE': (df_lr['prediction'] == 'FAKE').sum(),
        'LogReg REAL': (df_lr['prediction'] == 'REAL').sum(),
        'SVM FAKE': (df_svm['prediction'] == 'FAKE').sum(),
        'SVM REAL': (df_svm['prediction'] == 'REAL').sum(),
        'LightGBM FAKE': (df_lgb['prediction'] == 'FAKE').sum(),
        'LightGBM REAL': (df_lgb['prediction'] == 'REAL').sum(),
        'Stacking FAKE': (df_stack['prediction'] == 'FAKE').sum(),
        'Stacking REAL': (df_stack['prediction'] == 'REAL').sum()
    }
    
    colors_pred = ['#FF5252', '#4CAF50'] * 4
    axes[1, 1].bar(range(len(pred_counts)), list(pred_counts.values()), 
                   color=colors_pred, alpha=0.7, edgecolor='black')
    axes[1, 1].set_xlabel('Model - Prediction')
    axes[1, 1].set_ylabel('Count')
    axes[1, 1].set_title('Prediction Distribution by Model')
    axes[1, 1].set_xticks(range(len(pred_counts)))
    axes[1, 1].set_xticklabels(list(pred_counts.keys()), rotation=45, ha='right')
    axes[1, 1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot to buffer
    plot_buffer = BytesIO()
    plt.savefig(plot_buffer, format='png', dpi=150, bbox_inches='tight')
    plot_buffer.seek(0)
    
    # Save plot to MinIO
    minio_client = context.resources.minio_resource
    bucket_name = "models"
    plot_path = "plots/model_agreement_analysis.png"
    minio_client.put_object(
        bucket_name,
        plot_path,
        plot_buffer,
        length=plot_buffer.getbuffer().nbytes,
        content_type="image/png"
    )
    context.log.info(f"Saved plot to s3://{bucket_name}/{plot_path}")
    
    plot_buffer.seek(0)  # Reset buffer for metadata
    plt.close()
    
    # Calculate full agreement rate
    total_agreement = (
        (df_lr['predicted_label'] == df_svm['predicted_label']) &
        (df_lr['predicted_label'] == df_lgb['predicted_label']) &
        (df_lr['predicted_label'] == df_stack['predicted_label'])
    ).sum()
    
    context.log.info(f"Cases where all models agree: {total_agreement}/{len(df_lr)}")
    
    return Output(
        value={
            "agreement_matrix": agreement_matrix,
            "models": models,
            "total_agreement": int(total_agreement),
            "total_cases": len(df_lr)
        },
        metadata={
            "total_cases": len(df_lr),
            "full_agreement": int(total_agreement),
            "full_agreement_rate": float(total_agreement / len(df_lr) * 100),
            "plot_path": f"s3://{bucket_name}/{plot_path}",
            "plot": MetadataValue.md(f"![Model Agreement Analysis](data:image/png;base64,{__import__('base64').b64encode(plot_buffer.getvalue()).decode()})")
        }
    )
