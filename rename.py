# local_subject_date_rename.py
# Python 3.8+
# Comments in English. Use dataclasses. Keep functions short.

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re
import datetime

# local utils and handlers
from utils.common import (
    extract_text,
    extract_date_from_text,
    build_name,
    file_mod_date,
    print_docs_table,
    unique_path,
    apply_file_operation,
)
from handlers.canway import handle_canway_rechnung

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

def parse_file(path: Path) -> Doc:
    """Parse a PDF file and return Doc with target path."""
    txt = extract_text(path)
    subj = ""
    date = None

    # first, let handlers try to recognize/produce a subject
    handler_subj = handle_canway_rechnung(txt)
    if handler_subj:
        subj = handler_subj

    # fallbacks (subject extraction) if handler didn't set it
    if not subj:
        # try explicit markers
        m = re.search(r'^(Betreff|Subject|Betr)[\s:\-–]+(.+)', txt, flags=re.I | re.M)
        if m:
            subj = m.group(2).splitlines()[0].strip()
        else:
            # first meaningful line
            lines = [l.strip() for l in txt.splitlines() if l.strip()]
            subj = lines[0] if lines else "No Subject"

    # determine date
    if not date:
        date = extract_date_from_text(txt) or file_mod_date(path)

    # If a handler matched, put in Review/Dokumente and rename; otherwise put into ReviewUnsure keeping original name
    if handler_subj:
        newname = build_name(date, subj)
        target = unique_path(REVIEW_FOLDER / "Dokumente" / newname)
    else:
        # use fallback rename into ReviewUnsure (keep consistent naming, avoid overwrites)
        newname = build_name(date, subj)
        target = unique_path(REVIEW_UNSURE_FOLDER / newname)

    return Doc(path=path, subject=subj, date=date, target=target)

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

    print_docs_table(docs, SCRIPT_DIR)

    for doc in docs:
        try:
            apply_file_operation(doc, MODE)
        except Exception as e:
            print(f"Error processing {doc.path.name}: {e}")

if __name__ == "__main__":
    main()
