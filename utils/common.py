from abc import ABC
from pathlib import Path
from dataclasses import dataclass
import re
import datetime
import logging
import sys
from typing import List, Tuple, Optional

import fitz  # pymupdf

from .config import (
    Mode, MODE
)


def extract_pdf_content(pdf_path: Path) -> Optional[str]:
    """Extracts text from a PDF using PyMuPDF."""
    try:
        with fitz.open(pdf_path) as doc:
            full_text = []
            for page in doc:
                page_text = page.get_text()
                if page_text:
                    full_text.append(page_text)
            
            if not full_text:
                return None
            
            return "\n".join(full_text)
    except Exception as e:
        logging.error(f"Error reading {pdf_path}: {e}")
        return None


def sanitize(s: str) -> str:
    s = re.sub(r'[:\\/<>|"?*\n\r]+', '', s)
    s = re.sub(r'\s{2,}', ' ', s).strip()
    return s[:120] if s else "No Subject"


def file_mod_date(path: Path) -> datetime.date:
    return datetime.date.fromtimestamp(path.stat().st_mtime)


def build_name(d: datetime.date, subj: str) -> str:
    return f"{d.strftime('%Y.%m.%d')} {sanitize(subj)}.pdf"


@dataclass
class ProcessingContext:
    input_file: Path
    text: str
    subfolder: str
    date: Optional[datetime.date] = None
    subject: Optional[str] = None
    output_file: Optional[Path] = None
    confidence: float = 0.0

class BaseHandler(ABC):
    """Handler interface for document recognition and metadata extraction."""

    def setup(self) -> None:
        """
        Optional one-time initialization before a processing batch starts.
        Default implementation does nothing.
        """
        pass

    def handle(self, context: ProcessingContext) -> None:
        """
        Pre-processing: Handlers check the context and text to refine metadata.
        """
        pass

    def post_process(self, context: ProcessingContext) -> None:
        """
        Performs additional operations after the main file movement/copy.
        Default implementation does nothing.
        """
        pass

    def teardown(self) -> None:
        """
        Optional cleanup after a processing batch ends.
        Default implementation does nothing.
        """
        pass

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


def print_docs_table(contexts: List[ProcessingContext], base_folder: Path) -> None:
    """Print an aligned table of parsed documents (Source, Target) using paths relative to base_folder."""
    rows: List[Tuple[str, str]] = []
    for ctx in contexts:
        try:
            rel = str(ctx.output_file.relative_to(base_folder))
        except Exception:
            rel = str(ctx.output_file)
        rows.append((ctx.input_file.name, rel))
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


def apply_file_operation(context: ProcessingContext) -> None:
    """Apply file operation (move/copy/no-change) using the global MODE setting."""
    import shutil

    # Resolve unique target once here and update doc.target to the resolved path.
    final_target: Path = unique_path(context.output_file)
    final_target.parent.mkdir(parents=True, exist_ok=True)

    if MODE == Mode.MOVE: # else: NO_CHANGE, do nothing
        shutil.move(str(context.input_file), str(final_target))
        context.output_file = final_target
    elif MODE == Mode.COPY:
        shutil.copy(str(context.input_file), str(final_target))
        context.output_file = final_target
    # else: NO_CHANGE, do nothing

def wait_if_not_debugging():
    if sys.gettrace() is None:
        input("Press Enter to exit...")
