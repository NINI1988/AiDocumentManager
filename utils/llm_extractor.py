import contextlib
import json
import logging
import time
from typing import Optional, Dict, Any
import llama_cpp
from llama_cpp import Llama
from utils.config import FOLDER_PROJECT, LLM_MODEL_PATH

# Keep log path global to avoid recalculating it in the callback
INTERNAL_LOG_PATH = FOLDER_PROJECT / "llama_internal.log"

def _llama_log_callback(level, message, user_data):
    """Redirects internal llama.cpp messages to a file to keep the console clean."""
    with open(INTERNAL_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(message.decode('utf-8', errors='ignore'))

# IMPORTANT: The Python function must be wrapped in a C-compatible callback type.
# We keep the reference global so it is not removed by the Garbage Collector.
_llama_log_callback_ptr = llama_cpp.llama_log_callback(_llama_log_callback)

_llm_instance = None

def get_llm():
    """Loads the model only once (Singleton)."""
    global _llm_instance
    if _llm_instance is None:
        from pathlib import Path
        if not Path(LLM_MODEL_PATH).exists():
            logging.error(f"Modell-Datei nicht gefunden: {LLM_MODEL_PATH}")
            return None
        try:
            logging.info(f"Initializing local LLM: {LLM_MODEL_PATH}")
            
            # IMPORTANT: Set the logger globally before the instance is created.
            # This better catches CUDA initialization messages.
            llama_cpp.llama_log_set(_llama_log_callback_ptr, None)

            # redirect_stderr provides a valid handle for Python-level outputs 
            # during the constructor call, preventing the "No console" crash.
            with open(INTERNAL_LOG_PATH, "a", encoding="utf-8") as f:
                with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
                    _llm_instance = Llama(
                        model_path=LLM_MODEL_PATH,
                        n_ctx=4096,
                        n_gpu_layers=-1,    # Loads ALL 42 layers to the GPU (frees up your RAM)
                        verbose=True,       # Must be True during loading to avoid Windows redirect crash
                        n_threads=10,      # Uses CPU threads only for loading/handling
                        n_batch=2048,       # Massively increases the speed of "reading" the document
                        flash_attn=True,   # Significantly speeds up processing of long prompts
                        offload_kqv=True   # Explicitly forces the KV cache into VRAM
                    )
            
            # NOW set verbose to False. Loading is complete (no crash possible anymore),
            # but we suppress performance timings for each query.
            _llm_instance.verbose = False
            
        except Exception as e:
            logging.error(f"Error loading the LLM model: {e}")
    return _llm_instance

def unload_llm():
    """Frees up LLM memory (GPU/RAM)."""
    global _llm_instance
    if _llm_instance is not None:
        logging.info("Unloading local LLM...")
        _llm_instance = None
        import gc
        gc.collect()

def extract_metadata_with_llm(text: str) -> Optional[Dict[str, Any]]:
    """
    Uses the local LLM via llama-cpp-python to extract date and subject.
    """
    # Ensure the LLM is loaded before measuring time (fair comparison to LM Studio)
    llm = get_llm()
    if not llm:
        return None
    started = time.perf_counter()
    system_prompt = """You are a document extraction engine.
Extract:
- date (YYYY.MM.DD)
- subject (short title)

Rules:
- Use ONLY information from the document.
- Correct obvious OCR errors in the extracted subject (e.g. missing characters, common substitutions like "0" ↔ "O", "1" ↔ "l", broken words or spacing), but do NOT invent or infer information that is not supported by the document.
- Normalize whitespace and punctuation.
- Do NOT add or remove semantic information.
- If multiple versions of the subject exist, prefer the most complete and readable one found in the document.
- Do NOT guess missing values.
- Output must match the schema exactly.

Structured Output:
{
  "type": "object",
  "properties": {
    "date": { "type": "string", "description": "Format YYYY.MM.DD" },
    "subject": { "type": "string" },
  },
  "required": ["date", "subject"]
}"""

    # We only take the beginning of the document for metadata
    doc_content = text[:4000]

    try:
        logging.info("Starting LLM extraction for document metadata...")
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{doc_content}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=160
        )
        
        content = response["choices"][0]["message"]["content"] # LLM response received after %.1fs: %s
        elapsed = time.perf_counter() - started # LLM response received after %.1fs: %s
        logging.info("LLM response received after %.1fs: %s", elapsed, content[:200].replace("\n", " ")) # LLM response received after %.1fs: %s
        result = json.loads(content) # Validation of required fields
        
        # Validation of required fields
        if all(k in result for k in ["date", "subject"]):
            return result
            
    except Exception as e:
        logging.error(f"Local LLM extraction failed: {e}")
            
    return None
