"""
Sieve Scope v1.3 Edge Cases & Parallel Determinism Test Suite
- TestParallelDeterminism: Strict full-state parallel vs sequential determinism.
- TestUnicodeIdentifiers: Non-ASCII (Japanese) identifier extraction and evaluation.
- TestDeepASTRecursion: Stress testing against deeply nested ASTs (safe depth).
- TestIndirectChainDetection: Verified indirect propagation chain topology.
- TestEmptyAndInvalidInputs: Empty strings, whitespace, comment-only, and syntax errors.
"""

import unittest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from sieve_scope import SieveScopeEngineV1_3, SieveClusterAnalyzerV1_3


class TestParallelDeterminism(unittest.TestCase):
    """1. 並列実行と逐次実行の完全一致・決定論性検証（戻り値全体を比較）"""

    def setUp(self):
        self.engine = SieveScopeEngineV1_3()
        self.corpus = {
            "A.py": "def calc(a, b): return a + b",
            "B.py": "def calc(x, y): return x + y",
            "C.py": "def calc(p, q): return p + q",
            "D.py": "def calc(m, n): return m * n",
            "E.py": "def process(data): return data * 2",
        }

    def test_parallel_vs_sequential_identical(self):
        seq_analyzer = SieveClusterAnalyzerV1_3(self.engine, min_cluster_size=3)
        seq_result = seq_analyzer.analyze_corpus(self.corpus, max_workers=1)

        par_results = []
        for _ in range(3):
            par_analyzer = SieveClusterAnalyzerV1_3(self.engine, min_cluster_size=3)
            par_results.append(par_analyzer.analyze_corpus(self.corpus, max_workers=4))

        # 逐次実行と各並列実行の戻り値全体を完全一致比較
        for par_result in par_results:
            self.assertEqual(seq_result, par_result)

        # 並列実行同士も完全一致
        self.assertEqual(par_results[0], par_results[1])
        self.assertEqual(par_results[1], par_results[2])


class TestUnicodeIdentifiers(unittest.TestCase):
    """2. Unicode (日本語等) 識別子の正常トークナイズと評価検証"""

    def setUp(self):
        self.engine = SieveScopeEngineV1_3()

    def test_unicode_identifier_extraction_and_matching(self):
        code1 = "def 計算_処理(入力_データ, 係数):\n    結果 = 入力_データ * 係数\n    return 結果"
        code2 = "def 計算_処理(入力_データ, 係数):\n    結果 = 入力_データ * 係数\n    return 結果"
        code3 = "def 計算_処理(変数_a, 変数_b):\n    一時変数 = 変数_a * 変数_b\n    return 一時変数"

        res1 = self.engine.evaluate_pair(code1, code2)
        self.assertEqual(res1["mask"], "1110-111")

        res2 = self.engine.evaluate_pair(code1, code3)
        self.assertEqual(res2["v0_mask"], "1100")
        self.assertEqual(res2["h_states"]["H5"], 0)  # arg.arg が POS tuple に残るため


class TestDeepASTRecursion(unittest.TestCase):
    """3. 深層ASTにおけるスタックオーバーフロー耐性検証（安全な深度）"""

    def setUp(self):
        self.engine = SieveScopeEngineV1_3()

    def test_deeply_nested_if_statements(self):
        depth = 50  # Python parser is safe at this depth
        code_lines = ["def deep_func(x):"]
        for i in range(depth):
            code_lines.append(" " * ((i + 1) * 4) + f"if x > {i}:")
        code_lines.append(" " * ((depth + 1) * 4) + "return x")

        deep_code1 = "\n".join(code_lines)
        deep_code2 = "\n".join(code_lines)

        try:
            res = self.engine.evaluate_pair(deep_code1, deep_code2)
            self.assertEqual(res["h_states"]["H1"], 1)
            self.assertEqual(res["h_states"]["H2"], 1)
        except RecursionError:
            self.fail("SieveScopeEngine raised RecursionError on deeply nested AST")


class TestIndirectChainDetection(unittest.TestCase):
    """4. detect_indirect_chains の確実なトポロジー検証"""

    def setUp(self):
        self.engine = SieveScopeEngineV1_3(jaccard_threshold=0.50, freq_dice_threshold=0.60)

    def test_indirect_chain_warning_generated(self):
        corpus = {
            "node_A.py": (
                "def process_data(var_x, var_y):\n"
                "    temp_val = var_x + var_y\n"
                "    return temp_val"
            ),
            "node_B.py": (
                "def compute_total(val_a, val_b):\n"
                "    res_out = val_a + val_b\n"
                "    return res_out"
            ),
            "node_C.py": (
                "def compute_total(val_a, val_b):\n"
                "    return val_a + val_b"
            ),
        }

        analyzer = SieveClusterAnalyzerV1_3(self.engine, min_cluster_size=3)
        analysis = analyzer.analyze_corpus(corpus, max_workers=1)

        self.assertEqual(len(analysis["valid_clusters"]), 1)
        self.assertEqual(analysis["valid_clusters"][0], ["node_A.py", "node_B.py", "node_C.py"])

        warnings = analysis["warnings"]
        self.assertTrue(len(warnings) >= 1)

        chain_warning = next((w for w in warnings if w["code"] == "INDIRECT_PLAGIARISM_CHAIN_WARNING"), None)
        self.assertIsNotNone(chain_warning)
        self.assertEqual(chain_warning["pair"], ("node_A.py", "node_C.py"))
        self.assertEqual(chain_warning["hops"], 2)


class TestEmptyAndInvalidInputs(unittest.TestCase):
    """5. 構文エラー・コメントのみ等の境界条件検証"""

    def setUp(self):
        self.engine = SieveScopeEngineV1_3()

    def test_syntax_error_returns_zero_mask(self):
        code_invalid = "def syntax_error(:"
        code_valid = "def valid(): pass"

        res = self.engine.evaluate_pair(code_invalid, code_valid)
        self.assertEqual(res["v0_mask"], "0000")
        self.assertEqual(res["mask"], "0000-000")
        self.assertTrue(res["short_circuited"])

    def test_comment_only_code(self):
        code_comment1 = "# Comment line 1\n# Comment line 2"
        code_comment2 = "# Different comment line"

        res = self.engine.evaluate_pair(code_comment1, code_comment2)
        self.assertEqual(res["h_states"]["H1"], 1)
        self.assertEqual(res["h_states"]["H2"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)