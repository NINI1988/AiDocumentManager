import logging
import datetime
from typing import Optional, List
import joblib
from pathlib import Path
from sklearn.pipeline import Pipeline
from tqdm import tqdm

from train_model import train_model
from train_subject_model import predict_subject
from utils.llm_extractor import extract_metadata_with_llm
from handlers import HANDLERS
from utils.matchers import extract_date_from_text, normalize_text
from utils.common import (
    FOLDER_PROJECT, FOLDER_INBOX, FOLDER_UNSURE, FOLDER_REVIEW,
    MODEL_PATH, SUBJECT_MODEL_PATH, LOG_FILE, extract_pdf_content, build_name, 
    Doc, Mode, apply_file_operation, file_mod_date, BaseHandler,
    wait_if_not_debugging
)

# Global setting for file operation mode
# MODE = Mode.MOVE
MODE = Mode.NO_CHANGE

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

def get_subject_model() -> Optional[Pipeline]:
    if SUBJECT_MODEL_PATH.exists():
        return joblib.load(SUBJECT_MODEL_PATH)
    return None

def find_handlers(category: str) -> List[BaseHandler]:
    """Findet alle Handler, die für eine bestimmte Kategorie zuständig sind."""
    return [h for h in HANDLERS if category in h.get_categories()]

def process_file(file_path: Path, model: Pipeline, subject_model: Optional[Pipeline] = None):
    """Klassifiziert und verschiebt eine einzelne Datei unter Verwendung von Handlern."""
    if not file_path.suffix.lower() == ".pdf":
        return

    logging.info(f"Verarbeite: {file_path.name}")
    
    # 1. Text extrahieren
    text, first_line_subject = extract_pdf_content(file_path)
    if not text:
        logging.warning(f"Kein Text in {file_path.name}. Verschiebe nach Unsure.")
        dest_folder = FOLDER_UNSURE / "Kein_Text"
        doc = Doc(path=file_path, subject="Kein_Text", date=file_mod_date(file_path), 
                  target=dest_folder / file_path.name)
        apply_file_operation(doc, MODE)
        return

    # 2. Klassifizierung
    norm_text = normalize_text(text)
    probs = model.predict_proba([norm_text])[0]
    
    # Debug-Logging für die Top-Kategorien
    top_indices = probs.argsort()[-3:][::-1]
    for idx in top_indices:
        logging.info(f"  Mögliche Kategorie: {model.classes_[idx]} ({probs[idx]:.2f})")

    best_idx = probs.argmax()
    confidence = probs[best_idx]
    category = model.classes_[best_idx]

    # Neu: ML-basierte Betreff-Erkennung
    ml_subject = None
    if subject_model:
        try:
            ml_subject, ml_conf = predict_subject(file_path, subject_model)
            if ml_subject:
                logging.info(f"  ML-Betreff erkannt: {ml_subject} ({ml_conf:.2f})")
        except Exception as e:
            logging.error(f"Fehler bei ML-Betreff-Erkennung: {e}")

    # Neu: LLM-basierte Extraktion (Datum und Betreff)
    llm_metadata = extract_metadata_with_llm(text)
    llm_subject = None
    llm_date = None
    
    if llm_metadata:
        llm_subject = llm_metadata.get("subject")
        if llm_subject:
            logging.info(f"  LLM-Betreff erkannt: {llm_subject}")

        d_str = llm_metadata.get("date")
        if d_str:
            try:
                llm_date = datetime.datetime.strptime(d_str, "%Y.%m.%d").date()
            except Exception:
                pass

    # 3. Metadaten-Extraktion (Datum, Subfolder, Subject)
    doc_date = llm_date or extract_date_from_text(text)
    final_subject = llm_subject or ml_subject or first_line_subject or "Unbekannt"
    final_subfolder = category
    target_base = FOLDER_REVIEW
    reason = None

    # Überprüfung der Konfidenz
    if confidence < CONFIDENCE_THRESHOLD:
        target_base = FOLDER_UNSURE
        reason = f"Niedrige_Konfidenz_{confidence:.2f}"
    
    # Handler suchen und ausführen, falls Konfidenz hoch genug
    if confidence >= CONFIDENCE_THRESHOLD:
        handlers = find_handlers(str(category))
        for h in handlers:
            res = h.handle(text, file_path)
            if res:
                logging.info(f"  Handler '{h.__class__.__name__}' angewendet.")
                final_subject = res.subject
                final_subfolder = res.subfolder
                if res.date:
                    doc_date = res.date
                break

    # Fallback Datum, falls keines im Text gefunden wurde
    if not doc_date:
        doc_date = file_mod_date(file_path)
        if target_base != FOLDER_UNSURE:
            target_base = FOLDER_UNSURE
            reason = "Kein_Datum_im_Text"

    # Ziel-Pfad bauen
    new_name = build_name(doc_date, final_subject)
    dest_folder = target_base / final_subfolder

    doc = Doc(path=file_path, subject=final_subject, date=doc_date, target=dest_folder / new_name)
    
    # 4. Datei verschieben
    logging.info(f"'{file_path}' -> '{dest_folder.relative_to(FOLDER_PROJECT) / new_name}', Reason: {reason or ''}")
    apply_file_operation(doc, MODE)

def main():
    FOLDER_INBOX.mkdir(exist_ok=True)
    FOLDER_REVIEW.mkdir(exist_ok=True)
    FOLDER_UNSURE.mkdir(exist_ok=True)

    model = get_model()
    if not model:
        print(f"No Model found '{MODEL_PATH}'.")
        return
        
    subject_model = get_subject_model()

    files = list(FOLDER_INBOX.glob("*.pdf"))
    if not files:
        print("Inbox ist leer.")
        return
    
    # Phase 1: Parse all files
    print(f"Mode: '{MODE.value}'")
    print(f"Parsing {len(files)} files...\n")

    for file_path in tqdm(files, desc="Parsing files", unit="file"):
        process_file(file_path, model, subject_model)



if __name__ == "__main__":
    main()
    # wait_if_not_debugging()