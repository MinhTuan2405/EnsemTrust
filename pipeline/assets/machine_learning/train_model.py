from dagster import asset, AssetExecutionContext, AssetIn, Output
from pipeline.utils.models import (
    SVM_model, 
    logisticRegression_model, 
    LightGBM_model, 
    evaluate_model, 
    stacking_ensemble_model
)
import pickle
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, roc_curve, auc
import numpy as np


@asset(
    description='Train Logistic Regression model',
    compute_kind='Python',
    required_resource_keys={'minio_resource'},
    group_name='ML_pipeline',
    ins={
        'combine_features': AssetIn('combine_features')
    }
)
def train_logistic_regression(context: AssetExecutionContext, combine_features):
    """Train and evaluate Logistic Regression model."""
    
    # Extract features and labels
    X_train = combine_features['train']['X']
    y_train = combine_features['train']['y']
    X_val = combine_features['validation']['X']
    y_val = combine_features['validation']['y']
    X_test = combine_features['test']['X']
    y_test = combine_features['test']['y']
    
    context.log.info('Training Logistic Regression model...')
    
    # Create and train model
    model = logisticRegression_model()
    model.fit(X_train, y_train)
    
    context.log.info('Model training completed')
    
    # Evaluate on all sets
    train_metrics = evaluate_model(model, X_train, y_train, "Train")
    val_metrics = evaluate_model(model, X_val, y_val, "Validation")
    test_metrics = evaluate_model(model, X_test, y_test, "Test")
    
    context.log.info(f"Train - Accuracy: {train_metrics['accuracy']:.4f}, AUC: {train_metrics['auc']:.4f}")
    context.log.info(f"Val - Accuracy: {val_metrics['accuracy']:.4f}, AUC: {val_metrics['auc']:.4f}")
    context.log.info(f"Test - Accuracy: {test_metrics['accuracy']:.4f}, AUC: {test_metrics['auc']:.4f}")
    
    # Save model to MinIO
    minio_client = context.resources.minio_resource
    bucket_name = "models"
    
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
    
    model_buffer = BytesIO()
    pickle.dump(model, model_buffer)
    model_buffer.seek(0)
    
    model_path = "model/logistic_regression.pkl"
    minio_client.put_object(
        bucket_name,
        model_path,
        model_buffer,
        length=model_buffer.getbuffer().nbytes,
        content_type="application/octet-stream"
    )
    context.log.info(f"Saved model to s3://{bucket_name}/{model_path}")
    
    # Create visualization plots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Logistic Regression Model Performance', fontsize=16, fontweight='bold')
    
    # 1. Confusion Matrix
    y_pred_test = model.predict(X_test)
    cm = confusion_matrix(y_test, y_pred_test)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[0, 0])
    axes[0, 0].set_title('Confusion Matrix (Test Set)')
    axes[0, 0].set_ylabel('True Label')
    axes[0, 0].set_xlabel('Predicted Label')
    
    # 2. ROC Curve
    y_prob_test = model.predict_proba(X_test)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, y_prob_test)
    roc_auc = auc(fpr, tpr)
    axes[0, 1].plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.4f})')
    axes[0, 1].plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    axes[0, 1].set_xlim([0.0, 1.0])
    axes[0, 1].set_ylim([0.0, 1.05])
    axes[0, 1].set_xlabel('False Positive Rate')
    axes[0, 1].set_ylabel('True Positive Rate')
    axes[0, 1].set_title('ROC Curve (Test Set)')
    axes[0, 1].legend(loc="lower right")
    axes[0, 1].grid(alpha=0.3)
    
    # 3. Accuracy Comparison
    accuracies = [train_metrics['accuracy'], val_metrics['accuracy'], test_metrics['accuracy']]
    sets = ['Train', 'Validation', 'Test']
    bars = axes[1, 0].bar(sets, accuracies, color=['#4CAF50', '#2196F3', '#FF9800'])
    axes[1, 0].set_ylim([0, 1])
    axes[1, 0].set_ylabel('Accuracy')
    axes[1, 0].set_title('Accuracy Across Sets')
    axes[1, 0].grid(axis='y', alpha=0.3)
    for bar, acc in zip(bars, accuracies):
        height = bar.get_height()
        axes[1, 0].text(bar.get_x() + bar.get_width()/2., height,
                       f'{acc:.4f}', ha='center', va='bottom')
    
    # 4. AUC Comparison
    aucs = [train_metrics['auc'], val_metrics['auc'], test_metrics['auc']]
    bars = axes[1, 1].bar(sets, aucs, color=['#4CAF50', '#2196F3', '#FF9800'])
    axes[1, 1].set_ylim([0, 1])
    axes[1, 1].set_ylabel('AUC')
    axes[1, 1].set_title('AUC Across Sets')
    axes[1, 1].grid(axis='y', alpha=0.3)
    for bar, auc_val in zip(bars, aucs):
        height = bar.get_height()
        axes[1, 1].text(bar.get_x() + bar.get_width()/2., height,
                       f'{auc_val:.4f}', ha='center', va='bottom')
    
    plt.tight_layout()
    
    # Save plot to MinIO
    plot_buffer = BytesIO()
    plt.savefig(plot_buffer, format='png', dpi=150, bbox_inches='tight')
    plot_buffer.seek(0)
    plt.close()
    
    plot_path = "plots/logistic_regression_performance.png"
    minio_client.put_object(
        bucket_name,
        plot_path,
        plot_buffer,
        length=plot_buffer.getbuffer().nbytes,
        content_type="image/png"
    )
    context.log.info(f"Saved plot to s3://{bucket_name}/{plot_path}")
    
    return Output(
        value=model,
        metadata={
            "model_type": "LogisticRegression",
            "model_path": f"s3://{bucket_name}/{model_path}",
            "plot_path": f"s3://{bucket_name}/{plot_path}",
            "train_accuracy": float(train_metrics['accuracy']),
            "train_auc": float(train_metrics['auc']),
            "val_accuracy": float(val_metrics['accuracy']),
            "val_auc": float(val_metrics['auc']),
            "test_accuracy": float(test_metrics['accuracy']),
            "test_auc": float(test_metrics['auc']),
            "train_report": train_metrics['classification_report'],
            "val_report": val_metrics['classification_report'],
            "test_report": test_metrics['classification_report']
        }
    )


