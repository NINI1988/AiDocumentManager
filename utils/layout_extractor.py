import pdfplumber
from pathlib import Path
from typing import List, Dict, Any

def extract_lines_with_layout(pdf_path: Path) -> List[Dict[str, Any]]:
    """Extrahiert Zeilen mit Layout-Informationen aus den ersten 2 Seiten."""
    lines_data = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages[:2]): # Meist auf Seite 1 oder 2
                width = float(page.width)
                height = float(page.height)
                
                # Nutze extract_text_lines für strukturierte Daten
                lines = page.extract_text_lines(layout=True)
                
                for line_idx, line in enumerate(lines):
                    # Bestimme dominante Schriftgröße und Fett-Status aus den Zeichen
                    chars = line.get("chars", [])
                    avg_size = sum(c.get("size", 0) for c in chars) / len(chars) if chars else 0
                    is_bold = any("bold" in str(c.get("fontname", "")).lower() for c in chars)
                    
                    lines_data.append({
                        "text": line["text"].strip(),
                        "page_idx": page_idx,
                        "line_idx": line_idx,
                        "rel_x0": line["x0"] / width,
                        "rel_top": line["top"] / height,
                        "rel_width": (line["x1"] - line["x0"]) / width,
                        "rel_height": (line["bottom"] - line["top"]) / height,
                        "font_size": avg_size,
                        "is_bold": int(is_bold),
                        "page_width": width,
                        "page_height": height
                    })
                    
        # Berechne Abstände (Kontextmerkmale)
        for i in range(len(lines_data)):
            prev_line = lines_data[i-1] if i > 0 else None
            next_line = lines_data[i+1] if i < len(lines_data) - 1 else None
            
            lines_data[i]["dist_prev"] = lines_data[i]["rel_top"] - prev_line["rel_top"] if prev_line and prev_line["page_idx"] == lines_data[i]["page_idx"] else 1.0
            lines_data[i]["dist_next"] = next_line["rel_top"] - lines_data[i]["rel_top"] if next_line and next_line["page_idx"] == lines_data[i]["page_idx"] else 1.0
            
            # Kontextmerkmale für Text-Anker
            text_lower = lines_data[i]["text"].lower()
            lines_data[i]["is_salutation"] = int("sehr geehrte" in text_lower)
            
    except Exception as e:
        import logging
        logging.error(f"Layout-Extraktionsfehler in {pdf_path}: {e}")
        
    return lines_data