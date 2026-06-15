import time
import logging
import multiprocessing
import threading
import sys
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Tuple

import pystray
from PIL import Image, ImageDraw
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from utils.config import FOLDER_INBOX, FOLDER_REVIEW, FOLDER_UNSURE, LOG_FILE
from utils.config import ERROR_PAUSE_SECONDS
# Sets the logging level to DEBUG to get more detailed information
logging.basicConfig(level=logging.INFO, filename=LOG_FILE, format="%(asctime)s %(message)s")

class ServiceState(Enum):
    IDLE = "Idle"
    PROCESSING = "Processing"
    PAUSED = "Paused"
    ERROR = "Error Pause"

def process_files_worker(files: list, queue: multiprocessing.Queue, error_queue: multiprocessing.Queue, stop_event: multiprocessing.Event):
    """Separate process for LLM processing to isolate CUDA crashes."""
    try:
        # Re-Importe innerhalb des Kindprozesses für Windows 'spawn'
        import logging
        from utils.llm_extractor import get_llm, unload_llm
        from utils.processor import process_file

        try:
            get_llm()  # Pre-load LLM to initialize CUDA/GPU memory before processing
            for i, f in enumerate(files, 1):
                if stop_event.is_set():
                    break
                process_file(f)
                queue.put(i)  # Fortschritt an Hauptprozess melden
        except Exception as e:
            error_queue.put(str(e))
            sys.exit(1)
    finally:
        unload_llm()

