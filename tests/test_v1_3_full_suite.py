"""
Sieve Scope v1.3 Full 24-Case Strict Regression Test Suite

The suite contains 24 canonical pair cases:
- Basic: 6
- Boundary: 8
- 4-Quadrant: 6
- Q3 Deep Dive: 4

Expected masks below reflect the current v1.3 implementation semantics.
In particular:
- H5/g_POS is based on the current build_pos_tuple() implementation.
- H7 uses the configured weighted bi-gram Dice threshold (>= 0.60).
- The H2=0/H3=1 cases must not be treated as short-circuit cases.
"""

import unittest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from sieve_scope import SieveScopeEngineV1_3


class TestSieveScopeV13FullSuite(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = SieveScopeEngineV1_3(
            jaccard_threshold=0.50,
            freq_dice_threshold=0.60,
        )

    def _assert_case(self, group, idx, c1, c2, exp_v0, exp_mask):
        with self.subTest(group=group, case_idx=idx):
            res = self.engine.evaluate_pair(c1, c2)
            self.assertEqual(
                res["v0_mask"], exp_v0,
                f"{group} Case {idx} v0_mask mismatch",
            )
            self.assertEqual(
                res["mask"], exp_mask,
                f"{group} Case {idx} full mask mismatch",
            )

    # -----------------------------------------------------------------
    # Group 1: Basic 6
    # -----------------------------------------------------------------
    def test_group1_basic_cases(self):
        cases = [
            (
                "def add(a, b):\n    return a + b",
                "def add(a, b):\n    return a + b",
                "1110", "1110-111",
            ),
            (
                "def check(x):\n    return x > 100",
                "def check(x):\n    return x > 200",
                "1110", "1110-101",
            ),
            (
                "def compute_sum(first_num, second_num):\n"
                "    total_val = first_num + second_num\n"
                "    return total_val",
                "def compute_sum(param_x, param_y):\n"
                "    temp_out = param_x + param_y\n"
                "    return temp_out",
                "1100", "1100-010",
            ),
            (
                "def process_data(a, b):\n    return a + b",
                "def execute_data(a, b):\n    return a + b",
                "1110", "1110-011",
            ),
            (
                "def process(x, y):\n    return x * y + 10",
                "def process(x, y):\n    temp = x * y\n    return temp + 10",
                "1010", "1010-011",
            ),
            (
                "def add(a, b):\n    return a + b",
                "class Node:\n    def __init__(self, val):\n        self.val = val",
                "1000", "1000-000",
            ),
        ]

        for i, case in enumerate(cases, 1):
            self._assert_case("Basic", i, *case)

    # -----------------------------------------------------------------
    # Group 2: Boundary 8
    # -----------------------------------------------------------------
    def test_group2_boundary_cases(self):
        cases = [
            (
                "def f(x):\n    return x + 1",
                "def f(x):\n\n    return   x + 1\n",
                "1110", "1110-111",
            ),
            # Comments only
            (
                "# Comment 1\ndef f(x):\n    # body comment\n    return x + 1",
                "# Comment 2\ndef f(x):\n    # another comment\n    return x + 1",
                "1110", "1110-111",
            ),
            (
                "def add(a, b):\n    return a + b",
                "def add(a, b):\n    return b + a",
                "1110", "1110-111",
            ),
            (
                "def add(a, b):\n    return a + b",
                "def add(a: int, b: int) -> int:\n    return a + b",
                "1010", "1010-011",
            ),
            (
                "class Base:\n    def run(self):\n        return 0",
                "class Base:\n    def run(self):\n        return 0",
                "1110", "1110-111",
            ),
            (
                "def loop1(n):\n    for i in range(n):\n        print(i)",
                "def loop2(arr):\n    for item in arr:\n        item.clear()",
                "1000", "1000-000",
            ),
            # Same identifier vocabulary, different AST structure
            (
                "if a:\n    if b:\n        do_something()",
                "if a and b:\n    do_something()",
                "1010", "1010-011",
            ),
            (
                "def invalid_syntax(:",
                "def invalid_syntax(:",
                "0000", "0000-000",
            ),
        ]

        for i, case in enumerate(cases, 1):
            self._assert_case("Boundary", i, *case)

    # -----------------------------------------------------------------
    # Group 3: 4-Quadrant 6
    # -----------------------------------------------------------------
    def test_group3_four_quadrant_cases(self):
        cases = [
            (
                "def calc(a, b):\n    res = a * b\n    return res",
                "def calc(a, b):\n    res = a * b\n    return res",
                "1110", "1110-111",
            ),
            (
                "def calc_area(width, height):\n"
                "    area_val = width * height\n"
                "    return area_val",
                "def calc_area(var_x, var_y):\n"
                "    out_val = var_x * var_y\n"
                "    return out_val",
                "1100", "1100-010",
            ),
            (
                "def transform(val):\n"
                "    res = val * 2 + 1\n"
                "    return res",
                "def transform(val):\n"
                "    step1 = val * 2\n"
                "    res = step1 + 1\n"
                "    return res",
                "1010", "1010-010",
            ),
            (
                "def alpha(a):\n    return a + 1",
                "class Beta:\n    def __init__(self, x):\n        self.x = x",
                "1000", "1000-000",
            ),
            (
                "def greet():\n    return 'Hello'",
                "def greet():\n    return 'World'",
                "1110", "1110-100",   # H7=0 because empty bigrams fall to 0 in this implementation
            ),
            (
                "def build_dict(k, v):\n    return {k: v}",
                "def build_dict(k, v):\n"
                "    d = {}\n"
                "    d[k] = v\n"
                "    return d",
                "1010", "1010-010",
            ),
        ]

        for i, case in enumerate(cases, 1):
            self._assert_case("4-Quadrant", i, *case)

    # -----------------------------------------------------------------
    # Group 4: Q3 Deep Dive 4
    # -----------------------------------------------------------------
    def test_group4_q3_deep_dive_cases(self):
        cases = [
            (
                "def extract(items):\n"
                "    return [x for x in items if x > 0]",
                "def extract(items):\n"
                "    res = []\n"
                "    for x in items:\n"
                "        if x > 0:\n"
                "            res.append(x)\n"
                "    return res",
                "1010", "1010-010",
            ),
            (
                "def get_max(a, b):\n"
                "    return a if a > b else b",
                "def get_max(a, b):\n"
                "    if a > b:\n"
                "        return a\n"
                "    else:\n"
                "        return b",
                "1010", "1010-011",   # H7=1 because Dice=0.666
            ),
            (
                "def formula(a, b):\n"
                "    return (a + b) * (a - b)",
                "def formula(a, b):\n"
                "    return a**2 - b**2",
                "1010", "1010-001",   # H5=0, H6=0, H7=1
            ),
            (
                "def swap_vals(a, b):\n"
                "    a, b = b, a\n"
                "    return a, b",
                "def swap_vals(a, b):\n"
                "    temp = a\n"
                "    a = b\n"
                "    b = temp\n"
                "    return a, b",
                "1010", "1010-011",
            ),
        ]

        for i, case in enumerate(cases, 1):
            self._assert_case("Q3-Deep-Dive", i, *case)


if __name__ == "__main__":
    unittest.main(verbosity=2)