import os
import re
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from rapidfuzz import fuzz
from xgboost import XGBClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from utils.common import TRAIN_DATA_PATH, SUBJECT_MODEL_PATH, SUBJECT_TRAIN_CACHE_PATH
from utils.layout_extractor import extract_lines_with_layout

def clean_subject_from_filename(filename: str) -> str:
    """Extrahiert den Betreff aus 'YYYY.MM.DD Betreff.pdf'."""
    name = Path(filename).stem
    # Entferne Datum am Anfang (z.B. 2023.10.15 )
    name = re.sub(r'^\d{4}\.\d{2}\.\d{2}\s+', '', name)
    return name.strip()

def get_text_features(text: str):
    """Berechnet numerische Text-Features."""
    return {
        "text_len": len(text),
        "word_count": len(text.split()),
        "upper_ratio": sum(1 for c in text if c.isupper()) / len(text) if text else 0,
        "digit_ratio": sum(1 for c in text if c.isdigit()) / len(text) if text else 0,
        "special_ratio": sum(1 for c in text if not c.isalnum()) / len(text) if text else 0
    }

def prepare_dataset():
    if SUBJECT_TRAIN_CACHE_PATH.exists():
        print("Lade Datensatz aus Cache...")
        return joblib.load(SUBJECT_TRAIN_CACHE_PATH)

    all_pdfs = list(TRAIN_DATA_PATH.rglob("*.pdf"))
    data_rows = []

    for pdf_path in tqdm(all_pdfs, desc="Verarbeite Dokumente für Betreff-Training"):
        target_subject = clean_subject_from_filename(pdf_path.name)
        if len(target_subject) < 3: continue

        lines = extract_lines_with_layout(pdf_path)
        if not lines: continue

        # Finde die Zeile, die dem Dateinamen am ähnlichsten ist
        similarities = [fuzz.token_set_ratio(target_subject, l["text"]) for l in lines]
        if not similarities or max(similarities) < 70: continue
        
        best_idx = np.argmax(similarities)

        for i, line in enumerate(lines):
            row = line.copy()
            row.update(get_text_features(line["text"]))
            row["label"] = 1 if i == best_idx else 0
            data_rows.append(row)

    df = pd.DataFrame(data_rows)
    joblib.dump(df, SUBJECT_TRAIN_CACHE_PATH)
    return df

def train():
    df = prepare_dataset()
    if df.empty:
        print("Keine Daten zum Trainieren gefunden.")
        return

    # Feature-Gruppen definieren
    numeric_features = [
        "rel_x0", "rel_top", "rel_width", "rel_height", 
        "font_size", "is_bold", "page_idx", "line_idx",
        "dist_prev", "dist_next", "is_salutation",
        "text_len", "word_count", "upper_ratio", "digit_ratio", "special_ratio"
    ]
    
    # Preprocessing Pipeline
    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), numeric_features),
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=500), "text")
    ])

    # Model Pipeline
    # Wir nutzen scale_pos_weight, da wir viel mehr negative als positive Beispiele haben
    pos_weight = (len(df[df.label == 0]) / len(df[df.label == 1]))
    
    clf = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", XGBClassifier(
            n_estimators=200, 
            max_depth=5, 
            learning_rate=0.1, 
            scale_pos_weight=pos_weight,
            use_label_encoder=False,
            eval_metric="logloss"
        ))
    ])

    print(f"Trainiere Modell auf {len(df)} Zeilen...")
    clf.fit(df, df["label"])
    
    joblib.dump(clf, SUBJECT_MODEL_PATH)
    print(f"Betreff-Modell gespeichert unter {SUBJECT_MODEL_PATH}")

if __name__ == "__main__":
    train()

def predict_subject(pdf_path: Path, model: Pipeline):
   lines = extract_lines_with_layout(pdf_path)
   if not lines: return None
   
   df_test = pd.DataFrame([
       {**l, **get_text_features(l["text"])} for l in lines
   ])
   
   # Wahrscheinlichkeiten für "ist Betreff" (Klasse 1)
   probs = model.predict_proba(df_test)[:, 1]
   best_line_idx = np.argmax(probs)
   
   if probs[best_line_idx] > 0.5:
       return lines[best_line_idx]["text"]
   return None
