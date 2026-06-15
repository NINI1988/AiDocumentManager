from utils.common import BaseHandler, ProcessingContext
from utils.matchers import fuzzy_contains, fuzzy_extract_month_year


class CanwayRechnungHandler(BaseHandler):
    SUBFOLDER = "Lohnabrechnungen\\2016.06.01 Canway"

    def handle(self, context: ProcessingContext) -> None:
        if context.subfolder != self.SUBFOLDER:
            return

        if not fuzzy_contains(context.text, "Abrechnung der Brutto", threshold=0.65):
            return
        
        date_parts = fuzzy_extract_month_year(context.text, threshold=0.85)
        if date_parts:
            month, year = date_parts
            context.subject = f"Abrechnung Canway {year}.{month}"


class CanwayMeldebescheinigungZurSozialversicherungHandler(BaseHandler):
    SUBFOLDER = "Lohnabrechnungen\\2016.06.01 Canway"

    def handle(self, context: ProcessingContext) -> None:
        if context.subfolder != self.SUBFOLDER:
            return

        if not fuzzy_contains(context.text, "Meldebescheinigung zur Sozialversicherung", threshold=0.65):
            return
        
        context.subject = "Meldebescheinigung zur Sozialversicherung"
