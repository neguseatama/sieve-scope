"""
Sieve Scope v1.3 Full Regression Test Suite
- Verifies 100% backward compatibility with v0 and v1.2 engines.
- Covers IGNORED_WORDS, extract_pure_identifiers, build_pos_tuple,
  v0_mask, short-circuit execution, and extended H5-H7 states.
"""

import ast
import hashlib
import unittest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from sieve_scope import (
    SieveScopeEngineV1_3,
    IGNORED_WORDS_V0,
    extract_pure_identifiers,
    build_pos_tuple,
)


class TestSieveScopeV13Regression(unittest.TestCase):

    def setUp(self):
        self.engine = SieveScopeEngineV1_3(jaccard_threshold=0.50, freq_dice_threshold=0.60)

    def test_v0_ignored_words_compatibility(self):
        expected_words = {'print', 'len', 'range', 'sum', 'int', 'str', 'self', '__init__'}
        self.assertEqual(IGNORED_WORDS_V0, expected_words)

    def test_extract_pure_identifiers(self):
        code = "def compute_val(x, self, min_val):\n    res = len(x) + min(x)\n    print(res)\n    return res"
        extracted = extract_pure_identifiers(code)
        expected = ["compute_val", "x", "min_val", "res", "x", "min", "x", "res", "res"]  # fixed: include final return res
        self.assertEqual(extracted, expected)

    def test_v1_2_pos_tuple_compatibility(self):
        code1 = "x = a + 10"
        code2 = "y = b + 99"

        tree1 = ast.parse(code1)
        tree2 = ast.parse(code2)

        tuple1 = build_pos_tuple(tree1)
        tuple2 = build_pos_tuple(tree2)

        hash1 = hashlib.sha256(str(tuple1).encode('utf-8')).hexdigest()
        hash2 = hashlib.sha256(str(tuple2).encode('utf-8')).hexdigest()

        self.assertEqual(hash1, hash2)

    def test_short_circuit_behavior(self):
        code1 = "def add(a, b):\n    return a + b"
        code2 = "class Node:\n    def __init__(self, val):\n        self.val = val"

        res = self.engine.evaluate_pair(code1, code2)

        self.assertTrue(res["short_circuited"])
        self.assertEqual(res["v0_mask"], "1000")
        self.assertEqual(res["mask"], "1000-000")

    def test_short_regression_suite_8_cases(self):
        test_cases = [
            ("def f(x):\n    return x + 1", "def f(x):\n    return x + 1", "1110", 1),
            ("def f(x):\n    return x + 1", "def f(x):\n    return x + 2", "1110", 1),
            ("def process_data(alpha, beta):\n    res = alpha * beta\n    return res",
             "def process_data(x1, y1):\n    var_a = x1 * y1\n    return var_a", "1100", 0),  # 修正
            ("def add_val(a, b):\n    return a + b", "def sub_val(a, b):\n    return a + b", "1110", 0),
            ("def calc(a):\n    return a * 2", "class Runner:\n    def execute(self):\n        pass", "1000", 0),
            ("for i in range(10):\n    print(i)", "while True:\n    break", "1000", 0),
            ("def calc(a, b):\n    return a * b + 5",
             "def calc(a, b):\n    tmp = a * b\n    return tmp + 5", "1010", 0),
            ("class Base:\n    def run(self):\n        return 0",
             "class Base:\n    def run(self):\n        return 0", "1110", 1),
        ]

        for i, (c1, c2, expected_v0_mask, expected_h5) in enumerate(test_cases, start=1):
            with self.subTest(case_index=i):
                res = self.engine.evaluate_pair(c1, c2)
                self.assertEqual(res["v0_mask"], expected_v0_mask)
                if not res["short_circuited"]:
                    self.assertEqual(res["h_states"]["H5"], expected_h5)


if __name__ == "__main__":
    unittest.main(verbosity=2)