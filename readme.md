# Ai Document Manager

Local document sorting, renaming, and review for scanned PDFs.

All document data stays on your machine. Before using the project, update [`utils/config.py`](./utils/config.py) with your folder paths, destination root, and local model path.

## Overview

- watches an `Inbox` folder for new PDFs
- classifies PDFs into your existing folder structure
- renames documents with a local LLM using date and subject
- routes uncertain files to `Unsure` and review-ready files to `Review`
- can run as a tray service in the background

## Requirements

- Python dependencies from [`requirements.txt`](./requirements.txt)
- a local GGUF model for the LLM step
- optional GPU support if you want faster inference

## Setup

```sh
pip install -r requirements.txt
```

## Configure

Edit [`utils/config.py`](./utils/config.py) before running the scripts.

Key settings:

- `FOLDER_INBOX`: input folder containing new PDFs
- `FOLDER_REVIEW`: staging folder for files that need review
- `FOLDER_UNSURE`: staging folder for files that could not be classified confidently
- `DEST_ROOT`: final destination root for reviewed documents
- `MODE`: controls whether processing moves, copies, or leaves files unchanged
- `LLM_MODEL_PATH`: path to the local GGUF model
- `UNSURE_THRESHOLD`: confidence threshold for auto-classification

The current setup expects a local model such as:

- https://huggingface.co/lmstudio-community/gemma-4-E4B-it-QAT-GGUF/tree/main
  - Expected VRAM: around 6 GB for the configured setup

The repository is configured for GPU inference through `llama-cpp-python` with CUDA 12.5. If GPU support is not available, the model can still run on CPU, but it will be slower.
  - [Install CUDA toolchain 12.5](https://developer.nvidia.com/cuda-12-5-0-download-archive)
  - Required to run the LLM model on GPU instead of falling back to CPU

## Usage

Train the classifier on your destination structure:

```sh
python train_model.py
```

### Manual

1. Process files from the inbox:

```sh
python 1_rename.py
```

2. Review files that were moved to `Unsure` and `Review`.

3. Move reviewed documents into the final destination tree:

```sh
python 2_move_review.py
```

### Background Mode

Run the tray service with:

```sh
pythonw watchdog_service.py
```

Add that command to startup if you want it to run automatically.

## Project Files

- `train_model.py` builds or refreshes the local classifier
- `1_rename.py` processes the inbox and classifies files
- `2_move_review.py` moves reviewed files into `DEST_ROOT`
- `watchdog_service.py` runs the tray-based background watcher
- `train_cache.joblib` stores cached training data
- `classifier_model_word.pkl` stores the trained model
- `log.txt` captures runtime logs

## Customization

- add special-case handlers in `handlers/`
- update folder mappings and thresholds in `utils/config.py`
- change `MODE` to test without moving files

## Scanner Notes for NAPS2

These are kept here because they are useful to the scanning workflow, but they are not part of the main app logic.

- `Software Duplex = Alternatives Interleave`
  - `Interleave`: converts `1,3,5,2,4,6` to `1,2,3,4,5,6`
  - `Deinterleave`: converts `1,2,3,4,5,6` to `1,3,5,2,4,6`
  - `AltInterleave`: converts `1,3,5,6,4,2` to `1,2,3,4,5,6`
  - `AltDeinterleave`: converts `1,2,3,4,5,6` to `1,3,5,6,4,2`
- `TWAIN Feeder` supports feeder or glass automatically
