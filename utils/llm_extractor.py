import json
import logging
import time
from typing import Optional, Dict, Any
import llama_cpp
from llama_cpp import Llama
from utils.config import FOLDER_PROJECT, LLM_MODEL_PATH

def _llama_log_callback(level, message, user_data):
    """Leitet interne llama.cpp-Meldungen in eine Datei um, um die Konsole sauber zu halten."""
    log_path = FOLDER_PROJECT / "llama_internal.log"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(message.decode('utf-8', errors='ignore'))

# WICHTIG: Die Python-Funktion muss in einen C-kompatiblen Callback-Typ eingepackt werden.
# Wir halten die Referenz global, damit sie nicht vom Garbage Collector entfernt wird.
_llama_log_callback_ptr = llama_cpp.llama_log_callback(_llama_log_callback)

_llm_instance = None

def get_llm():
    """Lädt das Modell nur einmalig (Singleton)."""
    global _llm_instance
    if _llm_instance is None:
        from pathlib import Path
        if not Path(LLM_MODEL_PATH).exists():
            logging.error(f"Modell-Datei nicht gefunden: {LLM_MODEL_PATH}")
            return None
        try:
            logging.info(f"Initialisiere lokales LLM: {LLM_MODEL_PATH}")
            
            # WICHTIG: Den Logger global setzen, bevor die Instanz erstellt wird.
            # Das fängt CUDA-Initialisierungsmeldungen besser ab.
            llama_cpp.llama_log_set(_llama_log_callback_ptr, None)

            _llm_instance = Llama(
                model_path=LLM_MODEL_PATH,
                n_ctx=4096,
                n_gpu_layers=-1,    # Lädt ALLE 42 Layer auf die GPU (befreit deinen RAM)
                verbose=True,       # Muss True sein beim Laden, um Windows-Redirect-Crash zu vermeiden
                n_threads=10,      # Nutzt CPU-Threads nur für das Laden/Handling
                n_batch=2048,       # Erhöht die Geschwindigkeit beim "Lesen" des Dokuments massiv
                flash_attn=True,   # Beschleunigt die Verarbeitung langer Prompts deutlich
                offload_kqv=True   # Zwingt den KV-Cache explizit in den VRAM
            )
            
            # JETZT verbose auf False setzen. Das Laden ist fertig (kein Crash mehr möglich),
            # aber wir unterdrücken so die Performance-Timings bei jeder Abfrage.
            _llm_instance.verbose = False
            
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
    # Stelle sicher, dass das LLM geladen ist, bevor wir die Zeit messen (fairer Vergleich zu LM Studio)
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

    # Wir nehmen nur den Anfang des Dokuments für die Metadaten
    doc_content = text[:4000]

    try:
        logging.info("Starte LLM-Extraktion fuer Dokumentmetadaten...")
        response = llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{doc_content}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=160
        )
        
        content = response["choices"][0]["message"]["content"]
        elapsed = time.perf_counter() - started
        logging.info("LLM-Antwort erhalten nach %.1fs: %s", elapsed, content[:200].replace("\n", " "))
        result = json.loads(content)
        
        # Validierung der Pflichtfelder
        if all(k in result for k in ["date", "subject"]):
            return result
            
    except Exception as e:
        logging.error(f"Lokale LLM Extraktion fehlgeschlagen: {e}")
            
    return None
