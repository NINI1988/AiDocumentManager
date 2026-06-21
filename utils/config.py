import os
from enum import Enum
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


class Mode(Enum):
    """File operation mode."""

    NO_CHANGE = "NO_CHANGE"  # Don't change input files, just log results
    MOVE = "MOVE"  # Move files to review/unsure folders based on classification
    COPY = "COPY"  # Copy files instead of moving. Can be used for testing without affecting original files.


# --- User Settings ---

# FOLDER_PROJECT is the workspace root
FOLDER_PROJECT = Path(__file__).resolve().parents[1]

load_dotenv()


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: '{name}'")
    return value.strip()


def _optional_env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value.strip() if value else default


def _path_env(name: str, default: Optional[Path] = None) -> Path:
    value = os.getenv(name)
    if value:
        return Path(value)
    if default is not None:
        return default
    raise RuntimeError(f"Missing required environment variable: '{name}'")


def _mode_env(name: str, default: Mode) -> Mode:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return Mode[value.strip().upper()]
    except KeyError as exc:
        valid = ", ".join(mode.value for mode in Mode)
        raise RuntimeError(f"Invalid '{name}' value '{value!r}'. Expected one of: '{valid}'") from exc


MODE = _mode_env("MODE", Mode.MOVE)
FOLDER_INBOX = _path_env("FOLDER_INBOX")
FOLDER_REVIEW = _path_env("FOLDER_REVIEW", FOLDER_INBOX / "Review")
FOLDER_UNSURE = _path_env("FOLDER_UNSURE", FOLDER_INBOX / "Unsure")

# Destination root for final document storage (used in 2_move_review.py and TRAIN_DATA_PATH)
DEST_ROOT = _path_env("DEST_ROOT")

# TRAIN_DATA_PATH can point to a separate training folder, but defaults to DEST_ROOT.
TRAIN_DATA_PATH = _path_env("TRAIN_DATA_PATH", DEST_ROOT)
MODEL_PATH = FOLDER_PROJECT / "classifier_model_word.pkl"
TRAIN_CACHE_PATH = FOLDER_PROJECT / "train_cache.joblib"
LOG_FILE = FOLDER_PROJECT / "log.txt"

# Minimum confidence for auto-classification
UNSURE_THRESHOLD = float(_optional_env("UNSURE_THRESHOLD", "0.75"))

# Pause duration after an error (e.g. CUDA crash) in seconds
ERROR_PAUSE_SECONDS = int(_optional_env("ERROR_PAUSE_SECONDS", "7200"))

# Path to the local LLM GGUF model
LLM_MODEL_PATH = _require_env("LLM_MODEL_PATH")



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
