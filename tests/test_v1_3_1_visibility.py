"""SC-T01..T10 visibility & robustness probes for the v1.3.1 lane (red-first).

Baseline facts pinned here were measured on the v1.3.0 tree (main 63a2a5b)
before any change: two empty ``__init__.py`` files form the false clone
``1110-110`` (three promote it to ``1111-110``), a parse-failed pair omits
the ``scores`` key entirely, an attribute-chain file (``x`` + ``.y`` x 5000)
parses fine but blows ``RecursionError`` outside any try in the corpus
analysis, and the declared ``sieve-core-engine`` dependency is imported
nowhere. The AB pair digest below pins the observed result so the changes
cannot alter already-observed files/pairs.
"""

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import sieve_scope
from sieve_scope import SieveClusterAnalyzerV1_3, SieveScopeEngineV1_3

REPO_ROOT = Path(__file__).resolve().parent.parent

OK_CODE = "def calc(a, b):\n    return a + b"
OK_CODE2 = "def calc(p, q):\n    return p + q"
OK_CODE3 = "def calc(m, n):\n    return m * n"
BROKEN_CODE = "def broken(:"
DEEP_CODE = "x" + ".y" * 5000  # 実測: parse 成功・骨格/位置タプル構築で RecursionError

# Tray v1.1.0 と同一の閉じた語彙（依頼書 §2-3・8 語）
CLOSED_VOCAB = {
    "refused", "parse_failed", "unreadable", "too_large",
    "symlink_skipped", "engine_unavailable", "not_applicable", "empty_input",
}

# 金型: 空・壊れファイルを含まない 2 ファイル構成の pair_results digest（v1.3.0 実測）
GOLDEN_AB_PAIR_DIGEST = "de59289fd3bdab37e2b7ff07f61be3a784ff70b095af20cdaa563dcbfbd3d825"


def _analyze(corpus, max_workers=1):
    engine = SieveScopeEngineV1_3()
    return SieveClusterAnalyzerV1_3(engine, min_cluster_size=3).analyze_corpus(
        dict(corpus), max_workers=max_workers
    )


def _digest_pairs(analysis):
    ser = {k[0] + "|" + k[1]: v for k, v in analysis["pair_results"].items()}
    return hashlib.sha256(json.dumps(ser, sort_keys=True).encode("utf-8")).hexdigest()


class TestSkippedVisibility(unittest.TestCase):
    """SC-T01/02/03: 空・自明ファイルの除外と追加キー skipped。"""

    def test_sct01_empty_init_files_excluded_and_listed(self):
        corpus = {"pkg_a/__init__.py": "", "pkg_b/__init__.py": "", "app.py": OK_CODE}
        analysis = _analyze(corpus)
        pair_names = {name for pair in analysis["pair_results"] for name in pair}
        self.assertNotIn(("pkg_a/__init__.py", "pkg_b/__init__.py"),
                         [tuple(k) for k in analysis["pair_results"]])
        self.assertNotIn("pkg_a/__init__.py", pair_names)
        self.assertNotIn("pkg_b/__init__.py", pair_names)
        by_path = {e["path"]: e["reason"] for e in analysis["skipped"]}
        self.assertEqual(by_path.get("pkg_a/__init__.py"), "not_applicable")
        self.assertEqual(by_path.get("pkg_b/__init__.py"), "not_applicable")

    def test_sct02_nonempty_pairs_identical_with_or_without_empty_files(self):
        corpus_ab = {"a.py": OK_CODE, "b.py": OK_CODE2}
        corpus_with = {"a.py": OK_CODE, "b.py": OK_CODE2, "e1.py": "", "e2.py": "# comment only"}
        base = _analyze(corpus_ab)
        with_empty = _analyze(corpus_with)
        self.assertEqual(base["pair_results"], with_empty["pair_results"])
        self.assertEqual(_digest_pairs(base), GOLDEN_AB_PAIR_DIGEST)
        self.assertEqual(_digest_pairs(with_empty), GOLDEN_AB_PAIR_DIGEST)

    def test_sct03_docstring_only_files_stay_compared(self):
        corpus = {"a.py": OK_CODE, "doc.py": '"""Module docstring."""\n'}
        analysis = _analyze(corpus)
        self.assertIn(("a.py", "doc.py"), [tuple(k) for k in analysis["pair_results"]])
        self.assertEqual(analysis["skipped"], [])


