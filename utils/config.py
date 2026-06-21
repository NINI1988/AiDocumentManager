from pathlib import Path
from enum import Enum

class Mode(Enum):
    """File operation mode."""
    NO_CHANGE = "NO_CHANGE"  # Don't change input files, just log results
    MOVE = "MOVE"  # Move files to review/unsure folders based on classification
    COPY = "COPY"  # Copy files instead of moving. Can be used for testing without affecting original files.

# --- User Settings ---

# FOLDER_PROJECT is the workspace root
FOLDER_PROJECT = Path(__file__).resolve().parents[1]

# Global setting for file operation mode (used in 1_rename.py)
# MODE = Mode.NO_CHANGE
# MODE = Mode.MOVE
# FOLDER_INBOX = FOLDER_PROJECT / "1. Inbox"
# FOLDER_REVIEW = FOLDER_PROJECT / "3. Review"
# FOLDER_UNSURE = FOLDER_PROJECT / "2. Unsure"

MODE = Mode.MOVE
FOLDER_INBOX = Path(r"G:\OneDrive\Scan")
FOLDER_REVIEW = FOLDER_INBOX / "Review"
FOLDER_UNSURE = FOLDER_INBOX / "Unsure"

# Destination root for final document storage (used in 2_move_review.py and TRAIN_DATA_PATH)
DEST_ROOT = Path(r"G:\OneDrive\Dokumente")

# TRAIN_DATA_PATH = FOLDER_PROJECT / "test_documents" / "alleDokumente"
TRAIN_DATA_PATH = DEST_ROOT
MODEL_PATH = FOLDER_PROJECT / "classifier_model_word.pkl"
TRAIN_CACHE_PATH = FOLDER_PROJECT / "train_cache.joblib"
LOG_FILE = FOLDER_PROJECT / "log.txt"

# Minimum confidence for auto-classification
UNSURE_THRESHOLD = 0.75

# Pause duration after an error (e.g. CUDA crash) in seconds
ERROR_PAUSE_SECONDS = 7200

# Path to the local LLM GGUF model
# LLM_MODEL_PATH = r"G:\Programme\LmStudio\lmstudio-community\gemma-4-12B-it-QAT-GGUF\gemma-4-12B-it-QAT-Q4_0.gguf"
LLM_MODEL_PATH = r"G:\Programme\LmStudio\lmstudio-community\gemma-4-E4B-it-QAT-GGUF\gemma-4-E4B-it-QAT-Q4_0.gguf"
# LLM_MODEL_PATH = r"G:/Programme/LmStudio/Qwen/Qwen2.5-3B-Instruct-GGUF/qwen2.5-3b-instruct-q4_k_m.gguf"



# Simple list of German stop words to improve selectivity
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
