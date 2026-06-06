import os
import time
import logging
from typing import Optional
import joblib
import pdfplumber
from pathlib import Path # Keep Path for BASE_PATH, INBOX_PATH etc.
from datetime import datetime

from sklearn.pipeline import Pipeline

from train_model import train_model # Import train_model from its new home
from utils.matchers import extract_date_from_text, normalize_text
from utils.common import (
    FOLDER_PROJECT, FOLDER_INBOX, FOLDER_UNSURE, FOLDER_REVIEW,
    MODEL_PATH, LOG_FILE, extract_pdf_content
)

CONFIDENCE_THRESHOLD = 0.75

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()]
)

def get_model() -> Optional[Pipeline]:
    if MODEL_PATH.exists():
        return joblib.load(MODEL_PATH)
    return train_model()

def process_file(file_path: Path, model: Pipeline):
    """Klassifiziert und verschiebt eine einzelne Datei."""
    if not file_path.suffix.lower() == ".pdf":
        return

    logging.info(f"Verarbeite: {file_path.name}")
    
    # 1. Text extrahieren
    text, extracted_subject = extract_pdf_content(file_path)
    if not text:
        logging.warning(f"Kein Text in {file_path.name}. Verschiebe nach Unsure.")
        move_to(file_path, FOLDER_UNSURE / "Kein_Text")
        return

    # 2. Datum finden
    doc_date = extract_date_from_text(text)
    date_str = doc_date.strftime("%Y.%m.%d") if doc_date else None
    
    # 3. Klassifizierung
    norm_text = normalize_text(text)
    probs = model.predict_proba([norm_text])[0]
    
    # Beispiel für Debug-Logging in sort_inbox.py
    top_indices = probs.argsort()[-3:][::-1]
    for idx in top_indices:
        logging.info(f"  Mögliche Kategorie: {model.classes_[idx]} ({probs[idx]:.2f})")

    best_idx = probs.argmax()
    confidence = probs[best_idx]
    category = model.classes_[best_idx]

    # Fallback Datum
    if not date_str:
        mtime = os.path.getmtime(file_path)
        date_str = datetime.fromtimestamp(mtime).strftime("%Y.%m.%d")
        target_base = FOLDER_UNSURE
        reason = "Kein_Datum_im_Text"
    elif confidence < CONFIDENCE_THRESHOLD:
        target_base = FOLDER_UNSURE
        reason = f"Niedrige_Konfidenz_{confidence:.2f}"
    else:
        target_base = FOLDER_REVIEW
        reason = None

    # Ziel-Pfad bauen
    new_name = f"{date_str} {extracted_subject}.pdf"
    if reason:
        dest_folder = target_base / reason / category
    else:
        dest_folder = target_base / category
        
    move_to(file_path, dest_folder, new_name, confidence)

def move_to(src: Path, dest_folder: Path, new_name: str = None, conf: float = 0.0):
    """Hilfsfunktion zum sicheren Verschieben und Erstellen von Ordnern."""
    # dest_folder.mkdir(parents=True, exist_ok=True)
    target_name = new_name if new_name else src.name
    dest_path = dest_folder / target_name
    
    # Falls Datei existiert, Zeitstempel anhängen
    if dest_path.exists():
        dest_path = dest_folder / f"{int(time.time())}_{target_name}"

    try:
        # src.rename(dest_path)
        logging.info(f"Verschoben: {dest_path} ({target_name}) -> {dest_folder.relative_to(FOLDER_PROJECT)} (Konfidenz: {conf:.2f})")
    except Exception as e:
        logging.error(f"Fehler beim Verschieben von {src.name}: {e}")

def main():
    model = get_model()
    if not model:
        return

    files = list(FOLDER_INBOX.glob("*.pdf"))
    if not files:
        print("Inbox ist leer.")
        return

    for file_path in files:
        process_file(file_path, model)

if __name__ == "__main__":
    main()