import unittest

from utils.matchers import fuzzy_contains, fuzzy_extract_month_year


class TestFuzzyUtilities(unittest.TestCase):
    def test_fuzzy_contains_matches_broken_phrase(self):
        text = "Abrechnung derBrutto/Netto-Bezüge fürMai2026"
        self.assertTrue(fuzzy_contains(text, "Abrechnung der Brutto", threshold=0.80))

    def test_fuzzy_contains_matches_company_name(self):
        text = "CANWay technol ogyGmbH Abrechnung der Brutto"
        self.assertTrue(fuzzy_contains(text, "CANWay Technology GmbH", threshold=0.80))

    def test_fuzzy_contains_rejects_unrelated_text(self):
        text = "Rechnung nicht von Canway GmbH"
        self.assertFalse(fuzzy_contains(text, "CANWay Technology GmbH", threshold=0.80))

    def test_fuzzy_extract_month_year_exact_match(self):
        text = "Abrechnung Mai 2026"
        self.assertEqual(fuzzy_extract_month_year(text), ("05", 2026))

    def test_fuzzy_extract_month_year_no_space(self):
        text = "Abrechnung der Brutto Mai2026"
        self.assertEqual(fuzzy_extract_month_year(text), ("05", 2026))

    def test_fuzzy_extract_month_year_ocr_error(self):
        text = "Abrechnung der Brutto Maii 2026"
        self.assertEqual(fuzzy_extract_month_year(text), ("05", 2026))

    def test_fuzzy_extract_month_year_rejects_invalid_year(self):
        text = "Abrechnung Mai 1980"
        self.assertIsNone(fuzzy_extract_month_year(text))


if __name__ == "__main__":
    unittest.main()
