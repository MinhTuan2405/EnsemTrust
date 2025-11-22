"""
Machine learning models and utilities for fake news detection.

Provides factory functions for creating sklearn classifiers (SVM, LogReg, LightGBM),
stacking ensemble builder, model evaluation, and inference pipeline.
"""

import os
import pandas as pd
from dotenv import load_dotenv
import torch

from sklearn.metrics import classification_report, accuracy_score, roc_auc_score
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import StackingClassifier

from pipeline.utils.feature_engineer import (
    handcrafted_features,
    create_svd_transformer,
    create_tfidf_vectorizer,
    combine,
    encode_texts_st
)

try:
    from lightgbm import LGBMClassifier
except ImportError:  # optional dependency
    LGBMClassifier = None


load_dotenv()
RANDOM_STATE = int(os.getenv('RANDOM_STATE', 42))

# GPU detection
USE_GPU = torch.cuda.is_available()
DEVICE = "cuda" if USE_GPU else "cpu"



def evaluate_model(model, X, y, name="Dataset"):
    """Evaluate a binary classifier and return metrics dict.
    
    Args:
        model: Trained classifier with predict/predict_proba methods.
        X: Feature matrix (numpy array or pandas DataFrame).
        y: True labels (numpy array or pandas Series).
        name: Dataset name for logging.
    
    Returns:
        dict: Contains accuracy, AUC, and classification report string.
    """
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]
    
    return {
        "model name": name,
        "accuracy": float(accuracy_score(y, y_pred)),
        "auc": float(roc_auc_score(y, y_prob)),
        "classification_report": classification_report(y, y_pred)
    }


def SVM_model():
    """Return a binary Linear SVM classifier with probability outputs.
    
    Uses LinearSVC (optimized for linear kernel) wrapped with CalibratedClassifierCV
    for probability estimates. Much faster than SVC(kernel='linear').
    
    Returns:
        CalibratedClassifierCV: Linear SVM with probability calibration.
    """
    # Old approach (VERY SLOW - can take 3+ hours on large datasets):
    # from sklearn.svm import SVC
    # return SVC(kernel="linear", probability=True, random_state=RANDOM_STATE)
    
    # New approach: LinearSVC is much faster than SVC(kernel='linear') for large datasets
    # LinearSVC doesn't have probability output, so we wrap it with CalibratedClassifierCV
    base_svm = LinearSVC(
        dual="auto",  # Auto-select solver based on n_samples vs n_features
        max_iter=5000,
        random_state=RANDOM_STATE,
        class_weight='balanced'  # Handle imbalanced data
    )
    # Wrap with calibration to get probability estimates (uses 3-fold CV)
    return CalibratedClassifierCV(base_svm, cv=3)


def LightGBM_model():
    """Return a LightGBM classifier with reasonable defaults for binary classification.
    
    Automatically uses GPU if available (CUDA-enabled GPU detected).
    
    Returns:
        LGBMClassifier: Configured LightGBM binary classifier.
        
    Raises:
        ImportError: If lightgbm is not installed.
    """
    if LGBMClassifier is None:
        raise ImportError("lightgbm is not installed. Please add it to your dependencies.")

    params = {
        "n_estimators": 300,
        "learning_rate": 0.05,
        "max_depth": -1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "objective": "binary",
        "random_state": RANDOM_STATE,
        "n_jobs": -1,
    }
    
    # Enable GPU if available
    if USE_GPU:
        params["device"] = "gpu"
        params["gpu_use_dp"] = False  # Use single precision for speed
    
    return LGBMClassifier(**params)


def logisticRegression_model():
    """Return a regularized logistic regression classifier.
    
    Uses SAGA solver for L2 penalty with moderate regularization strength.
    
    Returns:
        LogisticRegression: Configured logistic regression classifier.
    """
    return LogisticRegression(
        max_iter=5000,
        solver="saga",
        penalty="l2",
        C=0.5,
        random_state=RANDOM_STATE
    )


def meta_model():
    """Return a logistic regression meta-learner for stacking ensemble.
    
    Uses LBFGS solver with increased max_iter for stability.
    
    Returns:
        LogisticRegression: Meta-learner for stacking.
    """
    return LogisticRegression(
        max_iter=2000,
        solver="lbfgs",
        random_state=RANDOM_STATE
    )


def stacking_ensemble_model(estimators, final_estimator=None):
    """Build a stacking ensemble classifier.
    
    Args:
        estimators: List of (name, model) tuples for base learners.
        final_estimator: Meta-learner (defaults to meta_model() if None).
    
    Returns:
        StackingClassifier: Configured stacking ensemble.
    """
    if final_estimator is None:
        final_estimator = meta_model()
    
    return StackingClassifier(
        estimators=estimators,
        final_estimator=final_estimator,
        cv=3,
        n_jobs=-1,
        passthrough=False
    )


def predict_fake_news(text_list, model, minio_client=None):
    """Predict fake news probability for given text(s).
    
    Applies full feature engineering pipeline (handcrafted + TF-IDF+SVD + embeddings)
    and runs inference with the trained model.
    
    Args:
        text_list: Single text string or list of text strings.
        model: Trained sklearn classifier with predict_proba method.
        minio_client: MinIO client to load pre-fitted transformers. If None, creates new transformers (not recommended).
    
    Returns:
        tuple: (predictions, probabilities)
            - predictions: Binary predictions (0=real, 1=fake) as numpy array.
            - probabilities: Probability of fake news (class 1) as numpy array.
    """
    import pickle
    from io import BytesIO
    
    if isinstance(text_list, str):
        text_list = [text_list]

    # Load pre-fitted transformers from MinIO
    if minio_client is not None:
        try:
            bucket_name = "models"
            
            # Load TF-IDF vectorizer
            tfidf_obj = minio_client.get_object(bucket_name, "transformers/tfidf_vectorizer.pkl")
            tfidf = pickle.load(BytesIO(tfidf_obj.read()))
            
            # Load SVD transformer
            svd_obj = minio_client.get_object(bucket_name, "transformers/svd_transformer.pkl")
            svd = pickle.load(BytesIO(svd_obj.read()))
        except Exception as e:
            print(f"Warning: Failed to load transformers from MinIO: {e}. Creating new ones.")
            tfidf = create_tfidf_vectorizer()
            svd = create_svd_transformer()
    else:
        # Fallback: create new transformers (not recommended for production)
        tfidf = create_tfidf_vectorizer()
        svd = create_svd_transformer()

    series = pd.Series(text_list)

    # Extract handcrafted features
    hand = handcrafted_features(series)

    # Extract TF-IDF + SVD features (use transform, not fit_transform)
    tfidf_vec = tfidf.transform(series)
    svd_vec = svd.transform(tfidf_vec)

    # Extract sentence embeddings
    emb = encode_texts_st(text_list)

    # Combine all features
    X_all = combine(emb, svd_vec, hand)

    # Predict
    prob = model.predict_proba(X_all)[:, 1]
    pred = (prob >= 0.5).astype(int)

    return pred, prob