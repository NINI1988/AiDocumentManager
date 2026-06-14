import re
from typing import Optional, List
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


class DekaBankHandler(BaseHandler):
    def get_subfolders(self) -> List[str]:
        return ["Versicherungen\\Investmentfonds Riester - Deka"]

    def handle(self, text: str, path: Path) -> Optional[HandlerResult]:
        # if not fuzzy_contains(text, "DekaBank", threshold=0.95):
        #     return None
        
        if "ERTRAGSAUSSCHÜTTUNG" in text:
            subj = "Ertragsausschüttung"
        elif "Quartalsbericht" in text:
            subj = "Quartalsbericht"
        else:
            subj = extract_subject_after_date(text) or "Deka Bank"
        return HandlerResult(subject=subj, date=None, subfolder="Versicherungen\\Investmentfonds Riester - Deka")
