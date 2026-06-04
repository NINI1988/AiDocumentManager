import re
from typing import Optional
from pathlib import Path
from utils.common import BaseHandler, HandlerResult
from utils.matchers import fuzzy_contains, fuzzy_extract_month_year


DATE_RE = re.compile(r"datum\s*[:\-–]?\s*\d{1,2}[.]\d{1,2}[.]\d{4}", re.I)


def extract_subject_after_date(text: str) -> Optional[str]:
    lines = [line.strip() for line in text.splitlines()]
    for i, line in enumerate(lines):
        if DATE_RE.search(line):
            for next_line in lines[i + 1 :]:
                if next_line:
                    return next_line
    return None


class RentenversicherungHandler(BaseHandler):
    def handle(self, text: str, path: Path) -> Optional[HandlerResult]:
        if not fuzzy_contains(text, "Deutsche Rentenversicherung", threshold=0.65):
            return None

        subj = extract_subject_after_date(text) or "Deutsche Rentenversicherung"
        return HandlerResult(subject=subj, date=None, subfolder="Versicherungen\\Deutsche Rentenversicherung")
