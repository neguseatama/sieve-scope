"""
Sieve Scope Engine v1.3 (Production Ready)
- 7-bit Observation Space (H1 - H7)
- Short-Circuit Evaluation
- Tokenize-based Pure Identifier Extraction
- Weighted Bi-gram Dice Coefficient
- Parallel Pair Evaluation
- Indirect Chain Detection
"""

import ast
import difflib
import hashlib
import io
import keyword
import tokenize
from collections import Counter, defaultdict, deque
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List, Set, Tuple, Optional

# v0完全互換の除外識別子集合
IGNORED_WORDS_V0: Set[str] = {
    'print', 'len', 'range', 'sum', 'int', 'str', 'self', '__init__'
}


def extract_pure_identifiers(code: str, ignored_words: Set[str] = IGNORED_WORDS_V0) -> List[str]:
    """
    v0完全互換: tokenizeベースで非キーワードNAMEトークンを順序通り抽出する。
    関数名・クラス名・変数名・属性名をすべて識別子として捕捉する。
    """
    identifiers = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(code).readline)
        for toknum, tokval, _, _, _ in tokens:
            if toknum == tokenize.NAME and not keyword.iskeyword(tokval):
                if tokval not in ignored_words:
                    identifiers.append(tokval)
    except Exception:
        pass
    return identifiers


def build_pos_tuple(node: Any) -> Any:
    """
    v1.2完全互換: ASTフィールド構造タプルを生成する。
    value / id / attr フィールドのうち非AST値（定数・識別子名）は除外するが、
    arg などのその他スカラーフィールドは保持する。
    """
    if not isinstance(node, ast.AST):
        if isinstance(node, list):
            return tuple(build_pos_tuple(x) for x in node)
        return str(node)

    field_tuples = []
    for field, value in ast.iter_fields(node):
        if field in ("value", "id", "attr") and not isinstance(value, ast.AST):
            continue
        field_tuples.append((field, build_pos_tuple(value)))
    return (type(node).__name__, tuple(field_tuples))


class ASTSkeletonVisitor(ast.NodeVisitor):
    """
    H2: AST構造骨格の抽出。
    generic_visit はすべてのノード型名を記録する（Load, Store, Del, 演算子ノードを含む）。
    """
    def __init__(self):
        self.skeleton = []

    def generic_visit(self, node):
        self.skeleton.append(type(node).__name__)
        super().generic_visit(node)


class ASTConstantVisitor(ast.NodeVisitor):
    """H6: g_CONST 定数・リテラルの抽出"""
    def __init__(self):
        self.constants = []

    def visit_Constant(self, node):
        self.constants.append(str(node.value))
        self.generic_visit(node)


