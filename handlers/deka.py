import re
from typing import Optional, List
from pathlib import Path
from utils.common import BaseHandler, HandlerResult
from utils.matchers import fuzzy_contains, fuzzy_extract_month_year


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
            return None

        return HandlerResult(subject=subj, date=None, subfolder="Versicherungen\\Investmentfonds Riester - Deka")
