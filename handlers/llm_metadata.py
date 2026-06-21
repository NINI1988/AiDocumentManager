import logging
import datetime
from utils.common import BaseHandler, ProcessingContext
from utils.llm_extractor import extract_metadata_with_llm

class LLMMetadataHandler(BaseHandler):
    def setup(self) -> None:
        from utils.llm_extractor import get_llm

        if not get_llm():
            raise RuntimeError("Local LLM model not available.")

    def teardown(self) -> None:
        from utils.llm_extractor import unload_llm

        unload_llm()
    
    def handle(self, context: ProcessingContext) -> None:
        """
        Uses the LLM as a fallback if date or subject are still missing after other handlers.
        """
        if not context.date or not context.subject:
            llm_metadata = extract_metadata_with_llm(context.text)
            if llm_metadata:
                if not context.date:
                    d_str = llm_metadata.get("date")
                    if d_str:
                        try:
                            context.date = datetime.datetime.strptime(d_str, "%Y.%m.%d").date() # LLM-Date recognized: {context.date}
                            logging.info(f"  LLM-Date recognized: {context.date}")
                        except Exception:
                            pass
                if not context.subject:
                    llm_subject = llm_metadata.get("subject")
                    if llm_subject:
                        context.subject = llm_subject # LLM-Subject recognized: {context.subject}
                        logging.info(f"  LLM-Subject recognized: {context.subject}")