class SieveScopeEngineV1_3:
    """7次元観測空間評価エンジン"""

    def __init__(self, jaccard_threshold: float = 0.50, freq_dice_threshold: float = 0.60):
        self.jaccard_threshold = jaccard_threshold
        self.freq_dice_threshold = freq_dice_threshold

    def evaluate_pair(self, code1: str, code2: str) -> Dict[str, Any]:
        # H1: Parseability
        try:
            tree1 = ast.parse(code1)
            tree2 = ast.parse(code2)
            h1 = 1
        except Exception:
            return {
                "h_states": {"H1": 0, "H2": 0, "H3": 0, "H4": 0, "H5": 0, "H6": 0, "H7": 0},
                "v0_mask": "0000",
                "mask": "0000-000",
                "short_circuited": True,
            }

        # H2: AST Skeleton（全ノード型の列を比較）
        vis1, vis2 = ASTSkeletonVisitor(), ASTSkeletonVisitor()
        vis1.visit(tree1)
        vis2.visit(tree2)
        skeleton1 = "_".join(vis1.skeleton)
        skeleton2 = "_".join(vis2.skeleton)
        h2 = 1 if skeleton1 == skeleton2 else 0

        # H3: 純粋識別子の類似度（Multiset Jaccard + SequenceMatcher）
        ids1 = extract_pure_identifiers(code1)
        ids2 = extract_pure_identifiers(code2)

        if not ids1 and not ids2:
            h3_score = 1.0
        elif not ids1 or not ids2:
            h3_score = 0.0
        else:
            c1, c2 = Counter(ids1), Counter(ids2)
            intersection = sum((c1 & c2).values())
            union = sum((c1 | c2).values())
            multiset_jaccard = intersection / union if union > 0 else 0.0

            seq_ratio = difflib.SequenceMatcher(None, ids1, ids2).ratio()
            h3_score = 0.6 * multiset_jaccard + 0.4 * seq_ratio

        # v0互換: 厳密な '>' 判定
        h3 = 1 if h3_score > self.jaccard_threshold else 0

        # ショートサーキット: H2=0 かつ H3=0 の場合のみ高コスト計算をスキップ
        if h2 == 0 and h3 == 0:
            return {
                "h_states": {"H1": 1, "H2": 0, "H3": 0, "H4": 0, "H5": 0, "H6": 0, "H7": 0},
                "v0_mask": "1000",
                "mask": "1000-000",
                "short_circuited": True,
                "scores": {"h3_score": h3_score},
            }

        # H5: g_POS（build_pos_tuple による決定論的ハッシュ）
        pos_tuple1 = build_pos_tuple(tree1)
        pos_tuple2 = build_pos_tuple(tree2)
        pos_hash1 = hashlib.sha256(str(pos_tuple1).encode('utf-8')).hexdigest()
        pos_hash2 = hashlib.sha256(str(pos_tuple2).encode('utf-8')).hexdigest()
        h5 = 1 if pos_hash1 == pos_hash2 else 0

        # H6: g_CONST（定数集合の一致）
        c_vis1, c_vis2 = ASTConstantVisitor(), ASTConstantVisitor()
        c_vis1.visit(tree1)
        c_vis2.visit(tree2)
        h6 = 1 if sorted(c_vis1.constants) == sorted(c_vis2.constants) else 0

        # H7: g_FREQ（重み付き Bi-gram Dice 係数）
        bigrams1 = self._get_weighted_bigrams(ids1)
        bigrams2 = self._get_weighted_bigrams(ids2)

        common_keys = set(bigrams1.keys()) & set(bigrams2.keys())
        common_weight = sum(min(bigrams1[bg], bigrams2[bg]) for bg in common_keys)
        total_weight = sum(bigrams1.values()) + sum(bigrams2.values())

        dice_score = (2.0 * common_weight) / total_weight if total_weight > 0 else 0.0
        h7 = 1 if dice_score >= self.freq_dice_threshold else 0

        # H4: ペア評価では常に0（クラスタ分析時のみ昇格）
        h4 = 0

        v0_mask = f"{h1}{h2}{h3}{h4}"
        ext_mask = f"{h5}{h6}{h7}"

        return {
            "h_states": {"H1": h1, "H2": h2, "H3": h3, "H4": h4, "H5": h5, "H6": h6, "H7": h7},
            "v0_mask": v0_mask,
            "mask": f"{v0_mask}-{ext_mask}",
            "short_circuited": False,
            "scores": {
                "h3_score": h3_score,
                "h7_dice_score": dice_score,
            },
        }

    @staticmethod
    def _get_weighted_bigrams(identifiers: List[str]) -> Dict[str, float]:
        """識別子列から Bi-gram と出現頻度（重み）を生成"""
        bigrams = defaultdict(float)
        for i in range(len(identifiers) - 1):
            bg = f"{identifiers[i]}___{identifiers[i+1]}"
            bigrams[bg] += 1.0
        return bigrams


def _pair_worker_func(args):
    """ProcessPoolExecutor用のトップレベル並列ワーカー関数"""
    key1, code1, key2, code2, jaccard_th, freq_th = args
    engine = SieveScopeEngineV1_3(jaccard_threshold=jaccard_th, freq_dice_threshold=freq_th)
    result = engine.evaluate_pair(code1, code2)
    return (key1, key2), result


