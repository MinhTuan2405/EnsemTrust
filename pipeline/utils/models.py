from sklearn.metrics import classification_report, accuracy_score, roc_auc_score
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression

try:
    from lightgbm import LGBMClassifier
except ImportError:  # optional dependency
    LGBMClassifier = None

import os
from dotenv import load_dotenv

load_dotenv ()


RANDOM_STATE = int(os.getenv('RANDOM_STATE', 42))



def evaluate_model(model, X, y, name="Dataset"):
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]
    print(f"--- {name} ---")
    print("Accuracy:", accuracy_score(y, y_pred))
    print("AUC:", roc_auc_score(y, y_prob))
    print(classification_report(y, y_pred))


def SVM_model():
    """Return a binary SVM classifier with probability outputs enabled."""
    return SVC(kernel="linear", probability=True, random_state=42)


def LightGBM_model():
    """Return a LightGBM classifier with reasonable defaults for binary classification."""
    if LGBMClassifier is None:
        raise ImportError("lightgbm is not installed. Please add it to your dependencies.")

    return LGBMClassifier(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=-1,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary",
        random_state=42,
        n_jobs=-1,
    )


def logisticRegression_model():
    """Return a regularized logistic regression classifier."""
    return LogisticRegression(
        max_iter=5000,
        solver="saga",
        penalty="l2",
        C=0.5,
        random_state=RANDOM_STATE
    )