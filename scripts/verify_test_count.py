from __future__ import annotations

import argparse
import unittest
from pathlib import Path

EXPECTED_COUNT = 207


def count_tests(suite: unittest.TestSuite) -> int:
    return suite.countTestCases()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tests", type=Path, default=Path("tests"))
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.discover(str(args.tests))
    count = count_tests(suite)
    print(f"test_count={count} expected={EXPECTED_COUNT}")
    return 0 if count == EXPECTED_COUNT else 1


if __name__ == "__main__":
    raise SystemExit(main())
