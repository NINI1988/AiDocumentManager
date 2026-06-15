import logging
from pydoc import text
from utils.common import BaseHandler, ProcessingContext, file_mod_date
from utils.matchers import extract_date_from_text

class FallbackHandler(BaseHandler):
    def handle(self, context: ProcessingContext) -> None:
        """
        Last resort: Sets base values if no other handler
        (or the LLM) could find information.
        """
        if not context.date:
            context.date = extract_date_from_text(context.text)
        
        if not context.date:
            context.date = file_mod_date(context.input_file)
            logging.info(f"  Fallback: Using file modification date ({context.date})")
        
        if not context.subject:
            context.confidence = 0.0
            # Fallback: Extract first line from text if subject is still missing
            lines = [l.strip() for l in context.text.split('\n') if len(l.strip()) > 3]
            if lines:
                context.subject = "".join(c for c in lines[0] if c.isalnum() or c in " -_")[:50]
                logging.info(f"  Fallback: Subject extracted from first line: '{context.subject}'")
        
        if not context.subject:
            context.subject = "Unbekannt"
            context.confidence = 0.0
            logging.info("  Fallback: Subject set to 'Unknown'")