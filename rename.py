# local_subject_date_rename.py
# Python 3.8+
# Comments in English. Use dataclasses. Keep functions short.

from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
import datetime
import json
import sys
from typing import Optional

# PDF lib
from PyPDF2 import PdfReader


# import ctypes

# from llama_cpp import llama_log_set

# def my_log_callback(level, message, user_data):
#     pass

# log_callback = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_char_p, ctypes.c_void_p)(my_log_callback)
# llama_log_set(log_callback, ctypes.c_void_p())

# import logging
# logging.getLogger("llama_cpp").setLevel(logging.WARNING)

# Local LLM: llama-cpp-python (wraps llama.cpp). Install:
# pip install llama-cpp-python PyPDF2
# You must download a ggml model and set MODEL_PATH below.
try:
    from llama_cpp import Llama
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False

MODEL_PATH = r"G:\Programme\LmStudio\models\hugging-quants\llama-2-7b-chat.Q4_K_M.gguf2"  # <- set your local model file here
SRC_FOLDER = Path(r"G:\scan")
DST = SRC_FOLDER / "Renamed"
DST.mkdir(exist_ok=True)

@dataclass
class Doc:
    path: Path
    subject: str
    date: datetime.date

class suppress_stdout_stderr(object):
    def __enter__(self):
        self.outnull_file = open(os.devnull, 'w')
        self.errnull_file = open(os.devnull, 'w')

        self.old_stdout_fileno_undup    = sys.stdout.fileno()
        self.old_stderr_fileno_undup    = sys.stderr.fileno()

        self.old_stdout_fileno = os.dup ( sys.stdout.fileno() )
        self.old_stderr_fileno = os.dup ( sys.stderr.fileno() )

        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr

        os.dup2 ( self.outnull_file.fileno(), self.old_stdout_fileno_undup )
        os.dup2 ( self.errnull_file.fileno(), self.old_stderr_fileno_undup )

        sys.stdout = self.outnull_file        
        sys.stderr = self.errnull_file
        return self

    def __exit__(self, *_):        
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

        os.dup2 ( self.old_stdout_fileno, self.old_stdout_fileno_undup )
        os.dup2 ( self.old_stderr_fileno, self.old_stderr_fileno_undup )

        os.close ( self.old_stdout_fileno )
        os.close ( self.old_stderr_fileno )

        self.outnull_file.close()
        self.errnull_file.close()

def extract_text(path: Path, max_pages: int = 5) -> str:
    """Extract embedded OCR/text from first pages."""
    try:
        r = PdfReader(str(path))
        pages = r.pages[:max_pages]
        texts = []
        for p in pages:
            t = p.extract_text() or ""
            texts.append(t)
        return "\n".join(texts)
    except Exception:
        return ""

def ask_local_llm(text: str, model_path: str, max_tokens: int = 4096) -> dict:
    """Ask local LLM to return JSON with subject and date (YYYY-MM-DD or null)."""
    prompt = (
        "Parse the following user text and output only a json object and no other output with the keys: "
        + "\"subject\": short title string or empty, \"date\": YYYY-MM-DD or null.\n\n"
        "### Instruction:\n" + text[:500] + "\n\n### Response:\n"  # truncate long docs
    )
    print(prompt)
    # with suppress_stdout_stderr():
    if not LLM_AVAILABLE or not Path(model_path).exists():
        return {}
    llm = Llama(model_path=model_path, n_gpu_layers=0, n_ctx=max_tokens)  #  , n_ctx=max_tokens , chat_format="llama-2"
    llm.verbose = False
    resp = llm(prompt=prompt, max_tokens=max_tokens, temperature=0.0)
    print(resp)
    out = resp.get("choices", [{}])[0].get("text", "").strip()
    print(out)
    # try to extract JSON blob
    m = re.search(r'(\{.*\})', out, flags=re.S)
    blob = m.group(1) if m else out
    try:
        # exit()
        return json.loads(blob)
    except Exception:
        return {}

