from typing import Optional, List
from pathlib import Path
from utils.common import BaseHandler, HandlerResult
from utils.matchers import fuzzy_contains, fuzzy_extract_month_year


class CanwayRechnungHandler(BaseHandler):
    def get_categories(self) -> List[str]:
        return ["Lohnabrechnungen\\2016.06.01 Canway"]

    def handle(self, text: str, path: Path) -> Optional[HandlerResult]:
        if not fuzzy_contains(text, "Abrechnung der Brutto", threshold=0.65):
            return None
        
        # if not fuzzy_contains(text, "CANWay Technology GmbH", threshold=0.65):
        #     if not fuzzy_contains(text, "48346 Ostbevern", threshold=0.65):
        #         return None

        date_parts = fuzzy_extract_month_year(text, threshold=0.85)
        if date_parts:
            month, year = date_parts
            subj = f"Abrechnung Canway {year}.{month}"
            return HandlerResult(subject=subj, date=None, subfolder="Lohnabrechnungen\\2016.06.01 Canway")

        return None


class CanwayMeldebescheinigungZurSozialversicherungHandler(BaseHandler):
    def get_categories(self) -> List[str]:
        return ["Lohnabrechnungen\\2016.06.01 Canway"]

    def handle(self, text: str, path: Path) -> Optional[HandlerResult]:
        if not fuzzy_contains(text, "Meldebescheinigung zur Sozialversicherung", threshold=0.65):
            return None
        
        # if not fuzzy_contains(text, "CANWay Technology GmbH", threshold=0.65):
        #     if not fuzzy_contains(text, "48346 Ostbevern", threshold=0.65):
        #         return None

        subj = f"Meldebescheinigung zur Sozialversicherung"
        return HandlerResult(subject=subj, date=None, subfolder="Lohnabrechnungen\\2016.06.01 Canway")
