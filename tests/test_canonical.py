from __future__ import annotations

import json
import tempfile
import unittest
from datetime import timezone
from decimal import Decimal
from pathlib import Path

from business_analytics_casebook.canonical import (
    canonical_json_bytes,
    parse_timestamp,
    quantize_money,
    quantize_rate,
    read_csv,
    read_json,
    sha256_bytes,
    sha256_file,
    slugify_identifier,
    stable_float,
    stable_noise,
    write_csv,
    write_json,
)


class CanonicalTests(unittest.TestCase):
    def test_canonical_json_sorts_keys(self):
        self.assertEqual(canonical_json_bytes({"b": 1, "a": 2}), b'{"a":2,"b":1}\n')

    def test_canonical_json_serializes_decimal_as_string(self):
        self.assertEqual(canonical_json_bytes({"x": Decimal("1.20")}), b'{"x":"1.20"}\n')

    def test_sha256_bytes_stable(self):
        self.assertEqual(sha256_bytes(b"abc"), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_parse_timestamp_z(self):
        value = parse_timestamp("2026-09-01T00:00:00Z")
        self.assertEqual(value.tzinfo, timezone.utc)

    def test_parse_timestamp_offset_normalizes(self):
        value = parse_timestamp("2026-09-01T08:00:00+08:00")
        self.assertEqual(value.hour, 0)

    def test_parse_timestamp_rejects_naive(self):
        with self.assertRaises(ValueError):
            parse_timestamp("2026-09-01T00:00:00")

    def test_money_rounding(self):
        self.assertEqual(quantize_money("1.005"), Decimal("1.01"))

    def test_rate_rounding(self):
        self.assertEqual(quantize_rate("0.123456"), Decimal("0.1235"))

    def test_stable_noise_repeatable(self):
        self.assertEqual(stable_noise("same-key"), stable_noise("same-key"))

    def test_stable_noise_changes_with_key(self):
        self.assertNotEqual(stable_noise("key-a"), stable_noise("key-b"))

    def test_stable_float_rejects_infinite(self):
        with self.assertRaises(ValueError):
            stable_float(float("inf"))

    def test_slugify_identifier(self):
        self.assertEqual(slugify_identifier("Revenue By Channel"), "revenue_by_channel")

    def test_slugify_rejects_empty(self):
        with self.assertRaises(ValueError):
            slugify_identifier("---")

    def test_json_round_trip(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "x.json"
            write_json(path, {"z": 1, "a": "two"})
            self.assertEqual(read_json(path), {"a": "two", "z": 1})

    def test_csv_round_trip(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "x.csv"
            write_csv(path, [{"a": 1, "b": True}, {"a": 2, "b": False}])
            self.assertEqual(read_csv(path)[0], {"a": "1", "b": "true"})

    def test_sha256_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "x.txt"
            path.write_text("abc", encoding="utf-8")
            self.assertEqual(sha256_file(path), sha256_bytes(b"abc"))


if __name__ == "__main__":
    unittest.main()
