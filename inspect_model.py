import joblib
import pandas as pd
from utils.common import wait_if_not_debugging
from utils.config import MODEL_PATH

def inspect():
    if not MODEL_PATH.exists():
        print(f"Model not found at {MODEL_PATH}. Please run train_model.py first.")
        return

    # Load model
    pipeline = joblib.load(MODEL_PATH)
    
    # Extract components from the pipeline
    vectorizer = pipeline.named_steps['tfidf']
    selector = pipeline.named_steps.get('chi2')
    classifier = pipeline.named_steps['clf']
    
    # Categories (Labels)
    classes = classifier.classes_
    # Words (Features)
    feature_names = vectorizer.get_feature_names_out()

    # If a feature selector was used, the names must be filtered
    if selector:
        feature_names = feature_names[selector.get_support()]

    print(f"--- Model Analysis ---")
    print(f"Found Categories: {len(classes)}")
    print(f"Vocabulary Size (used): {len(feature_names)} words")
    print("-" * 30)

    # Find the most important words per category
    for i, category in enumerate(classes[:20]):
        # Retrieve the log probabilities for this class
        # (For MultinomialNB, these are the coefficients)
        probs = classifier.feature_log_prob_[i]
        
        # Sort top 10 words for this category
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