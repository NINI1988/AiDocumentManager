import re
from typing import Optional
from pathlib import Path
from utils.common import BaseHandler, HandlerResult


class CanwayRechnungHandler(BaseHandler):
    def handle(self, text: str, path: Path) -> Optional[HandlerResult]:
        # check if subject present
        if not re.search(r"Abrechnung\s*der\s*Brutto", text, re.I):
            return None

        # try to find year and month near the phrase
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
            subj = f"Abrechnung Canway {year}.{month}"
            return HandlerResult(subject=subj, date=None, subfolder="Dokumente")

        return None

