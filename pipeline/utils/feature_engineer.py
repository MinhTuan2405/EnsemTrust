import pandas as pd
import numpy as np
import textstat
from sentence_transformers import SentenceTransformer
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD


import os
from dotenv import load_dotenv
load_dotenv ()

# Configuration from environment variables
TFIDF_MAX_FEATURES = int(os.getenv('TFIDF_MAX_FEATURES', 5000))
SVD_COMPONENTS = int(os.getenv('SVD_COMPONENTS', 300))
RANDOM_STATE = int(os.getenv('RANDOM_STATE', 42))


device = "cuda" if torch.cuda.is_available() else "cpu"


# Factory functions to create fresh instances (avoid state pollution)
def create_tfidf_vectorizer():
    """Create a new TF-IDF vectorizer instance"""
    return TfidfVectorizer(max_features=TFIDF_MAX_FEATURES, ngram_range=(1, 2))

def create_svd_transformer():
    """Create a new SVD transformer instance"""
    return TruncatedSVD(n_components=SVD_COMPONENTS, random_state=RANDOM_STATE)


def handcrafted_features(texts):
    features = pd.DataFrame()
    features['len_text'] = texts.apply(lambda x: len(x))
    features['num_words'] = texts.apply(lambda x: len(x.split()))
    features['avg_word_length'] = texts.apply(lambda x: np.mean([len(w) for w in x.split()]))
    features['num_sentences'] = texts.apply(lambda x: x.count('.'))
    features['num_uppercase'] = texts.apply(lambda x: sum(1 for c in x if c.isupper()))
    features['exclamation_ratio'] = texts.apply(lambda x: x.count('!')/(len(x)+1))
    features['question_ratio'] = texts.apply(lambda x: x.count('?')/(len(x)+1))
    features['dot_ratio'] = texts.apply(lambda x: x.count('.')/(len(x)+1))
    features['comma_ratio'] = texts.apply(lambda x: x.count(',')/(len(x)+1))
    features['semicolon_ratio'] = texts.apply(lambda x: x.count(';')/(len(x)+1))
    features['colon_ratio'] = texts.apply(lambda x: x.count(':')/(len(x)+1))
    features['quote_ratio'] = texts.apply(lambda x: x.count('"')/(len(x)+1))
    features['parenthesis_ratio'] = texts.apply(lambda x: x.count('(')/(len(x)+1))
    features['bracket_ratio'] = texts.apply(lambda x: x.count('[')/(len(x)+1))
    features['backslash_ratio'] = texts.apply(lambda x: x.count('\\')/(len(x)+1))
    features['bar_ratio'] = texts.apply(lambda x: x.count('|')/(len(x)+1))
    features['dollar_ratio'] = texts.apply(lambda x: x.count('$')/(len(x)+1))
    features['percent_ratio'] = texts.apply(lambda x: x.count('%')/(len(x)+1))
    features['ampersand_ratio'] = texts.apply(lambda x: x.count('&')/(len(x)+1))
    features['star_ratio'] = texts.apply(lambda x: x.count('*')/(len(x)+1))
    features['at_ratio'] = texts.apply(lambda x: x.count('@')/(len(x)+1))
    features['hash_ratio'] = texts.apply(lambda x: x.count('#')/(len(x)+1))
    features['caret_ratio'] = texts.apply(lambda x: x.count('^')/(len(x)+1))
    features['tilde_ratio'] = texts.apply(lambda x: x.count('~')/(len(x)+1))
    features['backtick_ratio'] = texts.apply(lambda x: x.count('`')/(len(x)+1))
    features['readability'] = texts.apply(lambda x: textstat.flesch_reading_ease(x) if len(x)>0 else 0)
    return features


model_st = SentenceTransformer("all-MiniLM-L6-v2", device=device)

def encode_texts_st(texts, batch_size=32):
    """
    Encode list/Series of texts into sentence embeddings using SentenceTransformer.
    """
    # sentence-transformers đã tự động batch trong encode
    emb = model_st.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=False
    )
    return emb


def combine(emb, tfidf_svd, hand):
    # emb: (N, E), tfidf_svd: (N, S), hand: DataFrame (N, H)
    return np.hstack([emb, tfidf_svd, hand.values])