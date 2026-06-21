import os
import logging
import joblib
import time
import hashlib
import sys
from pathlib import Path
from typing import Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from tqdm import tqdm

from utils.matchers import normalize_text
from utils.config import GERMAN_STOP_WORDS, MODEL_PATH, TRAIN_DATA_PATH, TRAIN_CACHE_PATH
from utils.common import extract_pdf_content

def get_file_hash(path: Path) -> str:
    """Generates an MD5 hash of the file content."""
    hasher = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

_cached_model: Optional[Pipeline] = None
_model_load_attempted: bool = False

def get_model() -> Optional[Pipeline]:
    """Loads the model if it exists; training is explicit via train_model()."""
    global _cached_model, _model_load_attempted
    if _cached_model is not None:
        return _cached_model

    if _model_load_attempted:
        return None
    _model_load_attempted = True

    if MODEL_PATH.exists():
        try:
            _cached_model = joblib.load(MODEL_PATH)
            return _cached_model
        except Exception as e:
            logging.error(f"Error loading the model: {e}")

    logging.error(f"Model file not found or unavailable: {MODEL_PATH}. Run 'python train_model.py' first.")
    return None

def train_model() -> Optional[Pipeline]:
    """Trains the model based on the existing folder structure."""
    logging.info(f"Starting training with data from: {TRAIN_DATA_PATH}")
    X, y = [], []
    show_progress = sys.stderr is not None
    
    all_pdf_files = list(TRAIN_DATA_PATH.rglob("*.pdf"))
    if not all_pdf_files:
        logging.warning("No training PDFs found!")
        return None

    cache = {}
    if TRAIN_CACHE_PATH.exists():
        try:
            cache = joblib.load(TRAIN_CACHE_PATH)
            logging.info(f"Cache loaded: {len(cache)} entries.")
        except Exception as e:
            logging.warning(f"Could not load cache: {e}")

    cache_hits = 0
    for pdf_file in tqdm(all_pdf_files, desc="PDFs verarbeiten", unit="file", disable=not show_progress):
        rel_path = pdf_file.relative_to(TRAIN_DATA_PATH)
        parts = rel_path.parts[:-1]
        if not parts:
            continue
        
        label = os.path.join(*parts)
        file_hash = get_file_hash(pdf_file)
        
        if file_hash in cache:
            norm_text = cache[file_hash]
            cache_hits += 1
        else:
            text, _ = extract_pdf_content(pdf_file)
            norm_text = normalize_text(text) if text else ""
            cache[file_hash] = norm_text

        if norm_text and len(norm_text.strip()) > 10:
            X.append(norm_text)
            y.append(label)
            
    if not X:
        logging.warning("No training data found!")
        return None

    joblib.dump(cache, TRAIN_CACHE_PATH, compress=3)
    logging.info(f"Processing complete. Cache hits: {cache_hits}")

    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            stop_words=GERMAN_STOP_WORDS,
            min_df=2,
            max_df=0.9,
            max_features=50000,
            token_pattern=r"(?u)\b[a-zA-Z0-9äöüÄÖÜß]{3,}\b"
        )),
        ('clf', MultinomialNB(alpha=0.01))
    ])
    
    logging.info(f"Pipeline Fit starts. Documents: {len(X)}, Categories: {len(set(y))}")
    fit_start_time = time.time()
    pipeline.fit(X, y)
    fit_end_time = time.time()
    joblib.dump(pipeline, MODEL_PATH, compress=3)
    logging.info(f"Model trained. Duration: {fit_end_time - fit_start_time:.2f}s")
    
    global _cached_model
    _cached_model = pipeline
    return pipeline
