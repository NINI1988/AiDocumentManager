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

from utils.config import GERMAN_STOP_WORDS, TRAIN_CACHE_PATH, TRAIN_DATA_PATH
from utils.matchers import normalize_text
from utils.common import extract_pdf_content
from utils.model_utils import get_file_hash


def load_dataset():
    """Loads data analogous to train_model.py for evaluation."""
    X, y = [], []
    all_pdf_files = list(TRAIN_DATA_PATH.rglob("*.pdf"))

    cache = {}
    if TRAIN_CACHE_PATH.exists():
        cache = joblib.load(TRAIN_CACHE_PATH)

    logging.info(f"Loading {len(all_pdf_files)} files for validation...")

    for pdf_file in tqdm(all_pdf_files, desc="Reading data"):
        rel_path = pdf_file.relative_to(TRAIN_DATA_PATH)
        parts = rel_path.parts[:-1]
        if not parts:
            continue

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

    logging.info("Loading dataset...")
    X, y = load_dataset()

    if not X or len(set(y)) < 2:
        logging.error("Not enough data or categories for a valid test available.")
        return

    class_counts = Counter(y)
    single_sample_classes = {cls for cls, count in class_counts.items() if count < 2}

    X_filtered, y_filtered = [], []
    if single_sample_classes:
        logging.warning(
            f"The following categories have less than 2 samples and will be excluded from the test: {', '.join(single_sample_classes)}"
        )
        for i, label in enumerate(y):
            if label not in single_sample_classes:
                X_filtered.append(X[i])
                y_filtered.append(label)
    else:
        X_filtered, y_filtered = X, y

    if len(set(y_filtered)) < 2 or len(y_filtered) < 2:
        logging.error("After filtering, not enough categories or samples are available for a test split.")
        return

    logging.info(f"Performing train-test split (80/20) on {len(X_filtered)} documents...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_filtered,
        y_filtered,
        test_size=0.2,
        random_state=42,
        stratify=y_filtered,
    )

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            stop_words=GERMAN_STOP_WORDS,
            min_df=2,
            max_df=0.9,
            max_features=50000,
            token_pattern=r"(?u)\b[a-zA-Z0-9äöüÄÖÜß]{3,}\b"
        )),
        ("clf", MultinomialNB(alpha=0.01)),
    ])

    logging.info("Training model on subset...")
    pipeline.fit(X_train, y_train)

    logging.info("Generating predictions for test set...")
    pred = pipeline.predict(X_test)

    print("\n" + "=" * 60)
    print(f"CLASSIFICATION REPORT ({len(X_filtered)} documents used for test)")
    print("=" * 60)
    print(classification_report(y_test, pred))
    print("=" * 60)


if __name__ == "__main__":
    run_accuracy_test()