class TestParseFailureVisibility(unittest.TestCase):
    """SC-T04/SC-T05: 解析失敗を「類似なし」と区別する。"""

    def test_sct04_parse_failure_listed_while_results_preserved(self):
        corpus = {"a.py": OK_CODE, "b.py": OK_CODE2, "bad.py": BROKEN_CODE}
        analysis = _analyze(corpus)
        by_path = {e["path"]: e["reason"] for e in analysis["skipped"]}
        self.assertEqual(by_path.get("bad.py"), "parse_failed")
        pair_keys = [tuple(k) for k in analysis["pair_results"]]
        self.assertIn(("a.py", "bad.py"), pair_keys)  # 既存の結果は保存される
        self.assertIn(("b.py", "bad.py"), pair_keys)
        bad_pair = analysis["pair_results"][("a.py", "bad.py")]
        self.assertEqual(bad_pair["mask"], "0000-000")

    def test_sct05_h1_zero_pairs_carry_scores_null(self):
        res = SieveScopeEngineV1_3().evaluate_pair(BROKEN_CODE, OK_CODE)
        self.assertIn("scores", res)
        self.assertIsNone(res["scores"])
        self.assertEqual(res["v0_mask"], "0000")
        self.assertEqual(res["mask"], "0000-000")
        self.assertTrue(res["short_circuited"])
        self.assertEqual(
            set(res.keys()),
            {"h_states", "v0_mask", "mask", "short_circuited", "scores"},
        )


class TestRecursionContainment(unittest.TestCase):
    """SC-T06: 深い入れ子で全体が止まらない。"""

    def test_sct06_deep_file_contained_and_limit_untouched(self):
        corpus = {"a.py": OK_CODE, "b.py": OK_CODE2, "c.py": OK_CODE3, "deep.py": DEEP_CODE}
        limit_before = sys.getrecursionlimit()
        analysis = _analyze(corpus)  # v1.3.0 では RecursionError で全体が止まる（実測）
        self.assertEqual(sys.getrecursionlimit(), limit_before)
        by_path = {e["path"]: e["reason"] for e in analysis["skipped"]}
        self.assertEqual(by_path.get("deep.py"), "parse_failed")
        pair_names = {name for pair in analysis["pair_results"] for name in pair}
        self.assertNotIn("deep.py", pair_names)
        self.assertIn(("a.py", "b.py"), [tuple(k) for k in analysis["pair_results"]])


class TestParallelFallback(unittest.TestCase):
    """SC-T07: プールを作れない環境でも同じ結果を逐次で返す。"""

    def test_sct07_pool_failure_falls_back_to_sequential(self):
        corpus = {"f%d.py" % i: "def calc_%d(a, b):\n    return a + %d" % (i, i) for i in range(6)}
        baseline = _analyze(corpus, max_workers=1)
        real_pool = sieve_scope.ProcessPoolExecutor

        class BoomPool:
            def __init__(self, *args, **kwargs):
                raise OSError("no functioning sem_open in frozen app")

        sieve_scope.ProcessPoolExecutor = BoomPool
        try:
            fallback = _analyze(corpus, max_workers=None)  # 15 ペア > 10 なので並列経路を試みる
        finally:
            sieve_scope.ProcessPoolExecutor = real_pool
        self.assertEqual(baseline, fallback)  # バイト一致（決定論）


class TestResultContract(unittest.TestCase):
    """SC-T09: 追加キーのみ・語彙は閉じている。"""

    def test_sct09_keys_additive_and_vocab_closed(self):
        corpus = {"a.py": OK_CODE, "b.py": OK_CODE2, "e.py": "", "bad.py": BROKEN_CODE}
        analysis = _analyze(corpus)
        self.assertEqual(
            set(analysis.keys()),
            {"valid_clusters", "all_clusters", "pair_results", "warnings", "skipped"},
        )
        for entry in analysis["skipped"]:
            self.assertTrue(set(entry.keys()) <= {"path", "reason"})
            self.assertIn(entry["reason"], CLOSED_VOCAB)
        for res in analysis["pair_results"].values():
            self.assertTrue(
                set(res.keys()) <= {"h_states", "v0_mask", "mask", "short_circuited", "scores"}
            )


class TestVersionAndChangelog(unittest.TestCase):
    """SC-T10: 版と CHANGELOG の整合（1.3.1）。"""

    def test_sct10_version_pins_and_changelog(self):
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## [1.3.1]", changelog)
        # 1.4.0（分離版）が同じ木に積まれると pyproject の版は 1.4.0 に上がるため、
        # 「pyproject の版 = CHANGELOG 先頭節の版」の整合で固定する。
        # 1.4.0 が適用されていない木では 1.3.1 であることを直接固定する。
        versions = re.findall(r"^## \[([0-9.]+)\]", changelog, re.MULTILINE)
        self.assertTrue(versions)
        self.assertIn('version = "%s"' % versions[0], pyproject)
        if "## [1.4.0]" not in changelog:
            self.assertIn('version = "1.3.1"', pyproject)


if __name__ == "__main__":
    unittest.main(verbosity=2)
