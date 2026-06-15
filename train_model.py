import logging
import time
from utils.common import wait_if_not_debugging
from utils.model_utils import train_model, TRAIN_DATA_PATH

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    start_time = time.time()
    print(f"--- Model training started ---")
    print(f"Source: {TRAIN_DATA_PATH}")
    model = train_model()
    if model:
        end_time = time.time()
        print(f"--- Training complete! Duration: {end_time - start_time:.2f}s ---")
    else:
        print("--- Error: Training failed. ---")
    wait_if_not_debugging()