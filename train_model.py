import logging
import time
from utils.model_utils import train_model, TRAIN_DATA_PATH

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    start_time = time.time()
    print(f"--- Modell-Training wird gestartet ---")
    print(f"Quelle: {TRAIN_DATA_PATH}")
    model = train_model()
    if model:
        end_time = time.time()
        print(f"--- Training abgeschlossen! Dauer: {end_time - start_time:.2f}s ---")
    else:
        print("--- Fehler: Training fehlgeschlagen. ---")