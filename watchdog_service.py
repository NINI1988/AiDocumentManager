import time
import logging
import importlib.util
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils.common import FOLDER_INBOX
from utils.llm_extractor import get_llm, unload_llm

# Dynamischer Import für "1. rename.py" aufgrund des speziellen Dateinamens
def load_rename_script():
    script_path = Path(__file__).parent / "1. rename.py"
    spec = importlib.util.spec_from_file_location("rename_script", str(script_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

rename_script = load_rename_script()

class InboxHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(".pdf"):
            file_path = Path(event.src_path)
            logging.info(f"Neue Datei erkannt: {file_path.name}. Warte auf Sync...")
            
            # OneDrive Sync-Verzögerung abwarten
            time.sleep(3)
            
            try:
                # 1. LLM vorab laden (Singleton sorgt dafür, dass es nur einmal passiert)
                get_llm()
                
                # 2. Modelle aus dem Rename-Script beziehen
                model = rename_script.get_model()
                subject_model = rename_script.get_subject_model()
                
                # 3. Datei mit der erweiterten Logik verarbeiten
                rename_script.process_file(file_path, model, subject_model)
                
            finally:
                # 4. Prüfen, ob noch weitere PDFs in der Inbox warten
                # (Wir ignorieren die aktuelle Datei, falls MODE=Mode.NO_CHANGE aktiv ist)
                remaining = [f for f in FOLDER_INBOX.glob("*.pdf") if f.name != file_path.name]
                if not remaining:
                    unload_llm()

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