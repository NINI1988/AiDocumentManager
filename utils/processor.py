import logging
from pathlib import Path
from handlers import HANDLERS
from utils.config import FOLDER_REVIEW, FOLDER_UNSURE, UNSURE_THRESHOLD
from utils.common import (
    ProcessingContext,
    extract_pdf_content, build_name, apply_file_operation
)

def process_file(file_path: Path):
    """Classifies and moves a single file using handlers."""
    if not file_path.suffix.lower() == ".pdf":
        return

    logging.info(f"Processing file: {file_path.name}")
    
    # 1. Extract text
    text, _ = extract_pdf_content(file_path)

    # 2. Initialize context
    context = ProcessingContext(
        input_file=file_path,
        subfolder="", 
        text=text or "",
        date=None,
        subject=None,
        confidence=0.0,
    )

    # 4. Handler Pre-processing (All handlers are called, they filter themselves)
    for h in HANDLERS:
        h.handle(context)

    # Build target path and determine base folder based on confidence
    assert context.date is not None, "Date must be set before building name"
    assert context.subject is not None, "Subject must be set before building name"
    new_name = build_name(context.date, context.subject)

    # Route to Unsure if the ML confidence is below the threshold
    target_base = FOLDER_REVIEW if context.confidence >= UNSURE_THRESHOLD else FOLDER_UNSURE
    context.output_file = target_base / context.subfolder / new_name
    
    # 6. Move/copy file
    logging.info(f"  Action: '{file_path.name}' -> '{context.output_file.relative_to(target_base.parent)}'")
    apply_file_operation(context)
    
    # 7. Handler Post-processing
    for h in HANDLERS:
        h.post_process(context)
