"""
Sieve Scope v1.3 Pair-Engine Benchmark
- Measures evaluate_pair() only.
- Uses deterministic synthetic code generation.
- Not a corpus-level ProcessPoolExecutor benchmark.
"""

import time
from sieve_scope import SieveScopeEngineV1_3


def generate_synthetic_code(i: int) -> str:
    templates = [
        f"def fn_{i}(a, b):\n    return a + {i} * b",
        f"class Handler_{i}:\n    def process(self, data):\n        return [x for x in data if x > {i}]",
        f"def compute_{i}(val):\n    res = 0\n    for k in range({i}):\n        res += k\n    return res",
    ]
    return templates[i % len(templates)]


def run_benchmark(num_files: int = 100) -> None:
    corpus = {f"file_{i}.py": generate_synthetic_code(i) for i in range(num_files)}
    engine = SieveScopeEngineV1_3()

    keys = list(corpus.keys())
    total_pairs = len(keys) * (len(keys) - 1) // 2

    # Warm-up
    engine.evaluate_pair(corpus[keys[0]], corpus[keys[1]])

    start_time = time.perf_counter()
    short_circuited_count = 0

    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            res = engine.evaluate_pair(corpus[keys[i]], corpus[keys[j]])
            if res["short_circuited"]:
                short_circuited_count += 1

    elapsed = time.perf_counter() - start_time
    skip_rate = (short_circuited_count / total_pairs) * 100

    print("=== Sieve Scope v1.3 Pair-Engine Benchmark ===")
    print(f"ファイル数           : {num_files}")
    print(f"総ペア数             : {total_pairs}")
    print(f"ショートサーキット数 : {short_circuited_count} ({skip_rate:.2f}%)")
    print(f"総実行時間           : {elapsed:.4f} 秒")
    print(f"ペアあたり平均時間   : {(elapsed / total_pairs) * 1000:.4f} ms")
    print("注: この結果は synthetic corpus に基づく参考値です。")


if __name__ == "__main__":
    run_benchmark(num_files=100)