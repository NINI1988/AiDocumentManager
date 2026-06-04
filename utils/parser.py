from pathlib import Path
import re
from typing import Optional

from utils.common import (
    extract_text,
    build_name,
    file_mod_date,
    HandlerResult,
    Doc,
    FOLDER_REVIEW,
    FOLDER_UNSURE,
)
from handlers import HANDLERS
from utils.matchers import extract_date_from_text, normalize_text


def _fallback_handler(text: str, path: Path) -> HandlerResult:
    m = re.search(r'^(Betreff|Subject|Betr)[\s:\-–]+(.+)', text, flags=re.I | re.M)
    if m:
        subj = m.group(2).splitlines()[0].strip()
    else:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        subj = lines[0] if lines else "No Subject"

    return HandlerResult(subject=subj, date=None, subfolder="")

def _process_handlers(path: Path, txt: str) -> Optional[HandlerResult]:
    for h in HANDLERS:
        try:
            r = h.handle(txt, path)
            if r:
                return r
        except Exception:
            pass
    return None

def parse_file(path: Path) -> Doc:
    """Parse a PDF file and return Doc with target path. Does not resolve uniqueness."""
    txt = extract_text(path)
    txt = normalize_text(txt)

    handler_result = _process_handlers(path, txt)

    if handler_result:
        target = FOLDER_REVIEW / handler_result.subfolder
    else:
        handler_result = _fallback_handler(txt, path)
        target = FOLDER_UNSURE
       
    date = handler_result.date or extract_date_from_text(txt) or file_mod_date(path)
    subj = handler_result.subject
    newname = build_name(date, subj)

    return Doc(path=path, subject=subj, date=date, target=target / newname)
