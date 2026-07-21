"""Unit tests for the "top endpoint per status bucket" feature.

Covers:
  * log_parser.summarize(path)["top_endpoint_by_status"]
  * report.f4(d) / report.make(d) rendering of that data

Run from the repo root with:
    python -m unittest discover -s tests -v
"""
import os
import sys
import shutil
import tempfile
import unittest

# src/ is not a package (no __init__.py), so make its modules importable.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import log_parser  # noqa: E402
import report  # noqa: E402


def _write_log(dir_path, lines):
    """Write the given log lines to a fresh .log file and return its path."""
    fd, path = tempfile.mkstemp(suffix=".log", dir=dir_path, text=True)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


class TopEndpointByStatusTest(unittest.TestCase):
    def setUp(self):
        # A dedicated temp dir per test keeps fixtures isolated and makes
        # cleanup trivial on Windows (no open-handle reopen issues).
        self.tmpdir = tempfile.mkdtemp(prefix="logtest_")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # (a) Within a bucket, the most frequent endpoint wins.
    def test_most_frequent_endpoint_wins_in_bucket(self):
        lines = [
            "2026-07-15 09:00:00 GET /api/orders 500 120ms",
            "2026-07-15 09:00:01 GET /api/orders 503 130ms",
            "2026-07-15 09:00:02 GET /api/orders 500 140ms",
            "2026-07-15 09:00:03 GET /api/users 500 150ms",
            "2026-07-15 09:00:04 GET /api/products 200 90ms",
            "2026-07-15 09:00:05 GET /api/products 200 95ms",
        ]
        path = _write_log(self.tmpdir, lines)
        stats = log_parser.summarize(path)

        # /api/orders has three 5xx responses, more than any other path.
        self.assertEqual(
            stats["top_endpoint_by_status"]["5xx"], ("/api/orders", 3)
        )
        # Sanity: the 2xx bucket picked up /api/products (2 hits).
        self.assertEqual(
            stats["top_endpoint_by_status"]["2xx"], ("/api/products", 2)
        )

    # (b) A bucket with zero matching requests yields None.
    def test_empty_bucket_is_none(self):
        lines = [
            "2026-07-15 10:00:00 GET /api/orders 200 100ms",
            "2026-07-15 10:00:01 GET /api/login 404 110ms",
            "2026-07-15 10:00:02 POST /api/orders 500 120ms",
        ]
        path = _write_log(self.tmpdir, lines)
        stats = log_parser.summarize(path)

        tbs = stats["top_endpoint_by_status"]
        # No 3xx lines at all -> None.
        self.assertIsNone(tbs["3xx"])
        # The buckets that do have traffic are populated.
        self.assertEqual(tbs["2xx"], ("/api/orders", 1))
        self.assertEqual(tbs["4xx"], ("/api/login", 1))
        self.assertEqual(tbs["5xx"], ("/api/orders", 1))

    # (c) report rendering includes the new section, and existing sections
    #     still render (light regression check).
    def test_report_renders_new_and_existing_sections(self):
        d = {
            "total": 10,
            "2xx": 6,
            "3xx": 1,
            "4xx": 2,
            "5xx": 1,
            "avg_latency_ms": 150,
            "top_endpoints": [("/api/orders", 5), ("/api/login", 3)],
            "top_endpoint_by_status": {
                "2xx": ("/api/orders", 4),
                "3xx": None,
                "4xx": ("/api/login", 2),
                "5xx": ("/api/orders", 1),
            },
        }

        section = report.f4(d)
        self.assertIn("TOP ENDPOINT BY STATUS", section)
        # A populated bucket line and the None-bucket line both render.
        self.assertIn(" 2xx : /api/orders  (4)", section)
        self.assertIn(" 3xx : -", section)

        full = report.make(d)
        # New section is present in the full report...
        self.assertIn("TOP ENDPOINT BY STATUS", full)
        # ...and it sits between ALERTS and TOP ENDPOINTS.
        self.assertLess(full.index("ALERTS"), full.index("TOP ENDPOINT BY STATUS"))
        self.assertLess(
            full.index("TOP ENDPOINT BY STATUS"), full.index("TOP ENDPOINTS")
        )
        # Existing sections/keys still work.
        self.assertIn("DAILY TRAFFIC REPORT", full)
        self.assertIn("TOP ENDPOINTS", full)
        self.assertIn("/api/orders", full)

    # (d) Malformed / short lines are silently skipped and do not affect buckets.
    def test_short_lines_are_skipped(self):
        lines = [
            "2026-07-15 11:00:00 GET /api/orders 500 100ms",
            "garbage line too short",  # 4 fields (< 6) -> skipped
            "2026-07-15 11:00:01 GET /api/orders 500 110ms",
            "short",  # 1 field -> skipped
            "",  # blank -> skipped
        ]
        path = _write_log(self.tmpdir, lines)
        stats = log_parser.summarize(path)

        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["top_endpoint_by_status"]["5xx"], ("/api/orders", 2))
        # Skipped lines never created spurious buckets.
        self.assertIsNone(stats["top_endpoint_by_status"]["2xx"])
        self.assertIsNone(stats["top_endpoint_by_status"]["3xx"])
        self.assertIsNone(stats["top_endpoint_by_status"]["4xx"])


if __name__ == "__main__":
    unittest.main()
