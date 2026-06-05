import os
import logging
import joblib
import time
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from tqdm import tqdm

from utils.matchers import normalize_text
from utils.common import TRAIN_DATA_PATH, MODEL_PATH, extract_pdf_content

def train_model():
    """Trainiert das Modell basierend auf der bestehenden Ordnerstruktur."""
    logging.info(f"Starte Training mit Daten aus: {TRAIN_DATA_PATH}")
    X, y = [], []
    
    all_pdf_files = list(TRAIN_DATA_PATH.rglob("*.pdf"))
    if not all_pdf_files:
        logging.warning("Keine Trainings-PDFs gefunden!")
        return None
    
    for pdf_file in tqdm(all_pdf_files, desc="PDFs verarbeiten", unit="file"):
        # Label bestimmen: Relativer Pfad bis zu 2 Ebenen
        rel_path = pdf_file.relative_to(TRAIN_DATA_PATH)
        parts = rel_path.parts[:-1] # Ohne Dateiname
        if not parts:
            continue
        
        label = os.path.join(*parts[:2]) # Max 2 Ebenen
        
        text, _ = extract_pdf_content(pdf_file) # Use the imported function
        if text and len(text.strip()) > 10:
            X.append(normalize_text(text))
            y.append(label)
            
    if not X: # Check again after processing, in case all PDFs were empty
        logging.warning("Keine Trainingsdaten gefunden!")
        return None

    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), stop_words=None)),
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
        print("--- Training erfolgreich abgeschlossen und Modell gespeichert! ---")
    else:
        print("--- Fehler: Training konnte nicht durchgeführt werden (keine Daten?). ---")