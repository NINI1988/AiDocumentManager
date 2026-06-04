from pathlib import Path
import re
import datetime
from typing import List, Tuple

# PDF lib
from PyPDF2 import PdfReader


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


def apply_file_operation(doc, mode) -> None:
    """Apply file operation (move/copy/no-change) for a Doc using the provided mode.

    The mode may be an Enum with a `value` attribute or a plain string.
    """
    import shutil

    mval = getattr(mode, 'value', mode)
    if mval == 'MOVE' or mval == 'move' or mval == 'MOVE':
        shutil.move(str(doc.path), str(doc.target))
    elif mval == 'COPY' or mval == 'copy':
        shutil.copy(str(doc.path), str(doc.target))
    # else: NO_CHANGE, do nothing
