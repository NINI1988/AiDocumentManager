import re
from difflib import SequenceMatcher
import datetime


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
    """Return True if `text` and `pattern` are similar above `threshold`."""
    if not text or not pattern:
        return False
    ratio = SequenceMatcher(None, re.sub(r"\s+", " ", text.lower()), re.sub(r"\s+", " ", pattern.lower())).ratio()
    return ratio >= threshold


def fuzzy_contains(text: str, pattern: str, threshold: float = 0.95) -> bool:
    """Return True if a fuzzy occurrence of `pattern` exists inside `text`."""
    if not text or not pattern:
        return False
    text_tokens = re.findall(r"\w+", text.lower())
    pat_tokens = re.findall(r"\w+", pattern.lower())
    if not pat_tokens:
        return False
    p_len = len(pat_tokens)
    for n in range(max(1, p_len - 1), p_len + 2):
        if n > len(text_tokens):
            break
        for i in range(0, len(text_tokens) - n + 1):
            window = " ".join(text_tokens[i : i + n])
            if SequenceMatcher(None, window, " ".join(pat_tokens)).ratio() >= threshold:
                return True
    return False


def fuzzy_find(text: str, pattern: str, threshold: float = 0.95):
    """Return the first fuzzy matching substring span for pattern inside text."""
    if not text or not pattern:
        return None
    norm_text = re.sub(r"\s+", " ", text.lower())
    norm_pattern = re.sub(r"\s+", " ", pattern.lower())
    pattern_len = len(norm_pattern)
    if pattern_len == 0:
        return None
    min_len = max(1, pattern_len - 2)
    max_len = pattern_len + 3
    for window_size in range(min_len, max_len + 1):
        for start in range(0, len(norm_text) - window_size + 1):
            window = norm_text[start : start + window_size]
            if SequenceMatcher(None, window, norm_pattern).ratio() >= threshold:
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
