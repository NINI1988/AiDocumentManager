from abc import ABC, abstractmethod
from pathlib import Path
from dataclasses import dataclass
import re
import datetime
from typing import List, Tuple, Optional
from enum import Enum
from difflib import SequenceMatcher

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


def extract_date_from_text(text: str):
    """Find first plausible date, allow spaces, ignore old ones (<2000)."""
    patterns = [
        r'(\d{4})\s*[.\-/]\s*(\d{1,2})\s*[.\-/]\s*(\d{1,2})',  # yyyy.mm.dd
        r'(\d{1,2})\s*[.\-/]\s*(\d{1,2})\s*[.\-/]\s*(\d{4})'   # dd.mm.yyyy
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if not m:
            continue
        g = m.groups()
        try:
            if len(g[0]) == 4:  # yyyy.mm.dd
                y, mo, d = int(g[0]), int(g[1]), int(g[2])
            else:               # dd.mm.yyyy
                d, mo, y = int(g[0]), int(g[1]), int(g[2])
            # ignore invalid or old dates
            if y < 2000 or y > datetime.date.today().year + 1:
                continue
            return datetime.date(y, mo, d)
        except Exception:
            continue
    return None


def sanitize(s: str) -> str:
    s = re.sub(r'[:\\/<>|"?*\n\r]+', '', s)
    s = re.sub(r'\s{2,}', ' ', s).strip()
    return s[:120] if s else "No Subject"


def file_mod_date(path: Path) -> datetime.date:
    return datetime.date.fromtimestamp(path.stat().st_mtime)


def build_name(d: datetime.date, subj: str) -> str:
    return f"{d.strftime('%Y.%m.%d')} {sanitize(subj)}.pdf"


def fuzzy_match(text: str, pattern: str, threshold: float = 0.95) -> bool:
    """Return True if `text` and `pattern` are similar above `threshold`.

    Uses a character-based SequenceMatcher ratio. Both inputs are lower-cased
    and normalized before comparison.
    """
    if not text or not pattern:
        return False
    ratio = SequenceMatcher(None, re.sub(r'\s+', ' ', text.lower()), re.sub(r'\s+', ' ', pattern.lower())).ratio()
    return ratio >= threshold


def fuzzy_contains(text: str, pattern: str, threshold: float = 0.95) -> bool:
    """Return True if a fuzzy occurrence of `pattern` exists inside `text`.

    This token-based approach slides short n-gram windows over the tokenized
    text and compares them to the tokenized pattern using SequenceMatcher.
    """
    if not text or not pattern:
        return False
    text_tokens = re.findall(r"\w+", text.lower())
    pat_tokens = re.findall(r"\w+", pattern.lower())
    if not pat_tokens:
        return False
    p_len = len(pat_tokens)
    # try window sizes around the pattern token length (±1)
    for n in range(max(1, p_len - 1), p_len + 2):
        if n > len(text_tokens):
            break
        for i in range(0, len(text_tokens) - n + 1):
            window = " ".join(text_tokens[i : i + n])
            if SequenceMatcher(None, window, " ".join(pat_tokens)).ratio() >= threshold:
                return True
    return False


def fuzzy_find(text: str, pattern: str, threshold: float = 0.95):
    """Return the first fuzzy matching substring span for pattern inside text."""
    if not text or not pattern:
        return None
    norm_text = re.sub(r"\s+", " ", text.lower())
    norm_pattern = re.sub(r"\s+", " ", pattern.lower())
    pattern_len = len(norm_pattern)
    if pattern_len == 0:
        return None
    min_len = max(1, pattern_len - 2)
    max_len = pattern_len + 3
    for window_size in range(min_len, max_len + 1):
        for start in range(0, len(norm_text) - window_size + 1):
            window = norm_text[start : start + window_size]
            if SequenceMatcher(None, window, norm_pattern).ratio() >= threshold:
                return start, start + window_size
    return None


MONTH_NAME_MAP = {
    "januar": "01",
    "februar": "02",
    "märz": "03",
    "maerz": "03",
    "april": "04",
    "mai": "05",
    "juni": "06",
    "juli": "07",
    "august": "08",
    "september": "09",
    "oktober": "10",
    "november": "11",
    "dezember": "12",
}


def fuzzy_extract_month_year(text: str, threshold: float = 0.85):
    """Extract a month and year from text using exact and fuzzy matching."""
    if not text:
        return None

    exact = re.search(r"(januar|februar|märz|maerz|april|mai|juni|juli|august|september|oktober|november|dezember)\s*(\d{4})", text, re.I)
    if exact:
        month = MONTH_NAME_MAP[exact.group(1).lower()]
        year = int(exact.group(2))
        if 2000 <= year <= datetime.date.today().year + 1:
            return month, year

    for yr in re.finditer(r"(\d{4})", text):
        year = int(yr.group(1))
        if year < 2000 or year > datetime.date.today().year + 1:
            continue
        window_start = max(0, yr.start() - 30)
        window_end = min(len(text), yr.end() + 10)
        window = text[window_start:window_end]
        for month_name in MONTH_NAME_MAP:
            if fuzzy_find(window, month_name, threshold=threshold):
                return MONTH_NAME_MAP[month_name], year
    return None


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