def extract_date_from_text(text: str):
    """Find first plausible date, allow spaces, ignore old ones (<2000)."""
    patterns = [
        r'(\d{4})\s*[.\-/]\s*(\d{1,2})\s*[.\-/]\s*(\d{1,2})',  # yyyy.mm.dd
        r'(\d{1,2})\s*[.\-/]\s*(\d{1,2})\s*[.\-/]\s*(\d{4})'   # dd.mm.yyyy
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if not m:
            continue
        g = m.groups()
        try:
            if len(g[0]) == 4:  # yyyy.mm.dd
                y, mo, d = int(g[0]), int(g[1]), int(g[2])
            else:               # dd.mm.yyyy
                d, mo, y = int(g[0]), int(g[1]), int(g[2])
            # ignore invalid or old dates
            if y < 2000 or y > datetime.date.today().year + 1:
                continue
            return datetime.date(y, mo, d)
        except Exception:
            continue
    return None

def sanitize(s: str) -> str:
    s = re.sub(r'[:\\/<>|"?*\n\r]+', '', s)
    s = re.sub(r'\s{2,}', ' ', s).strip()
    return s[:120] if s else "No Subject"

def file_mod_date(path: Path) -> datetime.date:
    return datetime.date.fromtimestamp(path.stat().st_mtime)

def build_name(d: datetime.date, subj: str) -> str:
    return f"{d.strftime('%Y.%m.%d')} {sanitize(subj)}.pdf"

def handle_canway_rechnung(text: str) -> Optional[str]:
    # check if subject present
    if not re.search(r"Abrechnung\s*der\s*Brutto", text, re.I):
        return None

    # try to find year and month near the phrase
    # examples: "Oktober 2025", "23.10.2025", etc.
    month_map = {
        "januar": "01", "februar": "02", "märz": "03", "maerz": "03",
        "april": "04", "mai": "05", "juni": "06", "juli": "07",
        "august": "08", "september": "09", "oktober": "10",
        "november": "11", "dezember": "12"
    }

    # match month name + year
    m = re.search(r"(januar|februar|märz|maerz|april|mai|juni|juli|august|september|oktober|november|dezember)\s+(\d{4})", text, re.I)
    if m:
        month = month_map[m.group(1).lower()]
        year = m.group(2)
        return f"Abrechnung Canway {year}.{month}"

def process_file(path: Path, model_path: str) -> None:
    txt = extract_text(path)
    parsed = {}
    if LLM_AVAILABLE and Path(model_path).exists() and txt.strip():
        parsed = ask_local_llm(txt, model_path)
    subj = ""
    date = None
    if parsed:
        subj = parsed.get("subject") or ""
        dstr = parsed.get("date")
        if dstr:
            try:
                date = datetime.date.fromisoformat(dstr)
            except Exception:
                date = None

    if not subj:
        subj = handle_canway_rechnung(txt)
    
    # fallbacks
    if not subj:
        # try explicit markers
        m = re.search(r'^(Betreff|Subject|Betr)[\s:\-–]+(.+)', txt, flags=re.I | re.M)
        if m:
            subj = m.group(2).splitlines()[0].strip()
        else:
            # first meaningful line
            lines = [l.strip() for l in txt.splitlines() if l.strip()]
            subj = lines[0] if lines else "No Subject"
    if not date:
        date = extract_date_from_text(txt) or file_mod_date(path)
    doc = Doc(path=path, subject=subj, date=date)
    newname = build_name(doc.date, doc.subject)
    # target = path.with_name(newname)
    # target = DST.with_name(newname)
    target = DST / newname
    base = target.stem
    counter = 1
    while target.exists():
        target = target.with_name(f"{base} ({counter}).pdf")
        counter += 1
    shutil.move(str(path), str(target))
    # shutil.copy(str(path), str(target))
    print(f"{path.name} -> {target.name}")
    print("\n\n")

def main():
    if not SRC_FOLDER.exists():
        print("Source folder not found:", SRC_FOLDER); return
    pdfs = sorted(SRC_FOLDER.glob("*.pdf"))
    if not pdfs:
        print("No PDFs found."); return
    print("LLM available:", LLM_AVAILABLE, "| Model exists:", Path(MODEL_PATH).exists())
    for p in pdfs:
        try:
            process_file(p, MODEL_PATH)
        except Exception as e:
            print("Error processing", p.name, e)

if __name__ == "__main__":
    main()