class SieveClusterAnalyzerV1_3:
    """クラスタ解析・安全不変式・並列処理・間接伝搬警告エンジン"""

    def __init__(self, engine: SieveScopeEngineV1_3, min_cluster_size: int = 3):
        self.engine = engine
        self.min_cluster_size = min_cluster_size

    def analyze_corpus(self, corpus: Dict[str, str], max_workers: Optional[int] = None) -> Dict[str, Any]:
        keys = sorted(list(corpus.keys()))
        pair_tasks = []

        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                k1, k2 = keys[i], keys[j]
                pair_tasks.append((
                    k1, corpus[k1], k2, corpus[k2],
                    self.engine.jaccard_threshold,
                    self.engine.freq_dice_threshold,
                ))

        raw_pair_results = {}

        if len(pair_tasks) > 10 and max_workers != 1:
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = [executor.submit(_pair_worker_func, task) for task in pair_tasks]
                for future in as_completed(futures):
                    pair_key, res = future.result()
                    raw_pair_results[pair_key] = res
        else:
            for task in pair_tasks:
                pair_key, res = _pair_worker_func(task)
                raw_pair_results[pair_key] = res

        # 決定論的順序の保証
        pair_results = dict(sorted(raw_pair_results.items()))

        # 直接類似エッジの構築（H2=1 または H3=1）
        direct_adj = defaultdict(set)
        for (k1, k2), res in pair_results.items():
            if res["h_states"]["H2"] == 1 or res["h_states"]["H3"] == 1:
                direct_adj[k1].add(k2)
                direct_adj[k2].add(k1)

        # 連結成分抽出
        visited = set()
        valid_clusters = []
        all_clusters = []

        for node in keys:
            if node not in visited:
                component = set()
                queue = deque([node])
                visited.add(node)
                while queue:
                    curr = queue.popleft()
                    component.add(curr)
                    for neighbor in sorted(list(direct_adj[curr])):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)

                all_clusters.append(component)
                if len(component) >= self.min_cluster_size:
                    valid_clusters.append(component)

        # H4 安全不変式の適用（有効クラスタ内・直接類似のあるペアのみ昇格）
        valid_nodes = set().union(*valid_clusters) if valid_clusters else set()

        for (k1, k2), res in pair_results.items():
            is_direct = (res["h_states"]["H2"] == 1 or res["h_states"]["H3"] == 1)
            in_valid_cluster = (k1 in valid_nodes and k2 in valid_nodes and
                                any(k1 in cl and k2 in cl for cl in valid_clusters))

            if in_valid_cluster and is_direct:
                res["h_states"]["H4"] = 1
                h = res["h_states"]
                res["v0_mask"] = f"{h['H1']}{h['H2']}{h['H3']}1"
                res["mask"] = f"{res['v0_mask']}-{h['H5']}{h['H6']}{h['H7']}"

        # 間接伝搬チェーン警告の検出
        warnings = self.detect_indirect_chains(keys, direct_adj, valid_clusters)

        return {
            "valid_clusters": [sorted(list(c)) for c in valid_clusters],
            "all_clusters": [sorted(list(c)) for c in all_clusters],
            "pair_results": pair_results,
            "warnings": warnings,
        }

    @staticmethod
    def detect_indirect_chains(nodes, direct_adj, valid_clusters):
        warnings = []
        for cluster in valid_clusters:
            cluster_nodes = sorted(list(cluster))
            for i in range(len(cluster_nodes)):
                for j in range(i + 1, len(cluster_nodes)):
                    u, v = cluster_nodes[i], cluster_nodes[j]
                    if v not in direct_adj[u]:
                        queue = deque([[u]])
                        visited = {u}
                        found_path = None
                        while queue:
                            path = queue.popleft()
                            curr = path[-1]
                            if curr == v:
                                found_path = path
                                break
                            for neighbor in sorted(list(direct_adj[curr])):
                                if neighbor not in visited and neighbor in cluster:
                                    visited.add(neighbor)
                                    queue.append(path + [neighbor])
                        if found_path and len(found_path) > 2:
                            warnings.append({
                                "code": "INDIRECT_PLAGIARISM_CHAIN_WARNING",
                                "pair": (u, v),
                                "message": (
                                    f"Direct similarity not confirmed between '{u}' and '{v}', "
                                    f"but indirect chain detected via {len(found_path)-1} hops."
                                ),
                                "propagation_path": " -> ".join(found_path),
                                "hops": len(found_path) - 1,
                            })
        return warnings