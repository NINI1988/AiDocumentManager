import logging
import joblib
import os
from pathlib import Path
from tqdm import tqdm
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from collections import Counter

from train_model import GERMAN_STOP_WORDS, get_file_hash
from utils.matchers import normalize_text
from utils.common import TRAIN_DATA_PATH, TRAIN_CACHE_PATH, extract_pdf_content

def load_dataset():
    """Lädt die Daten analog zu train_model.py für die Evaluierung."""
    X, y = [], []
    all_pdf_files = list(TRAIN_DATA_PATH.rglob("*.pdf"))
    
    cache = {}
    if TRAIN_CACHE_PATH.exists():
        cache = joblib.load(TRAIN_CACHE_PATH)

    logging.info(f"Lade {len(all_pdf_files)} Dateien für die Validierung...")
    
    for pdf_file in tqdm(all_pdf_files, desc="Daten einlesen"):
        rel_path = pdf_file.relative_to(TRAIN_DATA_PATH)
        parts = rel_path.parts[:-1]
        if not parts:
            continue
        
        # label = os.path.join(*parts[:2])
        label = os.path.join(*parts)
        
        file_hash = get_file_hash(pdf_file)
        if file_hash in cache:
            norm_text = cache[file_hash]
        else:
            text, _ = extract_pdf_content(pdf_file)
            norm_text = normalize_text(text) if text else ""
            
        if norm_text and len(norm_text.strip()) > 10:
            X.append(norm_text)
            y.append(label)
            
    return X, y

def run_accuracy_test():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    
    logging.info("Lade Datensatz...")
    X, y = load_dataset()
    
    if not X or len(set(y)) < 2:
        logging.error("Nicht genügend Daten oder Kategorien für einen validen Test vorhanden.")
        return

    # Zähle die Vorkommen jeder Kategorie
    class_counts = Counter(y)
    
    # Identifiziere Kategorien mit nur einem Mitglied
    single_sample_classes = {cls for cls, count in class_counts.items() if count < 2}
    
    X_filtered, y_filtered = [], []
    if single_sample_classes:
        logging.warning(f"Folgende Kategorien haben weniger als 2 Samples und werden vom Test ausgeschlossen: {', '.join(single_sample_classes)}")
        for i, label in enumerate(y):
            if label not in single_sample_classes:
                X_filtered.append(X[i])
                y_filtered.append(label)
    else:
        X_filtered, y_filtered = X, y

    if len(set(y_filtered)) < 2 or len(y_filtered) < 2:
        logging.error("Nach dem Filtern sind nicht genügend Kategorien oder Samples für einen Test-Split vorhanden.")
        return

    logging.info(f"Führe Train-Test-Split (80/20) durch auf {len(X_filtered)} Dokumenten...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_filtered, y_filtered,
        test_size=0.2,
        random_state=42,
        stratify=y_filtered
    )
    # Pipeline mit den aktuellsten Parametern aus train_model.py
    
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            stop_words=GERMAN_STOP_WORDS,
            min_df=2,
            max_df=0.9,
            # sublinear_tf=True,
            max_features=50000, # Deckelt die Anzahl der Merkmale
            token_pattern=r"(?u)\b[a-zA-Z0-9äöüÄÖÜß]{3,}\b"
        )),
        ('clf', MultinomialNB(alpha=0.01))
    ])
    
    # pipeline = Pipeline([
    #     ('tfidf', TfidfVectorizer(
    #         analyzer="char_wb",
    #         ngram_range=(3, 5),
    #         # ngram_range=(1, 3), # Jetzt bis zu 3 Wörter (z.B. "Deutsche Rentenversicherung Bund")
    #         # stop_words=GERMAN_STOP_WORDS,
    #         min_df=2,
    #         max_df=0.7,  # Strenger: Wörter, die in >70% der Docs vorkommen, fliegen raus
    #         sublinear_tf=True,  # Dämpft die Häufigkeit (10x "Auto" ist nicht 10x so wichtig wie 1x)
    #     )),
    #     ('clf', MultinomialNB(alpha=1))
    # ])

    logging.info("Trainiere Modell auf Teilmenge...")
    pipeline.fit(X_train, y_train)

    logging.info("Generiere Vorhersagen für Test-Set...")
    pred = pipeline.predict(X_test)

    print("\n" + "="*60)
    print(f"KLASSIFIZIERUNGSBERICHT ({len(X_filtered)} Dokumente für Test verwendet)")
    print("="*60)
    print(classification_report(y_test, pred))
    print("="*60)

if __name__ == "__main__":
    run_accuracy_test()