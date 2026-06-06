import joblib
import pandas as pd
from utils.common import MODEL_PATH, wait_if_not_debugging

def inspect():
    if not MODEL_PATH.exists():
        print(f"Modell nicht gefunden unter {MODEL_PATH}. Bitte zuerst train_model.py ausführen.")
        return

    # Modell laden
    pipeline = joblib.load(MODEL_PATH)
    
    # Komponenten aus der Pipeline extrahieren
    vectorizer = pipeline.named_steps['tfidf']
    selector = pipeline.named_steps.get('chi2')
    classifier = pipeline.named_steps['clf']
    
    # Kategorien (Labels)
    classes = classifier.classes_
    # Wörter (Features)
    feature_names = vectorizer.get_feature_names_out()

    # Falls ein Feature-Selector verwendet wurde, müssen die Namen gefiltert werden
    if selector:
        feature_names = feature_names[selector.get_support()]

    print(f"--- Modell-Analyse ---")
    print(f"Gefundene Kategorien: {len(classes)}")
    print(f"Vokabular-Größe (genutzt): {len(feature_names)} Wörter")
    print("-" * 30)

    # Die wichtigsten Wörter pro Kategorie finden
    for i, category in enumerate(classes):
        # Die Log-Wahrscheinlichkeiten für diese Klasse abrufen
        # (Bei MultinomialNB sind das die Koeffizienten)
        probs = classifier.feature_log_prob_[i]
        
        # Top 10 Wörter für diese Kategorie sortieren
        top_indices = probs.argsort()[-10:][::-1]
        top_features = [feature_names[j] for j in top_indices]
        
        print(f"\nKategorie: {category}")
        print(f"Top Wörter: {', '.join(top_features)}")

if __name__ == "__main__":
    try:
        inspect()
    except Exception as e:
        print(f"Fehler bei der Inspektion: {e}")
        
    # wait_if_not_debugging()