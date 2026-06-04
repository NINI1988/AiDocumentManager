from typing import Optional
from pathlib import Path
from utils.common import BaseHandler, HandlerResult, fuzzy_contains, fuzzy_extract_month_year


class CanwayRechnungHandler(BaseHandler):
    def handle(self, text: str, path: Path) -> Optional[HandlerResult]:
        if not fuzzy_contains(text, "Abrechnung der Brutto", threshold=0.92):
            return None
        
        if not fuzzy_contains(text, "CANWay Technology GmbH", threshold=0.92):
            return None

        date_parts = fuzzy_extract_month_year(text, threshold=0.85)
        if date_parts:
            month, year = date_parts
            subj = f"Abrechnung Canway {year}.{month}"
            return HandlerResult(subject=subj, date=None, subfolder="Lohnabrechnungen\\2016.06.01 Canway")

        return None

