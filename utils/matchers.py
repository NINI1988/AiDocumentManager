import re
import datetime

from rapidfuzz import fuzz


def normalize_text(text: str) -> str:
    return " ".join(re.findall(r"\w+", (text or "").lower()))


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


MONTH_NAME_MAP = {
    "januar": "01",
    "februar": "02",
    "märz": "03",
    "maerz": "03",
    "april": "04",
    "mai": "05",
    "juni": "06",
    "juli": "07",
    "august": "08",
    "september": "09",
    "oktober": "10",
    "november": "11",
    "dezember": "12",
}


def fuzzy_match(text: str, pattern: str, threshold: float = 0.95) -> bool:
    """Return True if `text` and `pattern` are similar above `threshold`.

    vergleicht zwei Strings als Ganzes
    sinnvoll, wenn beide Texte in etwa gleich lang sind
    Beispiel: vollständige Dokumentüberschrift vs. Referenztext
    """
    if not text or not pattern:
        return False
    norm_text = normalize_text(text)
    norm_pattern = normalize_text(pattern)
    return fuzz.ratio(norm_pattern, norm_text, score_cutoff=int(threshold * 100)) >= int(threshold * 100)


def fuzzy_contains(text: str, pattern: str, threshold: float = 0.95) -> bool:
    """Return True if a fuzzy occurrence of `pattern` exists inside `text`.

    sucht den besten Teilabgleich zwischen den Strings
    ideal, wenn ein kürzeres Muster in einem längeren, verrauschten Text vorkommt
    """
    if not text or not pattern:
        return False
    norm_text = normalize_text(text)
    norm_pattern = normalize_text(pattern)
    threshold_100 = threshold * 100
    ratio = fuzz.partial_ratio(norm_pattern, norm_text, score_cutoff=threshold_100)
    return ratio >= threshold_100


def fuzzy_find(text: str, pattern: str, threshold: float = 0.95):
    """Return the first fuzzy matching substring span for pattern inside text."""
    if not text or not pattern:
        return None
    norm_text = normalize_text(text)
    norm_pattern = normalize_text(pattern)
    pattern_len = len(norm_pattern)
    if pattern_len == 0:
        return None
    score_cutoff = int(threshold * 100)
    min_len = max(1, pattern_len - 2)
    max_len = pattern_len + 3
    for window_size in range(min_len, max_len + 1):
        for start in range(0, len(norm_text) - window_size + 1):
            window = norm_text[start : start + window_size]
            if fuzz.ratio(window, norm_pattern, score_cutoff=score_cutoff) >= score_cutoff:
                return start, start + window_size
    return None


def fuzzy_extract_month_year(text: str, threshold: float = 0.85):
    """Extract a month and year from text using exact and fuzzy matching."""
    if not text:
        return None

    exact = re.search(r"(januar|februar|märz|maerz|april|mai|juni|juli|august|september|oktober|november|dezember)\s*(\d{4})", text, re.I)
    if exact:
        month = MONTH_NAME_MAP[exact.group(1).lower()]
        year = int(exact.group(2))
        if 2000 <= year <= datetime.date.today().year + 1:
            return month, year

    for yr in re.finditer(r"(\d{4})", text):
        year = int(yr.group(1))
        if year < 2000 or year > datetime.date.today().year + 1:
            continue
        window_start = max(0, yr.start() - 30)
        window_end = min(len(text), yr.end() + 10)
        window = text[window_start:window_end]
        for month_name in MONTH_NAME_MAP:
            if fuzzy_find(window, month_name, threshold=threshold):
                return MONTH_NAME_MAP[month_name], year
    return None