@asset(
    description='Train SVM model',
    compute_kind='Python',
    required_resource_keys={'minio_resource'},
    group_name='ML_pipeline',
    ins={
        'combine_features': AssetIn('combine_features')
    }
)
def train_svm(context: AssetExecutionContext, combine_features):
    """Train and evaluate SVM model."""
    
    # Extract features and labels
    X_train = combine_features['train']['X']
    y_train = combine_features['train']['y']
    X_val = combine_features['validation']['X']
    y_val = combine_features['validation']['y']
    X_test = combine_features['test']['X']
    y_test = combine_features['test']['y']
    
    context.log.info('Training SVM model...')
    
    # Create and train model
    model = SVM_model()
    model.fit(X_train, y_train)
    
    context.log.info('Model training completed')
    
    # Evaluate on all sets
    train_metrics = evaluate_model(model, X_train, y_train, "Train")
    val_metrics = evaluate_model(model, X_val, y_val, "Validation")
    test_metrics = evaluate_model(model, X_test, y_test, "Test")
    
    context.log.info(f"Train - Accuracy: {train_metrics['accuracy']:.4f}, AUC: {train_metrics['auc']:.4f}")
    context.log.info(f"Val - Accuracy: {val_metrics['accuracy']:.4f}, AUC: {val_metrics['auc']:.4f}")
    context.log.info(f"Test - Accuracy: {test_metrics['accuracy']:.4f}, AUC: {test_metrics['auc']:.4f}")
    
    # Save model to MinIO
    minio_client = context.resources.minio_resource
    bucket_name = "models"
    
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
    
    model_buffer = BytesIO()
    pickle.dump(model, model_buffer)
    model_buffer.seek(0)
    
    model_path = "model/svm.pkl"
    minio_client.put_object(
        bucket_name,
        model_path,
        model_buffer,
        length=model_buffer.getbuffer().nbytes,
        content_type="application/octet-stream"
    )
    context.log.info(f"Saved model to s3://{bucket_name}/{model_path}")
    
    # Create visualization plots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('SVM Model Performance', fontsize=16, fontweight='bold')
    
    # 1. Confusion Matrix
    y_pred_test = model.predict(X_test)
    cm = confusion_matrix(y_test, y_pred_test)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Greens', ax=axes[0, 0])
    axes[0, 0].set_title('Confusion Matrix (Test Set)')
    axes[0, 0].set_ylabel('True Label')
    axes[0, 0].set_xlabel('Predicted Label')
    
    # 2. ROC Curve
    y_prob_test = model.predict_proba(X_test)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, y_prob_test)
    roc_auc = auc(fpr, tpr)
    axes[0, 1].plot(fpr, tpr, color='green', lw=2, label=f'ROC curve (AUC = {roc_auc:.4f})')
    axes[0, 1].plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    axes[0, 1].set_xlim([0.0, 1.0])
    axes[0, 1].set_ylim([0.0, 1.05])
    axes[0, 1].set_xlabel('False Positive Rate')
    axes[0, 1].set_ylabel('True Positive Rate')
    axes[0, 1].set_title('ROC Curve (Test Set)')
    axes[0, 1].legend(loc="lower right")
    axes[0, 1].grid(alpha=0.3)
    
    # 3. Accuracy Comparison
    accuracies = [train_metrics['accuracy'], val_metrics['accuracy'], test_metrics['accuracy']]
    sets = ['Train', 'Validation', 'Test']
    bars = axes[1, 0].bar(sets, accuracies, color=['#4CAF50', '#2196F3', '#FF9800'])
    axes[1, 0].set_ylim([0, 1])
    axes[1, 0].set_ylabel('Accuracy')
    axes[1, 0].set_title('Accuracy Across Sets')
    axes[1, 0].grid(axis='y', alpha=0.3)
    for bar, acc in zip(bars, accuracies):
        height = bar.get_height()
        axes[1, 0].text(bar.get_x() + bar.get_width()/2., height,
                       f'{acc:.4f}', ha='center', va='bottom')
    
    # 4. AUC Comparison
    aucs = [train_metrics['auc'], val_metrics['auc'], test_metrics['auc']]
    bars = axes[1, 1].bar(sets, aucs, color=['#4CAF50', '#2196F3', '#FF9800'])
    axes[1, 1].set_ylim([0, 1])
    axes[1, 1].set_ylabel('AUC')
    axes[1, 1].set_title('AUC Across Sets')
    axes[1, 1].grid(axis='y', alpha=0.3)
    for bar, auc_val in zip(bars, aucs):
        height = bar.get_height()
        axes[1, 1].text(bar.get_x() + bar.get_width()/2., height,
                       f'{auc_val:.4f}', ha='center', va='bottom')
    
    plt.tight_layout()
    
    # Save plot to MinIO
    plot_buffer = BytesIO()
    plt.savefig(plot_buffer, format='png', dpi=150, bbox_inches='tight')
    plot_buffer.seek(0)
    plt.close()
    
    plot_path = "plots/svm_performance.png"
    minio_client.put_object(
        bucket_name,
        plot_path,
        plot_buffer,
        length=plot_buffer.getbuffer().nbytes,
        content_type="image/png"
    )
    context.log.info(f"Saved plot to s3://{bucket_name}/{plot_path}")
    
    return Output(
        value=model,
        metadata={
            "model_type": "SVM",
            "model_path": f"s3://{bucket_name}/{model_path}",
            "plot_path": f"s3://{bucket_name}/{plot_path}",
            "train_accuracy": float(train_metrics['accuracy']),
            "train_auc": float(train_metrics['auc']),
            "val_accuracy": float(val_metrics['accuracy']),
            "val_auc": float(val_metrics['auc']),
            "test_accuracy": float(test_metrics['accuracy']),
            "test_auc": float(test_metrics['auc']),
            "train_report": train_metrics['classification_report'],
            "val_report": val_metrics['classification_report'],
            "test_report": test_metrics['classification_report']
        }
    )


