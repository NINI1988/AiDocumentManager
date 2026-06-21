import logging
from pathlib import Path
from tqdm import tqdm

from handlers import HANDLERS
from utils.config import FOLDER_INBOX, FOLDER_REVIEW, FOLDER_UNSURE, LOG_FILE, MODE
from utils.processor import process_file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()]
)

def main():
    FOLDER_INBOX.mkdir(exist_ok=True)
    FOLDER_REVIEW.mkdir(exist_ok=True)
    FOLDER_UNSURE.mkdir(exist_ok=True)

    files = list(FOLDER_INBOX.glob("*.pdf"))
    if not files:
        print(f"Inbox '{FOLDER_INBOX}' is empty.")
        return

    # Phase 1: Parse all files
    print(f"Mode: '{MODE.value}'")
    print(f"Parsing {len(files)} files...\n")

    try:
        for handler in HANDLERS:
            handler.setup()
        for file_path in tqdm(files, desc="Parsing files", unit="file"):
            process_file(file_path)
    finally:
        for handler in reversed(HANDLERS):
            handler.teardown()


if __name__ == "__main__":
    main()
    # wait_if_not_debugging()
