import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sort_inbox import process_file, get_model
from utils.common import FOLDER_INBOX

class InboxHandler(FileSystemEventHandler):
    def __init__(self):
        self.model = get_model()

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(".pdf"):
            file_path = Path(event.src_path)
            logging.info(f"Neue Datei erkannt: {file_path.name}. Warte auf Sync...")
            
            # OneDrive Sync-Verzögerung
            time.sleep(3)
            
            # Modell sicherheitshalber neu laden falls Datei gelöscht wurde (Training Update)
            self.model = get_model()
            process_file(file_path, self.model)

def start_watchdog():
    logging.info(f"Überwachung gestartet für: {FOLDER_INBOX}")
    event_handler = InboxHandler()
    observer = Observer()
    observer.schedule(event_handler, str(FOLDER_INBOX), recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    # Sicherstellen, dass die Ordner existieren
    FOLDER_INBOX.mkdir(parents=True, exist_ok=True)
    start_watchdog()