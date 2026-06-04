"""Orchestrator: parse files, print table, apply operations."""

from typing import List

from utils.common import (
    print_docs_table,
    apply_file_operation,
    Doc,
    Mode,
    SCRIPT_DIR,
    INBOX_FOLDER,
    REVIEW_FOLDER,
    REVIEW_UNSURE_FOLDER,
)
from utils.parser import parse_file

# Global setting for file operation mode
MODE = Mode.NO_CHANGE


def main():
    REVIEW_FOLDER.mkdir(exist_ok=True)
    REVIEW_UNSURE_FOLDER.mkdir(exist_ok=True)
    
    if not INBOX_FOLDER.exists():
        print("Source folder not found:", INBOX_FOLDER)
        return
    
    pdfs = sorted(INBOX_FOLDER.glob("*.pdf"))
    if not pdfs:
        print("No PDFs found.")
        return

    # Phase 1: Parse all files
    print(f"Mode: '{MODE.value}'")
    print(f"Parsing {len(pdfs)} files...\n")
    docs: List[Doc] = []
    for p in pdfs:
        try:
            doc = parse_file(p)
            docs.append(doc)
        except Exception as e:
            print(f"Error parsing {p.name}: {e}")

    print_docs_table(docs, SCRIPT_DIR)

    for doc in docs:
        try:
            apply_file_operation(doc, MODE)
        except Exception as e:
            print(f"Error processing {doc.path.name}: {e}")


if __name__ == "__main__":
    main()
