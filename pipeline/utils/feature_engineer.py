import pandas as pd
import numpy as np
import textstat
from sentence_transformers import SentenceTransformer
import torch
from sklearn.feature_extraction.text import TfidfVectorizer

import os
from dotenv import load_dotenv
load_dotenv ()

max_feat = os.getenv ('TFIDF_MAX_FEATURES', 5000)


device = "cuda" if torch.cuda.is_available() else "cpu"



tfidf = TfidfVectorizer(max_features=max_feat, ngram_range=(1,2))


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
