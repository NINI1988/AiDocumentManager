import re
from typing import Optional


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

    return None
