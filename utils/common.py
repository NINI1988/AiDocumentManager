from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass
import re
import datetime
from typing import List, Tuple, Optional
from enum import Enum

# PDF lib
from PyPDF2 import PdfReader


# Project-level folders and mode enum
# SCRIPT_DIR is the workspace root (parent of the folder containing utils)
SCRIPT_DIR = Path(__file__).resolve().parents[1]
FOLDER_INBOX = SCRIPT_DIR / "1. Inbox"
FOLDER_REVIEW = SCRIPT_DIR / "3. Review"
FOLDER_UNSURE = SCRIPT_DIR / "2. Unsure"


def extract_text(path: Path, max_pages: int = 5) -> str:
    """Extract embedded OCR/text from first pages."""
    try:
        r = PdfReader(str(path))
        pages = r.pages[:max_pages]
        texts = []
        for p in pages:
            t = p.extract_text() or ""
            texts.append(t)
        return "\n".join(texts)
    except Exception:
        return ""


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


class Mode(Enum):
    """File operation mode."""
    NO_CHANGE = "NO_CHANGE"
    MOVE = "MOVE"
    COPY = "COPY"


def print_docs_table(docs: List, base_folder: Path) -> None:
    """Print an aligned table of parsed documents (Source, Target) using paths relative to base_folder."""
    rows: List[Tuple[str, str]] = []
    for doc in docs:
        try:
            rel = doc.target.relative_to(base_folder)
        except Exception:
            rel = doc.target
        rows.append((doc.path.name, str(rel)))

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

    if mode == Mode.MOVE:
        shutil.move(str(doc.path), str(final_target))
        doc.target = final_target
    elif mode == Mode.COPY:
        shutil.copy(str(doc.path), str(final_target))
        doc.target = final_target
    # else: NO_CHANGE, do nothing
