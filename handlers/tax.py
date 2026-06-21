import shutil
import logging
from utils.config import FOLDER_REVIEW, MODE, Mode
from utils.common import BaseHandler, ProcessingContext
from utils.matchers import fuzzy_contains

class TaxHandler(BaseHandler):

    def post_process(self, context: ProcessingContext) -> None:
        """
        Checks if the file name contains 'tax' or 'steuer' and copies it to a tax folder.
        """

        # Simplified check: Name (case-insensitive) or content (fuzzy)
        filename_lower = context.input_file.name.lower()
        if any(kw in filename_lower for kw in ["tax", "steuer"]):
            tax_dest_folder = FOLDER_REVIEW / "Steuererklärung" / "neue Belege"
            tax_dest_folder.mkdir(parents=True, exist_ok=True)
            assert context.output_file is not None, "Output file must be set before post_process"
            tax_dest_path = tax_dest_folder / context.output_file.name
            logging.info(f"  [TaxHandler] Copy for tax declaration created: {tax_dest_path.name}")
            if MODE != Mode.NO_CHANGE:
                shutil.copy(str(context.output_file), str(tax_dest_path)) # Copy for tax declaration created: {tax_dest_path.name}