class WatchdogService:
    def __init__(self) -> None:
        self.state: ServiceState = ServiceState.IDLE
        self.processed_count: int = 0
        self.error_message: Optional[str] = None
        self.error_pause_until: Optional[datetime] = None
        self.is_paused: bool = False
        self.running: bool = True
        self.last_change_time: float = 0.0
        self.stop_event = multiprocessing.Event()
        
        # Check if files already exist and initialize timer
        existing_files = list(FOLDER_INBOX.glob("*.pdf"))
        if existing_files:
            # Set timer to current time for 5s wait (stability check)
            self.last_change_time = time.time()
            logging.info(f"Startup check: {len(existing_files)} files found. Waiting for stability...")

        # Initialize Tray Icon
        self.icon = pystray.Icon("AiDocumentManager", self.generate_icon(ServiceState.IDLE),
                                 title="Ai Document Manager", menu=self.create_menu())
        # Immediate UI refresh based on initial status
        self.update_ui(ServiceState.IDLE)

    def generate_icon(self, state: ServiceState) -> Image.Image: # Immediate UI refresh based on initial status
        # Create a transparent background
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        
        # Draw Document Body (Base Icon)
        d.rectangle([12, 4, 52, 60], fill="white", outline="black", width=2)
        # Folded corner effect (top right)
        d.polygon([(40, 4), (52, 4), (52, 16)], fill="lightgray", outline="black")
        
        # Draw some lines to represent text on the document
        for i in range(22, 55, 8):
            d.line([20, i, 44, i], fill="gray", width=2)

        # Status Overlays in the bottom right corner # Relatively large (32x32 on 64x64 canvas) for good visibility
        # Relatively large (32x32 on 64x64 canvas) for good visibility
        overlay_size = 32 
        overlay_x = 64 - overlay_size 
        overlay_y = 64 - overlay_size

        if state == ServiceState.PROCESSING:
            # Blue circle for processing # Static "loading" arc
            d.ellipse([overlay_x, overlay_y, overlay_x + overlay_size, overlay_y + overlay_size], 
                      fill=(0, 120, 215), outline="white", width=2)
            # Static "loading" arc # Yellow square for better visibility of the pause
            d.arc([overlay_x + 3, overlay_y + 3, overlay_x + overlay_size - 3, overlay_y + overlay_size - 3], 
                  start=0, end=270, fill="white", width=4)
        elif state == ServiceState.PAUSED:
            # Yellow square for better visibility of the pause # Black vertical bars for maximum contrast
            d.rectangle([overlay_x, overlay_y, overlay_x + overlay_size, overlay_y + overlay_size], 
                        fill="yellow", outline="black", width=1)
            # Black vertical bars for maximum contrast # Red circle with an X
            bar_width = 6
            bar_height = 18
            bar_spacing = 4
            total_bars_width = (bar_width * 2) + bar_spacing
            start_x_bars = overlay_x + (overlay_size - total_bars_width) // 2
            start_y_bars = overlay_y + (overlay_size - bar_height) // 2

            d.rectangle([start_x_bars, start_y_bars, start_x_bars + bar_width, start_y_bars + bar_height], fill="black")
            d.rectangle([start_x_bars + bar_width + bar_spacing, start_y_bars, start_x_bars + bar_width + bar_spacing + bar_width, start_y_bars + bar_height], fill="black")
        elif state == ServiceState.ERROR:
            # Red circle with an X # Give UI a moment to update
            d.ellipse([overlay_x, overlay_y, overlay_x + overlay_size, overlay_y + overlay_size], 
                      fill="red", outline="white", width=2)
            d.line([overlay_x + 6, overlay_y + 6, overlay_x + overlay_size - 6, overlay_y + overlay_size - 6], fill="white", width=4)
            d.line([overlay_x + overlay_size - 6, overlay_y + 6, overlay_x + 6, overlay_y + overlay_size - 6], fill="white", width=4)
            
        return img

    def create_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(lambda item: "Resume" if (self.is_paused or self.error_pause_until) else "Pause", self.toggle_pause),
            pystray.MenuItem("Exit", self.stop_service)
        )

    def toggle_pause(self) -> None:
        if self.error_pause_until:
            # Special case: Direct resume from error state
            self.error_pause_until = None
            self.error_message = None
            self.is_paused = False
            self.stop_event.clear()
            logging.info("Manual resume from error state.")
        else:
            self.is_paused = not self.is_paused
        if self.is_paused:
            logging.info("Service paused.")
            self.stop_event.set()  # Signal to worker: Stop after current file
        else:
            self.stop_event.clear() # Reset signal for next run
            # If files are waiting, restart stability timer
            if list(FOLDER_INBOX.glob("*.pdf")):
                self.last_change_time = time.time()
                logging.info("Stability timer reset on manual resume (files in inbox).")
            logging.info("Service resumed.")
        self.update_ui(ServiceState.PAUSED if self.is_paused else ServiceState.IDLE)
    def stop_service(self) -> None:
        self.running = False
        self.stop_event.set()  # Signal to worker: Stop immediately after the current file
        self.icon.stop()

    def update_ui(self, state: ServiceState, progress: Optional[Tuple[int, int]] = None) -> None:
        logging.debug(f"Updating UI to state: {state.value}")
        self.icon.icon = self.generate_icon(state)
        
        inbox_files = len(list(FOLDER_INBOX.glob("*.pdf")))
        review_files = len(list(FOLDER_REVIEW.rglob("*.pdf")))
        unsure_files = len(list(FOLDER_UNSURE.rglob("*.pdf")))

        # Line 1: Status & Timer
        status_text = state.value
        if state == ServiceState.ERROR and self.error_pause_until:
            remaining = self.error_pause_until - datetime.now()
            secs = max(0, int(remaining.total_seconds()))
            status_text += f" ({secs}s)"
        line1 = f"Ai Doc Manager: {status_text}"
        # Line 2: Progress, Review and Unsure (Fully visible)
        # Line 2: Progress, Review and Unsure (Fully visible)
        if progress:
            progress_text = f"{progress[0]}/{progress[1]} files"
        else:
            progress_text = f"{inbox_files} files"
        line2 = f"{progress_text} | Review: {review_files} | Unsure: {unsure_files}"

        # Line 3: Full path
        line3 = f"Folder: {FOLDER_INBOX}"

        # Combine and observe Windows limit (128 characters)
        full_msg = f"{line1}\n{line2}\n{line3}"
        if len(full_msg) > 127:
            # If the path is extremely long, we only shorten the path line
            available = 127 - len(line1) - len(line2) - 10
            if available > 10:
                line3 = line3[:available] + "..."
            full_msg = f"{line1}\n{line2}\n{line3}"

        # Last safeguard against ValueError
        self.icon.title = full_msg[:127]

        # ONLY update menu if status has changed # This prevents entries from disappearing with second-by-second updates
        # This prevents entries from disappearing with second-by-second updates
        if state != self.state:
            self.icon.menu = self.create_menu()
        
        self.state = state

    def process_queue(self) -> None:
        while self.running:
            time.sleep(1)
            logging.debug(f"Process queue loop: is_paused={self.is_paused}, error_pause_until={self.error_pause_until}, last_change_time={self.last_change_time}")
            if self.is_paused: continue
            # Check Error Pause
            if self.error_pause_until:
                logging.debug("In error pause state.")
                if datetime.now() < self.error_pause_until:
                    # Update UI for the countdown in the tooltip
                    self.update_ui(ServiceState.ERROR)
                    continue
                else:
                    self.error_pause_until = None
                    self.error_message = None
                    if list(FOLDER_INBOX.glob("*.pdf")):
                        self.last_change_time = time.time()
                    self.update_ui(ServiceState.IDLE)

            # Stability check: 5 seconds since last change
            logging.debug(f"Stability check: time.time() - self.last_change_time = {time.time() - self.last_change_time}") # Stability check: 5 seconds since last change
            if self.last_change_time > 0 and (time.time() - self.last_change_time) > 5:
                files = list(FOLDER_INBOX.glob("*.pdf"))
                logging.debug(f"Stability check passed. Files in inbox: {len(files)}")
                if not files:
                    self.last_change_time = 0
                    continue

                total_files = len(files)
                last_done = 0
                if not self.is_paused:
                    logging.info(f"Starting processing of {total_files} files.")
                    self.update_ui(ServiceState.PROCESSING, progress=(0, total_files))
                # Create a queue for progress and start the subprocess
                try:
                    self.stop_event.clear()
                    # Create a queue for progress and start the subprocess
                    queue = multiprocessing.Queue()
                    error_queue = multiprocessing.Queue()
                    p = multiprocessing.Process(target=process_files_worker, args=(files, queue, error_queue, self.stop_event))
                    p.start()
                    # Monitor the process while it is running
                    while p.is_alive():
                        while not queue.empty():
                            last_done = queue.get()
                            # Only update UI if we haven't just clicked pause
                            if not self.is_paused:
                                self.update_ui(ServiceState.PROCESSING, progress=(last_done, total_files))
                        time.sleep(0.5)
                    p.join()
                    
                    # Exit code 0 is a normal exit, everything else (if not manually stopped) is a crash
                    if p.exitcode != 0 and not self.stop_event.is_set():
                        subprocess_err = None
                        if not error_queue.empty():
                            subprocess_err = error_queue.get()
                        
                        err_msg = subprocess_err or f"KI-Prozess abgestürzt (Exitcode {p.exitcode}). Wahrscheinlich CUDA-Fehler."
                        raise RuntimeError(err_msg)

                    self.processed_count += last_done
                    self.last_change_time = 0
                    if not self.is_paused:
                        self.update_ui(ServiceState.IDLE)
                except Exception as e:
                    logging.error(f"Watchdog Error: {e}")
                    self.error_message = str(e)
                    self.error_pause_until = datetime.now() + timedelta(seconds=ERROR_PAUSE_SECONDS)
                    self.update_ui(ServiceState.ERROR)
                    time.sleep(0.1)

class InboxHandler(FileSystemEventHandler):
    def __init__(self, service: WatchdogService) -> None:
        self.service = service

    def on_any_event(self, event: FileSystemEvent) -> None:
        if not event.is_directory and event.src_path.lower().endswith(".pdf"):
            self.service.last_change_time = time.time()
            # Tooltip sofort aktualisieren, um neue Datei in Inbox anzuzeigen
            self.service.update_ui(self.service.state)


def start_watchdog() -> None:
    multiprocessing.freeze_support() # Important for Windows
    FOLDER_INBOX.mkdir(parents=True, exist_ok=True)
    
    service = WatchdogService()
    handler = InboxHandler(service)
    observer = Observer()
    observer.schedule(handler, str(FOLDER_INBOX), recursive=False)
    observer.start()
    # Start processing thread
    # Run Icon (Blocks main thread)
    threading.Thread(target=service.process_queue, daemon=True).start()
    
    service.icon.run()
    
    observer.stop()
    observer.join()

if __name__ == "__main__":
    start_watchdog()