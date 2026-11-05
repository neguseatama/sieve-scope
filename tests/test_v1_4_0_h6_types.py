"""SC-T11/SC-T12 probes for the v1.4.0 lane (S2, separate version).

Baseline measured on the 1.3.1 tree: H6 compares ``str(value)``, so the
integer ``1`` and the string ``"1"`` collide into one constant form and
H6 becomes 1 for ``x = 1`` vs ``x = "1"``. Same-type comparisons are
pinned here as invariants (they must not move with the fix). Per the
commission, if any frozen-corpus mold/digest changed with this fix the
lane stops and reports instead of shipping — the 24-case suite has no
mixed-type constants (measured), so it is expected to stay green.
"""

import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from sieve_scope import SieveScopeEngineV1_3

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestH6TypeAwareComparison(unittest.TestCase):
    """SC-T11: H6 が 1 と "1" を区別し、同型の結果は不変。"""

    def setUp(self):
        self.engine = SieveScopeEngineV1_3()

    def test_sct11_h6_distinguishes_value_types(self):
        self.assertEqual(
            self.engine.evaluate_pair("x = 1", 'x = "1"')["h_states"]["H6"], 0
        )  # v1.3.x では 1（衝突）だった・実測済み
        self.assertEqual(
            self.engine.evaluate_pair("x = 1", "x = 1")["h_states"]["H6"], 1
        )  # 同型同値は不変
        self.assertEqual(
            self.engine.evaluate_pair("x = 1", "x = 2")["h_states"]["H6"], 0
        )  # 同型異値は不変
        self.assertEqual(
            self.engine.evaluate_pair("x = 1", "x = 1.0")["h_states"]["H6"], 0
        )  # int vs float（実測: 旧版でも 0）

    def test_sct11_constant_sets_stay_order_insensitive(self):
        mixed_a = "a = 1\nb = 'x'"
        mixed_b = "a = 'x'\nb = 1"
        self.assertEqual(
            self.engine.evaluate_pair(mixed_a, mixed_b)["h_states"]["H6"], 1
        )
        mixed_c = "a = 1\nb = \"x\""  # 同値だが型が違う組合せ
        self.assertEqual(
            self.engine.evaluate_pair(mixed_a, mixed_c)["h_states"]["H6"], 1
        )
        self.assertEqual(
            self.engine.evaluate_pair("a = 1\nb = 2", "a = '1'\nb = '2'")["h_states"]["H6"], 0
        )


class TestVersionAndChangelog(unittest.TestCase):
    """SC-T12: 版と CHANGELOG の整合（1.4.0・分離版）。"""

    def test_sct12_version_pins_and_changelog(self):
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('version = "1.4.0"', pyproject)
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## [1.4.0]", changelog)


if __name__ == "__main__":
    unittest.main(verbosity=2)
