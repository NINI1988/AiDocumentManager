# local_subject_date_rename.py
# Python 3.8+
# Comments in English. Use dataclasses. Keep functions short.

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re
import shutil
import datetime
from typing import Optional

# PDF lib
from PyPDF2 import PdfReader

class Mode(Enum):
    """File operation mode."""
    NO_CHANGE = "NO_CHANGE"
    MOVE = "MOVE"
    COPY = "COPY"

SCRIPT_DIR = Path(__file__).parent
INBOX_FOLDER = SCRIPT_DIR / "Inbox"
REVIEW_FOLDER = SCRIPT_DIR / "Review"
REVIEW_FOLDER.mkdir(exist_ok=True)
REVIEW_UNSURE_FOLDER = SCRIPT_DIR / "ReviewUnsure"
REVIEW_UNSURE_FOLDER.mkdir(exist_ok=True)

# Global setting for file operation mode
MODE = Mode.NO_CHANGE

@dataclass
class Doc:
    path: Path
    subject: str
    date: datetime.date
    target: Path

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

def handle_canway_rechnung(text: str) -> Optional[str]:
    # check if subject present
    if not re.search(r"Abrechnung\s*der\s*Brutto", text, re.I):
        return None

    # try to find year and month near the phrase
    # examples: "Oktober 2025", "23.10.2025", etc.
    month_map = {
        "januar": "01", "februar": "02", "märz": "03", "maerz": "03",
        "april": "04", "mai": "05", "juni": "06", "juli": "07",
        "august": "08", "september": "09", "oktober": "10",
        "november": "11", "dezember": "12"
    }

    # match month name + year
    m = re.search(r"(januar|februar|märz|maerz|april|mai|juni|juli|august|september|oktober|november|dezember)\s+(\d{4})", text, re.I)
    if m:
        month = month_map[m.group(1).lower()]
        year = m.group(2)
        return f"Abrechnung Canway {year}.{month}"

def parse_file(path: Path) -> Doc:
    """Parse a PDF file and return Doc with target path."""
    txt = extract_text(path)
    subj = ""
    date = None

    subj = handle_canway_rechnung(txt)
    
    # fallbacks
    if not subj:
        # try explicit markers
        m = re.search(r'^(Betreff|Subject|Betr)[\s:\-–]+(.+)', txt, flags=re.I | re.M)
        if m:
            subj = m.group(2).splitlines()[0].strip()
        else:
            # first meaningful line
            lines = [l.strip() for l in txt.splitlines() if l.strip()]
            subj = lines[0] if lines else "No Subject"
    if not date:
        date = extract_date_from_text(txt) or file_mod_date(path)
    
    newname = build_name(date, subj)
    target = REVIEW_FOLDER / "Dokumente" / newname
    base = target.stem
    counter = 1
    while target.exists():
        target = target.with_name(f"{base} ({counter}).pdf")
        counter += 1
    
    return Doc(path=path, subject=subj, date=date, target=target)

def apply_file_operation(doc: Doc) -> None:
    """Apply file operation (move/copy/no-change) based on MODE."""
    if MODE == Mode.MOVE:
        shutil.move(str(doc.path), str(doc.target))
    elif MODE == Mode.COPY:
        shutil.copy(str(doc.path), str(doc.target))
    # else: NO_CHANGE, do nothing


def print_docs_table(docs: list) -> None:
    """Print an aligned table of parsed documents (Source, Target, Mode)."""
    rows = []
    for doc in docs:
        try:
            rel = doc.target.relative_to(SCRIPT_DIR)
        except Exception:
            rel = doc.target
        rows.append((doc.path.name, str(rel)))

    if not rows:
        return

    src_col = max(len(r[0]) for r in rows)
    tgt_col = max(len(r[1]) for r in rows)
    src_col = max(src_col, len("Source"))
    tgt_col = max(tgt_col, len("Target"))
    print(f"Mode: '{MODE.value}'")
    print(f"Parsing {len(rows)} files...\n")
    print(f"{'Source':<{src_col}}  {'Target':<{tgt_col}}")
    print(f"{'-'*src_col}  {'-'*tgt_col}")
    for src, tgt in rows:
        print(f"{src:<{src_col}}  {tgt:<{tgt_col}}")
    print()

def main():
    if not INBOX_FOLDER.exists():
        print("Source folder not found:", INBOX_FOLDER); return
    pdfs = sorted(INBOX_FOLDER.glob("*.pdf"))
    if not pdfs:
        print("No PDFs found."); return
    
    # Phase 1: Parse all files
    print(f"Mode: '{MODE.value}'")
    print(f"Parsing {len(pdfs)} files...\n")
    docs = []
    for p in pdfs:
        try:
            doc = parse_file(p)
            docs.append(doc)
        except Exception as e:
            print(f"Error parsing {p.name}: {e}")

    print_docs_table(docs)

    for doc in docs:
        try:
            apply_file_operation(doc)
        except Exception as e:
            print(f"Error processing {doc.path.name}: {e}")

if __name__ == "__main__":
    main()