@asset(
    description='Train LightGBM model',
    compute_kind='Python',
    required_resource_keys={'minio_resource'},
    group_name='ML_pipeline',
    ins={
        'combine_features': AssetIn('combine_features')
    }
)
def train_lightgbm(context: AssetExecutionContext, combine_features):
    """Train and evaluate LightGBM model."""
    
    # Extract features and labels
    X_train = combine_features['train']['X']
    y_train = combine_features['train']['y']
    X_val = combine_features['validation']['X']
    y_val = combine_features['validation']['y']
    X_test = combine_features['test']['X']
    y_test = combine_features['test']['y']
    
    context.log.info('Training LightGBM model...')
    
    # Create and train model
    model = LightGBM_model()
    model.fit(X_train, y_train)
    
    context.log.info('Model training completed')
    
    # Evaluate on all sets
    train_metrics = evaluate_model(model, X_train, y_train, "Train")
    val_metrics = evaluate_model(model, X_val, y_val, "Validation")
    test_metrics = evaluate_model(model, X_test, y_test, "Test")
    
    context.log.info(f"Train - Accuracy: {train_metrics['accuracy']:.4f}, AUC: {train_metrics['auc']:.4f}")
    context.log.info(f"Val - Accuracy: {val_metrics['accuracy']:.4f}, AUC: {val_metrics['auc']:.4f}")
    context.log.info(f"Test - Accuracy: {test_metrics['accuracy']:.4f}, AUC: {test_metrics['auc']:.4f}")
    
    # Save model to MinIO
    minio_client = context.resources.minio_resource
    bucket_name = "models"
    
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
    
    model_buffer = BytesIO()
    pickle.dump(model, model_buffer)
    model_buffer.seek(0)
    
    model_path = "model/lightgbm.pkl"
    minio_client.put_object(
        bucket_name,
        model_path,
        model_buffer,
        length=model_buffer.getbuffer().nbytes,
        content_type="application/octet-stream"
    )
    context.log.info(f"Saved model to s3://{bucket_name}/{model_path}")
    
    # Create visualization plots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('LightGBM Model Performance', fontsize=16, fontweight='bold')
    
    # 1. Confusion Matrix
    y_pred_test = model.predict(X_test)
    cm = confusion_matrix(y_test, y_pred_test)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Purples', ax=axes[0, 0])
    axes[0, 0].set_title('Confusion Matrix (Test Set)')
    axes[0, 0].set_ylabel('True Label')
    axes[0, 0].set_xlabel('Predicted Label')
    
    # 2. ROC Curve
    y_prob_test = model.predict_proba(X_test)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, y_prob_test)
    roc_auc = auc(fpr, tpr)
    axes[0, 1].plot(fpr, tpr, color='purple', lw=2, label=f'ROC curve (AUC = {roc_auc:.4f})')
    axes[0, 1].plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    axes[0, 1].set_xlim([0.0, 1.0])
    axes[0, 1].set_ylim([0.0, 1.05])
    axes[0, 1].set_xlabel('False Positive Rate')
    axes[0, 1].set_ylabel('True Positive Rate')
    axes[0, 1].set_title('ROC Curve (Test Set)')
    axes[0, 1].legend(loc="lower right")
    axes[0, 1].grid(alpha=0.3)
    
    # 3. Accuracy Comparison
    accuracies = [train_metrics['accuracy'], val_metrics['accuracy'], test_metrics['accuracy']]
    sets = ['Train', 'Validation', 'Test']
    bars = axes[1, 0].bar(sets, accuracies, color=['#4CAF50', '#2196F3', '#FF9800'])
    axes[1, 0].set_ylim([0, 1])
    axes[1, 0].set_ylabel('Accuracy')
    axes[1, 0].set_title('Accuracy Across Sets')
    axes[1, 0].grid(axis='y', alpha=0.3)
    for bar, acc in zip(bars, accuracies):
        height = bar.get_height()
        axes[1, 0].text(bar.get_x() + bar.get_width()/2., height,
                       f'{acc:.4f}', ha='center', va='bottom')
    
    # 4. AUC Comparison
    aucs = [train_metrics['auc'], val_metrics['auc'], test_metrics['auc']]
    bars = axes[1, 1].bar(sets, aucs, color=['#4CAF50', '#2196F3', '#FF9800'])
    axes[1, 1].set_ylim([0, 1])
    axes[1, 1].set_ylabel('AUC')
    axes[1, 1].set_title('AUC Across Sets')
    axes[1, 1].grid(axis='y', alpha=0.3)
    for bar, auc_val in zip(bars, aucs):
        height = bar.get_height()
        axes[1, 1].text(bar.get_x() + bar.get_width()/2., height,
                       f'{auc_val:.4f}', ha='center', va='bottom')
    
    plt.tight_layout()
    
    # Save plot to MinIO
    plot_buffer = BytesIO()
    plt.savefig(plot_buffer, format='png', dpi=150, bbox_inches='tight')
    plot_buffer.seek(0)
    plt.close()
    
    plot_path = "plots/lightgbm_performance.png"
    minio_client.put_object(
        bucket_name,
        plot_path,
        plot_buffer,
        length=plot_buffer.getbuffer().nbytes,
        content_type="image/png"
    )
    context.log.info(f"Saved plot to s3://{bucket_name}/{plot_path}")
    
    return Output(
        value=model,
        metadata={
            "model_type": "LightGBM",
            "model_path": f"s3://{bucket_name}/{model_path}",
            "plot_path": f"s3://{bucket_name}/{plot_path}",
            "train_accuracy": float(train_metrics['accuracy']),
            "train_auc": float(train_metrics['auc']),
            "val_accuracy": float(val_metrics['accuracy']),
            "val_auc": float(val_metrics['auc']),
            "test_accuracy": float(test_metrics['accuracy']),
            "test_auc": float(test_metrics['auc']),
            "train_report": train_metrics['classification_report'],
            "val_report": val_metrics['classification_report'],
            "test_report": test_metrics['classification_report']
        }
    )


