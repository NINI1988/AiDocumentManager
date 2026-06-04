"""Orchestrator: parse files, print table, apply operations."""

from typing import List

from tqdm import tqdm

from utils.common import (
    print_docs_table,
    apply_file_operation,
    Doc,
    Mode,
    SCRIPT_DIR,
    FOLDER_INBOX,
    FOLDER_REVIEW,
    FOLDER_UNSURE,
)
from utils.parser import parse_file

# Global setting for file operation mode
MODE = Mode.NO_CHANGE


def main():
    FOLDER_REVIEW.mkdir(exist_ok=True)
    FOLDER_UNSURE.mkdir(exist_ok=True)

    if not FOLDER_INBOX.exists():
        print("Source folder not found:", FOLDER_INBOX)
        return
    
    pdfs = sorted(FOLDER_INBOX.glob("*.pdf"))
    if not pdfs:
        print("No PDFs found.")
        return

    # Phase 1: Parse all files
    print(f"Mode: '{MODE.value}'")
    print(f"Parsing {len(pdfs)} files...\n")
    docs: List[Doc] = []

    for p in tqdm(pdfs, desc="Parsing files", unit="file"):
        try:
            doc = parse_file(p)
            docs.append(doc)
        except Exception as e:
            print(f"Error parsing {p.name}: {e}")

    print()
    print_docs_table(docs, SCRIPT_DIR)

    for doc in docs:
        try:
            apply_file_operation(doc, MODE)
        except Exception as e:
            print(f"Error processing {doc.path.name}: {e}")


if __name__ == "__main__":
    main()
