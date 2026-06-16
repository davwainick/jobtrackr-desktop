"""Tests for CSV export generation."""

import csv
import io
import unittest

from export.csv_export import generate_csv


def _parse(text: str) -> tuple[list[str], list[list[str]]]:
    rows = list(csv.reader(io.StringIO(text)))
    return rows[0], rows[1:]


class GenerateCsvTests(unittest.TestCase):
    def test_empty_rows_returns_empty_string(self) -> None:
        self.assertEqual(generate_csv([]), "")

    def test_headers_use_human_readable_map(self) -> None:
        header, _ = _parse(generate_csv([{"company_name": "Acme", "tier": "Tier 1"}]))
        self.assertEqual(header, ["Company Name", "Tier"])

    def test_unknown_key_falls_back_to_raw_name(self) -> None:
        header, _ = _parse(generate_csv([{"mystery_field": "x"}]))
        self.assertEqual(header, ["mystery_field"])

    def test_boolean_integers_render_as_yes_no(self) -> None:
        _, body = _parse(generate_csv([{"open_role": 1, "warm_intro_available": 0}]))
        self.assertEqual(body[0], ["Yes", "No"])

    def test_none_renders_as_empty_cell(self) -> None:
        _, body = _parse(generate_csv([{"company_name": None}]))
        self.assertEqual(body[0], [""])

    def test_plain_text_passthrough(self) -> None:
        _, body = _parse(generate_csv([{"company_name": "Acme", "notes": "hello, world"}]))
        # csv module handles quoting of the embedded comma on round-trip.
        self.assertEqual(body[0], ["Acme", "hello, world"])


if __name__ == "__main__":
    unittest.main()
