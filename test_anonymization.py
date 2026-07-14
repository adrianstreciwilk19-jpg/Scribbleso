import unittest

from Scribbleso import ScribblesoApp


class DateAnonymizationTests(unittest.TestCase):
    def setUp(self):
        self.app = ScribblesoApp.__new__(ScribblesoApp)

    def anonymize(self, text):
        return self.app._anonymize_sections([("default", text)])[0][1]

    def test_common_date_formats_are_not_anonymized(self):
        dates = (
            "20260501",
            "01052026",
            "260501",
            "010526",
            "2026-05-01",
            "01-05-2026",
            "05/01/2026",
            "2026.5.1",
            "2026_05_01",
            "1.5.2026",
            "2026 05 01",
            "01 05 2026",
            "14.07",
            "2026/07",
            "07/2026",
            r"2026\05\01",
            "1 maja 2026",
            "1-go maja 2026 r.",
            "14 lipca",
            "July 14, 2026",
            "14th July 2026",
            "Jul-14-2026",
            "lipiec 2026",
            "2026 July",
            "2026 July 14",
            "14 VII 2026",
            "2026-W18-5",
            "2026W185",
            "2026-121",
            "2026121",
            "2024-02-29",
            "29.02.2024",
            "2026-05-01T12:30:45Z",
            "2026-05-01 9:05",
            "01.05.2026 23:59:59+02:00",
            "20260501T123045+0200",
        )

        for date in dates:
            with self.subTest(date=date):
                self.assertEqual(self.anonymize(date), date)

    def test_invalid_dates_are_still_anonymized(self):
        values = (
            "2026-02-30",
            "31/13/2026",
            "2023-02-29",
            "12345678",
        )

        for value in values:
            with self.subTest(value=value):
                self.assertNotEqual(self.anonymize(value), value)

    def test_date_is_preserved_next_to_regular_identifier(self):
        result = self.anonymize("Termin 2026-05-01, numer 12345678")

        self.assertIn("2026-05-01", result)
        self.assertNotIn("12345678", result)
        self.assertIn("[ID_1]", result)


if __name__ == "__main__":
    unittest.main()
