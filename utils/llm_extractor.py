import json
import logging
import time
from typing import Optional, Dict, Any
from llama_cpp import Llama

# Pfad zum Modell aus deiner LM Studio Bibliothek
MODEL_PATH = r"G:\Programme\LmStudio\lmstudio-community\gemma-4-12B-it-QAT-GGUF\gemma-4-12B-it-QAT-Q4_0.gguf"
# MODEL_PATH = r"G:\Programme\LmStudio\lmstudio-community\gemma-4-E4B-it-QAT-GGUF\gemma-4-E4B-it-QAT-Q4_0.gguf"
# MODEL_PATH = r"G:/Programme/LmStudio/Qwen/Qwen2.5-3B-Instruct-GGUF/qwen2.5-3b-instruct-q4_k_m.gguf"

_llm_instance = None

def get_llm():
    """Lädt das Modell nur einmalig (Singleton)."""
    global _llm_instance
    if _llm_instance is None:
        from pathlib import Path
        if not Path(MODEL_PATH).exists():
            logging.error(f"Modell-Datei nicht gefunden: {MODEL_PATH}")
            return None
        try:
            logging.info(f"Initialisiere lokales LLM: {MODEL_PATH}")
            _llm_instance = Llama(
                model_path=MODEL_PATH,
                n_ctx=4096,
                n_gpu_layers=-1,  # Erzwingt ALLE Layer in die GPU
                verbose=False,      # Wichtig für Fehlerdiagnose (CUDA/BLAS)
                n_threads=6       # Nutzt CPU-Threads nur für das Laden/Handling
            )
        except Exception as e:
            logging.error(f"Fehler beim Laden des LLM-Modells: {e}")
    return _llm_instance

def unload_llm():
    """Gibt den Speicher des LLM wieder frei (GPU/RAM)."""
    global _llm_instance
    if _llm_instance is not None:
        logging.info("Entlade lokales LLM...")
        _llm_instance = None
        import gc
        gc.collect()

def extract_metadata_with_llm(text: str) -> Optional[Dict[str, Any]]:
    """
    Nutzt das lokale LLM via llama-cpp-python zur Extraktion von Datum und Betreff.
    """
    llm = get_llm()
    if not llm:
        return None

    system_prompt = """You are a document extraction engine.

Extract:
- date (YYYY.MM.DD)
- subject (short title)
- confidence for date and subject

Rules:
- Use ONLY information from the document.
- Do NOT guess missing values.
- Output must match the schema exactly.

Structured Output:
{
  "type": "object",
  "properties": {
    "date": { "type": "string", "description": "Format YYYY.MM.DD" },
    "subject": { "type": "string" },
    "date_confidence": { "type": "number", "minimum": 0, "maximum": 130 },
    "subject_confidence": { "type": "number", "minimum": 0, "maximum": 100 }
  },
  "required": ["date", "subject", "date_confidence", "subject_confidence"]
}"""

    # Wir nehmen nur den Anfang des Dokuments für die Metadaten
    doc_content = text[:4000]

    try:
        started = time.perf_counter()
        logging.info("Starte LLM-Extraktion fuer Dokumentmetadaten...")
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Document content:\n\n{doc_content}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=300
        )
        
        content = response["choices"][0]["message"]["content"]
        elapsed = time.perf_counter() - started
        logging.info("LLM-Antwort erhalten nach %.1fs: %s", elapsed, content[:200].replace("\n", " "))
        result = json.loads(content)
        
        # Validierung der Pflichtfelder
        if all(k in result for k in ["date", "subject", "date_confidence", "subject_confidence"]):
            return result
            
    except Exception as e:
        logging.error(f"Lokale LLM Extraktion fehlgeschlagen: {e}")
            
    return None
