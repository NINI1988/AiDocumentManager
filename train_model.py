import os
import logging
from typing import Optional
import joblib
import time
from pathlib import Path
import hashlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectKBest, chi2
from tqdm import tqdm

from utils.matchers import normalize_text
from utils.common import TRAIN_DATA_PATH, MODEL_PATH, TRAIN_CACHE_PATH, extract_pdf_content

# Einfache Liste deutscher Stop-Words zur Verbesserung der Trennschärfe
GERMAN_STOP_WORDS = [
    # Articles
    "der", "die", "das", "ein", "eine", "einer", "einem", "einen",

    # Pronouns
    "ich", "du", "er", "sie", "es", "wir", "ihr", "ihnen",
    "mein", "meine", "meiner", "meinem", "meinen",
    "dein", "deine", "deiner", "deinem", "deinen",
    "sein", "seine", "seiner", "seinem", "seinen",
    "ihr", "ihre", "ihrer", "ihrem", "ihren",

    # Prepositions
    "von", "vom", "zu", "zum", "zur", "mit", "bei", "nach",
    "für", "auf", "aus", "in", "im", "an", "am", "unter",
    "über", "durch", "gegen", "ohne",

    # Conjunctions
    "und", "oder", "aber", "sowie", "dass", "da", "weil",
    "wenn", "als", "ob",

    # Common verbs
    "ist", "sind", "war", "waren", "wird", "werden",
    "hat", "haben", "hatte", "hatten",
    "kann", "können", "soll", "sollen",

    # Misc
    "auch", "noch", "bereits", "nur", "nicht", "kein",
    "eines", "einem", "einer", "des", "dem", "den",

    # OCR/document noise
    "gmbh", "kg", "ag", "mbh", "euro", "eur",
    "rechnung", "konto", "datum"
]

def get_file_hash(path: Path) -> str:
    """Erzeugt einen MD5-Hash des Dateiinhalts."""
    hasher = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def train_model() -> Optional[Pipeline]:
    """Trainiert das Modell basierend auf der bestehenden Ordnerstruktur."""
    logging.info(f"Starte Training mit Daten aus: {TRAIN_DATA_PATH}")
    X, y = [], []
    
    all_pdf_files = list(TRAIN_DATA_PATH.rglob("*.pdf"))
    if not all_pdf_files:
        logging.warning("Keine Trainings-PDFs gefunden!")
        return None

    # Cache laden
    cache = {}
    if TRAIN_CACHE_PATH.exists():
        try:
            cache = joblib.load(TRAIN_CACHE_PATH)
            logging.info(f"Cache geladen: {len(cache)} Einträge.")
        except Exception as e:
            logging.warning(f"Konnte Cache nicht laden: {e}")

    current_cache = {}
    cache_hits = 0
    
    for pdf_file in tqdm(all_pdf_files, desc="PDFs verarbeiten", unit="file"):
        # Label bestimmen: Relativer Pfad bis zu 2 Ebenen
        rel_path = pdf_file.relative_to(TRAIN_DATA_PATH)
        parts = rel_path.parts[:-1] # Ohne Dateiname
        if not parts:
            continue
        
        label = os.path.join(*parts[:2]) # Max 2 Ebenen
        
        # Hash berechnen für Cache-Prüfung
        file_hash = get_file_hash(pdf_file)
        
        if file_hash in cache:
            norm_text = cache[file_hash]
            cache_hits += 1
        else:
            text, _ = extract_pdf_content(pdf_file)
            norm_text = normalize_text(text) if text else ""

        # In den aktuellen Cache für diesen Lauf übernehmen
        current_cache[file_hash] = norm_text

        if norm_text and len(norm_text.strip()) > 10:
            X.append(norm_text)
            y.append(label)
            
    if not X: # Check again after processing, in case all PDFs were empty
        logging.warning("Keine Trainingsdaten gefunden!")
        return None

    # Neuen Cache speichern
    joblib.dump(current_cache, TRAIN_CACHE_PATH)
    logging.info(f"Verarbeitung abgeschlossen. Cache-Treffer: {cache_hits}, Neu eingelesen: {len(all_pdf_files) - cache_hits}")

    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            # ngram_range=(1, 3), # Jetzt bis zu 3 Wörter (z.B. "Deutsche Rentenversicherung Bund")
            # stop_words=GERMAN_STOP_WORDS,
            min_df=2,
            max_df=0.7,  # Strenger: Wörter, die in >70% der Docs vorkommen, fliegen raus
            sublinear_tf=True,  # Dämpft die Häufigkeit (10x "Auto" ist nicht 10x so wichtig wie 1x)
            # # WICHTIG: Nur Wörter mit mind. 3 Buchstaben, keine reinen Zahlen
            # token_pattern=r"(?u)\b[a-zA-ZäöüÄÖÜß]{3,}\b"
            
            # token_pattern=r"(?u)\b[a-zA-Z0-9äöüÄÖÜß]{3,}\b"
        )),
        # Feature Selection: Behalte nur die Wörter/Phrasen, die am 
        # stärksten zwischen den Kategorien unterscheiden
        # ('chi2', SelectKBest(chi2, k=5000)), 
        ('clf', MultinomialNB())
    ])
    
    logging.info(f"Pipeline Fit startet. Anzahl Dokumente: {len(X)}, Anzahl Kategorien: {len(set(y))}")
    fit_start_time = time.time()
    pipeline.fit(X, y)
    fit_end_time = time.time()
    joblib.dump(pipeline, MODEL_PATH)
    logging.info(f"Modell trainiert und gespeichert: {len(X)} Dokumente, {len(set(y))} Kategorien. Fit-Dauer: {fit_end_time - fit_start_time:.2f} Sekunden.")
    return pipeline

if __name__ == "__main__":
    # Konfiguriere einfaches Konsolen-Logging für das manuelle Training
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    start_time = time.time()

    print(f"--- Modell-Training wird gestartet ---")
    print(f"Quelle: {TRAIN_DATA_PATH}") # Use the local TRAIN_DATA_PATH
    
    model = train_model()
    if model:
        end_time = time.time()
        print(f"--- Training erfolgreich abgeschlossen und Modell gespeichert! Dauer: {end_time - start_time:.2f} Sekunden ---")
    else:
        print("--- Fehler: Training konnte nicht durchgeführt werden (keine Daten?). ---")