from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass
import re
import datetime
import logging
import sys
from typing import List, Tuple, Optional
from enum import Enum

import pdfplumber

# Unterdrücke die gesprächigen Warnungen des PDF-Parsers (pdfminer.six)
logging.getLogger("pdfminer").setLevel(logging.ERROR)


# Project-level folders and mode enum
# FOLDER_PROJECT is the workspace root (parent of the folder containing utils)
FOLDER_PROJECT = Path(__file__).resolve().parents[1]
FOLDER_INBOX = FOLDER_PROJECT / "1. Inbox"
# FOLDER_INBOX = Path("G:/OneDrive/Scan")
FOLDER_REVIEW = FOLDER_PROJECT / "3. Review"
FOLDER_UNSURE = FOLDER_PROJECT / "2. Unsure"
# TRAIN_DATA_PATH = FOLDER_PROJECT / "test_documents" / "Dokumente"
TRAIN_DATA_PATH = FOLDER_PROJECT / "test_documents" / "alleDokumente"
MODEL_PATH = FOLDER_PROJECT / "classifier_model_word.pkl"
TRAIN_CACHE_PATH = FOLDER_PROJECT / "train_cache.joblib"
LOG_FILE = FOLDER_PROJECT / "log.txt"


def extract_text(path: Path, max_pages: int = 5) -> str:
    """Extract embedded OCR/text from first pages using pdfplumber."""
    try:
        texts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages[:max_pages]:
                texts.append(page.extract_text() or "")
        return "\n".join(texts)
    except Exception:
        return ""

def extract_pdf_content(pdf_path: Path):
    """Extrahiert Text und eine Betreff-Zeile aus einem PDF."""
    text = ""
    subject = "Unbekannt"
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text.append(page_text)
            
            if not full_text:
                return None, None
            
            text = "\n".join(full_text)
            # Erste Zeile mit Inhalt als Betreff nutzen
            lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 3]
            if lines:
                # Bereinige den Betreff von ungültigen Zeichen
                subject = "".join(c for c in lines[0] if c.isalnum() or c in " -_")[:50]
                
        return text, subject
    except Exception as e:
        logging.error(f"Fehler beim Lesen von {pdf_path}: {e}")
        return None, None


def sanitize(s: str) -> str:
    s = re.sub(r'[:\\/<>|"?*\n\r]+', '', s)
    s = re.sub(r'\s{2,}', ' ', s).strip()
    return s[:120] if s else "No Subject"


def file_mod_date(path: Path) -> datetime.date:
    return datetime.date.fromtimestamp(path.stat().st_mtime)


def build_name(d: datetime.date, subj: str) -> str:
    return f"{d.strftime('%Y.%m.%d')} {sanitize(subj)}.pdf"


@dataclass
class HandlerResult:
    subject: str
    date: Optional[datetime.date]
    subfolder: str  # relative to FOLDER_REVIEW


@dataclass
class Doc:
    path: Path
    subject: str
    date: datetime.date
    target: Path


class BaseHandler(ABC):
    """Handler interface for document recognition and metadata extraction."""

    @abstractmethod
    def handle(self, text: str, path: Path) -> Optional[HandlerResult]:
        pass

    @abstractmethod
    def get_categories(self) -> List[str]:
        """Return a list of categories this handler can process."""
        pass


class Mode(Enum):
    """File operation mode."""
    NO_CHANGE = "NO_CHANGE"
    MOVE = "MOVE"
    COPY = "COPY"


def print_rows_table(rows: List[Tuple[str, str]]) -> None:
    """Print an aligned table of (Source, Target) rows."""
    if not rows:
        return

    src_col = max(len(r[0]) for r in rows)
    tgt_col = max(len(r[1]) for r in rows)
    src_col = max(src_col, len("Source"))
    tgt_col = max(tgt_col, len("Target"))
    print(f"{'Source':<{src_col}}  {'Target':<{tgt_col}}")
    print(f"{'-'*src_col}  {'-'*tgt_col}")
    for src, tgt in rows:
        print(f"{src:<{src_col}}  {tgt:<{tgt_col}}")
    print()


def print_docs_table(docs: List[Doc], base_folder: Path) -> None:
    """Print an aligned table of parsed documents (Source, Target) using paths relative to base_folder."""
    rows: List[Tuple[str, str]] = []
    for doc in docs:
        try:
            rel = str(doc.target.relative_to(base_folder))
        except Exception:
            rel = str(doc.target)
        rows.append((doc.path.name, rel))
    print_rows_table(rows)


def unique_path(path: Path) -> Path:
    """Return a non-existing Path by appending ' (N)' before the suffix when needed.

    Example: if 'file.pdf' exists, returns 'file (1).pdf', then 'file (2).pdf', etc.
    """
    if not path.exists():
        return path
    parent = path.parent
    base = path.stem
    suffix = path.suffix
    counter = 1
    while True:
        candidate = parent / f"{base} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def apply_file_operation(doc: Doc, mode: Mode) -> None:
    """Apply file operation (move/copy/no-change) for a Doc using the provided Mode enum."""
    import shutil

    # Resolve unique target once here and update doc.target to the resolved path.
    final_target: Path = unique_path(doc.target)
    final_target.parent.mkdir(parents=True, exist_ok=True)

    if mode == Mode.MOVE:
        shutil.move(str(doc.path), str(final_target))
        doc.target = final_target
    elif mode == Mode.COPY:
        shutil.copy(str(doc.path), str(final_target))
        doc.target = final_target
    # else: NO_CHANGE, do nothing

def wait_if_not_debugging():
    if sys.gettrace() is None:
        input("Press Enter to exit...")