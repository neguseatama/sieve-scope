"""
Sieve Scope v1.3 Threshold Tuning Experiment Script
- Target Engine: SieveScopeEngineV1_3
- Feature Space: Tokenize-based pure identifiers (H3) & Weighted Bi-gram Dice (H7)
- Evaluates Precision, Recall, and F1-score over typical plagiarism & non-plagiarism patterns.
"""

import itertools
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from sieve_scope import SieveScopeEngineV1_3

POSITIVE_PAIRS = [
    ("def add(a, b):\n    return a + b",
     "def add(a, b):\n    return a + b",
     "Exact Match"),
    ("def check_limit(val):\n    return val > 100",
     "def check_limit(val):\n    return val > 200",
     "Constant Modification"),
    ("def add(a, b):\n    return a + b",
     "def sub(a, b):\n    return a + b",
     "Function Rename"),
    ("def compute_avg(a, b):\n    return (a + b) / 2",
     "def compute_avg(x, y):\n    return (x + y) / 2",
     "Variable Rename"),
    ("def process(x, y):\n    return x * y + 10",
     "def process(x, y):\n    temp = x * y\n    return temp + 10",
     "Introduce Temp Var"),
    ("class DataProcessor:\n    def run(self, items):\n        return len(items)",
     "class ListProcessor:\n    def execute(self, items):\n        return len(items)",
     "Class/Method Rename"),
]

NEGATIVE_PAIRS = [
    ("def add(a, b):\n    return a + b",
     "class Node:\n    def __init__(self, val):\n        self.val = val",
     "Different Domain"),
    ("def print_numbers(n):\n    for i in range(n):\n        print(i)",
     "def clear_cache(cache_dict):\n    for k in cache_dict.keys():\n        cache_dict[k] = None",
     "Common Syntax Loop"),
    ("def parse_json(raw_str):\n    import json\n    return json.loads(raw_str)",
     "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
     "Logic Mismatch"),
]


def run_grid_search():
    jaccard_candidates = [round(x * 0.05, 2) for x in range(7, 16)]
    dice_candidates = [round(x * 0.05, 2) for x in range(7, 16)]

    best_f1 = -1.0
    best_params = None
    best_metrics = None

    results = []

    for j_th, d_th in itertools.product(jaccard_candidates, dice_candidates):
        engine = SieveScopeEngineV1_3(jaccard_threshold=j_th, freq_dice_threshold=d_th)
        tp = fp = tn = fn = 0

        for c1, c2, label in POSITIVE_PAIRS:
            res = engine.evaluate_pair(c1, c2)
            h = res["h_states"]
            if h["H2"] == 1 or h["H3"] == 1 or h["H7"] == 1:
                tp += 1
            else:
                fn += 1

        for c1, c2, label in NEGATIVE_PAIRS:
            res = engine.evaluate_pair(c1, c2)
            h = res["h_states"]
            if h["H2"] == 1 or h["H3"] == 1 or h["H7"] == 1:
                fp += 1
            else:
                tn += 1

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        results.append((j_th, d_th, tp, fp, tn, fn, precision, recall, f1))

        if f1 > best_f1:
            best_f1 = f1
            best_params = (j_th, d_th)
            best_metrics = (tp, fp, tn, fn, precision, recall, f1)

    print("=" * 80)
    print("         SIEVE SCOPE v1.3 THRESHOLD TUNING (TOKENIZE FIXED)         ")
    print("=" * 80)
    print(f"{'Jaccard (H3)':<12} | {'Dice (H7)':<10} | {'TP':<3} | {'FP':<3} | {'TN':<3} | {'FN':<3} | {'Precision':<9} | {'Recall':<9} | {'F1-Score':<8}")
    print("-" * 80)

    for j_th, d_th, tp, fp, tn, fn, prec, rec, f1 in results:
        if f1 >= (best_f1 - 0.05):
            is_best = "<-- OPTIMAL" if (j_th, d_th) == best_params else ""
            print(f"{j_th:<12.2f} | {d_th:<10.2f} | {tp:<3} | {fp:<3} | {tn:<3} | {fn:<3} | {prec:<9.4f} | {rec:<9.4f} | {f1:<8.4f} {is_best}")

    print("=" * 80)
    print(f"OPTIMAL CONFIGURATION:")
    print(f"  - Jaccard Threshold (H3) : {best_params[0]}")
    print(f"  - Bi-gram Dice Threshold (H7): {best_params[1]}")
    print(f"  - Confusion Matrix       : TP={best_metrics[0]}, FP={best_metrics[1]}, TN={best_metrics[2]}, FN={best_metrics[3]}")
    print(f"  - Metrics                : Precision={best_metrics[4]:.4f}, Recall={best_metrics[5]:.4f}, F1-Score={best_metrics[6]:.4f}")
    print("=" * 80)

    return best_params, best_metrics


if __name__ == "__main__":
    run_grid_search()