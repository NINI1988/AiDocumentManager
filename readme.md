# Ai Document Manager

All document data is handled locally.

Before using this project, adapt [`utils/config.py`](./utils/config.py) to your own folder paths, model path, and retention settings.

## Overview

- watches an `Inbox` folder for new PDFs
- Train on your local PDF folder structure and use it to sort new PDFs into the right folders.
- moves files to `Review` or `Unsure`
- Can be run as a tray service

## Setup

```powershell
pip install -r requirements.txt
```

## Local LLM

The project uses a local GGUF model. Download the GGUF file from the model page and set `LLM_MODEL_PATH` in [`utils/config.py`](./utils/config.py) to the downloaded file.
- Model page: https://huggingface.co/lmstudio-community/gemma-4-E4B-it-QAT-GGUF/tree/main
- Expected VRAM: around 6 GB for the configured setup

[Install CUDA toolchain 12.5](https://developer.nvidia.com/cuda-12-5-0-download-archive)
- Required to run the LLM model on GPU instead of falling back to CPU


## Usage

- Once or when wanted, train your local document structure: `python train_model.py`

### Manual
- Manual mode, execute: `python 1_rename.py`
- Check all documents in `Unsure` folder an move to `Review` folder
- When all documents have been reviewed in `Review` folder, execute `python 2_move_review.py` to move all your `Review` documents to the destination folder

### Background mode
- Add `pythonw watchdog_service.py` to autostart.

## Customization

- Add your own handler in `handlers/` if you need to support special handling of a document type
- Update the folder mapping and destination rules in `utils/config.py`
- `train_cache.joblib` stores cached training data so retraining can be restarted without rebuilding everything from scratch

# NAPS2 scan software

- Software Duplex = Alternatives Interleave
  - Interleave: Converts lists in the order 1,3,5,2,4,6 to 1,2,3,4,5,6.
  - Deinterleave: Converts lists in the order 1,2,3,4,5,6 to 1,3,5,2,4,6.
  - AltInterleave: Converts lists in the order 1,3,5,6,4,2 to 1,2,3,4,5,6.
  - AltDeinterleave: Converts lists in the order 1,2,3,4,5,6 to 1,3,5,6,4,2.
    
- TWAIN Feeder supports Feeder or Glass automatically 