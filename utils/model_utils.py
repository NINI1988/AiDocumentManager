import os
import logging
import joblib
import time
import hashlib
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
    """Erzeugt einen MD5-Hash des Dateiinhalts."""
    hasher = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_model() -> Optional[Pipeline]:
    """Lädt das Modell oder trainiert es neu, falls nicht vorhanden."""
    if MODEL_PATH.exists():
        try:
            return joblib.load(MODEL_PATH)
        except Exception as e:
            logging.error(f"Fehler beim Laden des Modells: {e}")
    return train_model()

def train_model() -> Optional[Pipeline]:
    """Trainiert das Modell basierend auf der bestehenden Ordnerstruktur."""
    logging.info(f"Starte Training mit Daten aus: {TRAIN_DATA_PATH}")
    X, y = [], []
    
    all_pdf_files = list(TRAIN_DATA_PATH.rglob("*.pdf"))
    if not all_pdf_files:
        logging.warning("Keine Trainings-PDFs gefunden!")
        return None

    cache = {}
    if TRAIN_CACHE_PATH.exists():
        try:
            cache = joblib.load(TRAIN_CACHE_PATH)
            logging.info(f"Cache geladen: {len(cache)} Einträge.")
        except Exception as e:
            logging.warning(f"Konnte Cache nicht laden: {e}")

    cache_hits = 0
    for pdf_file in tqdm(all_pdf_files, desc="PDFs verarbeiten", unit="file"):
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
        logging.warning("Keine Trainingsdaten gefunden!")
        return None

    joblib.dump(cache, TRAIN_CACHE_PATH, compress=3)
    logging.info(f"Verarbeitung abgeschlossen. Cache-Treffer: {cache_hits}")

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
    
    logging.info(f"Pipeline Fit startet. Dokumente: {len(X)}, Kategorien: {len(set(y))}")
    fit_start_time = time.time()
    pipeline.fit(X, y)
    fit_end_time = time.time()
    joblib.dump(pipeline, MODEL_PATH, compress=3)
    logging.info(f"Modell trainiert. Dauer: {fit_end_time - fit_start_time:.2f}s")
    return pipeline