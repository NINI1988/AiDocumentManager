from utils.common import BaseHandler, ProcessingContext


class DekaBankHandler(BaseHandler):
    SUBFOLDER = "Versicherungen\\Investmentfonds Riester - Deka"

    def handle(self, context: ProcessingContext) -> None:
        if context.subfolder != self.SUBFOLDER:
            return
        
        text = context.text
        if "ERTRAGSAUSSCHÜTTUNG" in text:
            subj = "Ertragsausschüttung"
        elif "Quartalsbericht" in text:
            subj = "Quartalsbericht"
        else:
            return

        context.subject = subj
