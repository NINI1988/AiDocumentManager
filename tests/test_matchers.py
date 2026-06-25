from utils.matchers import fuzzy_contains, fuzzy_extract_month_year


def test_fuzzy_contains_matches_broken_phrase():
    text = "Abrechnung derBrutto/Netto-Bezüge fürMai2026"
    assert fuzzy_contains(text, "Abrechnung der Brutto", threshold=0.80)


def test_fuzzy_contains_matches_company_name():
    text = "CANWay technol ogyGmbH Abrechnung der Brutto"
    assert fuzzy_contains(text, "CANWay Technology GmbH", threshold=0.80)


def test_fuzzy_contains_rejects_unrelated_text():
    text = "Rechnung nicht von Canway GmbH"
    assert not fuzzy_contains(text, "CANWay Technology GmbH", threshold=0.80)


def test_fuzzy_extract_month_year_exact_match():
    text = "Abrechnung Mai 2026"
    assert fuzzy_extract_month_year(text) == ("05", 2026)


def test_fuzzy_extract_month_year_no_space():
    text = "Abrechnung der Brutto Mai2026"
    assert fuzzy_extract_month_year(text) == ("05", 2026)


def test_fuzzy_extract_month_year_ocr_error():
    text = "Abrechnung der Brutto Maii 2026"
    assert fuzzy_extract_month_year(text) == ("05", 2026)


def test_fuzzy_extract_month_year_rejects_invalid_year():
    text = "Abrechnung Mai 1980"
    assert fuzzy_extract_month_year(text) is None