@asset(
    description='Train Stacking Ensemble model',
    compute_kind='Python',
    required_resource_keys={'minio_resource'},
    group_name='ML_pipeline',
    ins={
        'combine_features': AssetIn('combine_features'),
        'train_logistic_regression': AssetIn('train_logistic_regression'),
        'train_svm': AssetIn('train_svm'),
        'train_lightgbm': AssetIn('train_lightgbm')
    }
)
def train_stacking_ensemble(context: AssetExecutionContext, 
                           combine_features,
                           train_logistic_regression,
                           train_svm,
                           train_lightgbm):
    """Train and evaluate Stacking Ensemble model."""
    
    # Extract features and labels
    X_train = combine_features['train']['X']
    y_train = combine_features['train']['y']
    X_val = combine_features['validation']['X']
    y_val = combine_features['validation']['y']
    X_test = combine_features['test']['X']
    y_test = combine_features['test']['y']
    
    context.log.info('Training Stacking Ensemble model...')
    
    # Create estimators list from trained base models
    estimators = [
        ('logistic_regression', train_logistic_regression),
        ('svm', train_svm),
        ('lightgbm', train_lightgbm)
    ]
    
    # Create and train stacking model
    model = stacking_ensemble_model(estimators)
    model.fit(X_train, y_train)
    
    context.log.info('Model training completed')
    
    # Evaluate on all sets
    train_metrics = evaluate_model(model, X_train, y_train, "Train")
    val_metrics = evaluate_model(model, X_val, y_val, "Validation")
    test_metrics = evaluate_model(model, X_test, y_test, "Test")
    
    context.log.info(f"Train - Accuracy: {train_metrics['accuracy']:.4f}, AUC: {train_metrics['auc']:.4f}")
    context.log.info(f"Val - Accuracy: {val_metrics['accuracy']:.4f}, AUC: {val_metrics['auc']:.4f}")
    context.log.info(f"Test - Accuracy: {test_metrics['accuracy']:.4f}, AUC: {test_metrics['auc']:.4f}")
    
    # Save model to MinIO
    minio_client = context.resources.minio_resource
    bucket_name = "models"
    
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
    
    model_buffer = BytesIO()
    pickle.dump(model, model_buffer)
    model_buffer.seek(0)
    
    model_path = "model/stacking_ensemble.pkl"
    minio_client.put_object(
        bucket_name,
        model_path,
        model_buffer,
        length=model_buffer.getbuffer().nbytes,
        content_type="application/octet-stream"
    )
    context.log.info(f"Saved model to s3://{bucket_name}/{model_path}")
    
    # Also save as best_model.pkl for easy access
    best_model_path = "model/best_model.pkl"
    model_buffer.seek(0)
    minio_client.put_object(
        bucket_name,
        best_model_path,
        model_buffer,
        length=model_buffer.getbuffer().nbytes,
        content_type="application/octet-stream"
    )
    context.log.info(f"Saved as best model to s3://{bucket_name}/{best_model_path}")
    
    # Create visualization plots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Stacking Ensemble Model Performance', fontsize=16, fontweight='bold')
    
    # 1. Confusion Matrix
    y_pred_test = model.predict(X_test)
    cm = confusion_matrix(y_test, y_pred_test)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Reds', ax=axes[0, 0])
    axes[0, 0].set_title('Confusion Matrix (Test Set)')
    axes[0, 0].set_ylabel('True Label')
    axes[0, 0].set_xlabel('Predicted Label')
    
    # 2. ROC Curve
    y_prob_test = model.predict_proba(X_test)[:, 1]
    fpr, tpr, _ = roc_curve(y_test, y_prob_test)
    roc_auc = auc(fpr, tpr)
    axes[0, 1].plot(fpr, tpr, color='red', lw=2, label=f'ROC curve (AUC = {roc_auc:.4f})')
    axes[0, 1].plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    axes[0, 1].set_xlim([0.0, 1.0])
    axes[0, 1].set_ylim([0.0, 1.05])
    axes[0, 1].set_xlabel('False Positive Rate')
    axes[0, 1].set_ylabel('True Positive Rate')
    axes[0, 1].set_title('ROC Curve (Test Set)')
    axes[0, 1].legend(loc="lower right")
    axes[0, 1].grid(alpha=0.3)
    
    # 3. Accuracy Comparison
    accuracies = [train_metrics['accuracy'], val_metrics['accuracy'], test_metrics['accuracy']]
    sets = ['Train', 'Validation', 'Test']
    bars = axes[1, 0].bar(sets, accuracies, color=['#4CAF50', '#2196F3', '#FF9800'])
    axes[1, 0].set_ylim([0, 1])
    axes[1, 0].set_ylabel('Accuracy')
    axes[1, 0].set_title('Accuracy Across Sets')
    axes[1, 0].grid(axis='y', alpha=0.3)
    for bar, acc in zip(bars, accuracies):
        height = bar.get_height()
        axes[1, 0].text(bar.get_x() + bar.get_width()/2., height,
                       f'{acc:.4f}', ha='center', va='bottom')
    
    # 4. AUC Comparison
    aucs = [train_metrics['auc'], val_metrics['auc'], test_metrics['auc']]
    bars = axes[1, 1].bar(sets, aucs, color=['#4CAF50', '#2196F3', '#FF9800'])
    axes[1, 1].set_ylim([0, 1])
    axes[1, 1].set_ylabel('AUC')
    axes[1, 1].set_title('AUC Across Sets')
    axes[1, 1].grid(axis='y', alpha=0.3)
    for bar, auc_val in zip(bars, aucs):
        height = bar.get_height()
        axes[1, 1].text(bar.get_x() + bar.get_width()/2., height,
                       f'{auc_val:.4f}', ha='center', va='bottom')
    
    plt.tight_layout()
    
    # Save plot to MinIO
    plot_buffer = BytesIO()
    plt.savefig(plot_buffer, format='png', dpi=150, bbox_inches='tight')
    plot_buffer.seek(0)
    plt.close()
    
    plot_path = "plots/stacking_ensemble_performance.png"
    minio_client.put_object(
        bucket_name,
        plot_path,
        plot_buffer,
        length=plot_buffer.getbuffer().nbytes,
        content_type="image/png"
    )
    context.log.info(f"Saved plot to s3://{bucket_name}/{plot_path}")
    
    return Output(
        value=model,
        metadata={
            "model_type": "StackingEnsemble",
            "base_models": "LogisticRegression, SVM, LightGBM",
            "model_path": f"s3://{bucket_name}/{model_path}",
            "best_model_path": f"s3://{bucket_name}/{best_model_path}",
            "plot_path": f"s3://{bucket_name}/{plot_path}",
            "train_accuracy": float(train_metrics['accuracy']),
            "train_auc": float(train_metrics['auc']),
            "val_accuracy": float(val_metrics['accuracy']),
            "val_auc": float(val_metrics['auc']),
            "test_accuracy": float(test_metrics['accuracy']),
            "test_auc": float(test_metrics['auc']),
            "train_report": train_metrics['classification_report'],
            "val_report": val_metrics['classification_report'],
            "test_report": test_metrics['classification_report']
        }
    )