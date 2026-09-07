# 🏛️ Sieve Scope v1.3 Architecture Specification

## Pipeline overview

[ Source Code Pair ]
│
▼
[ AST Parseability Check (H1) ]
│ (SyntaxError → 0000-000, short-circuit)
▼
[ AST Skeleton Extraction (H2) ]
│
▼
[ Pure Identifier Extraction via tokenize (H3) ]
│
▼
[ Short-Circuit Evaluation: H2=0 ∧ H3=0 ? ]
→ YES: return "1000-000" immediately
→ NO : continue to H5–H7
│
▼
[ Positional AST Structure Hash (H5) ]
[ Constant / Literal Signature (H6) ]
[ Weighted Bi-gram Dice Coefficient (H7) ]
│
▼
[ H4 Safety-Gated Cluster Promotion ]
│ (valid cluster ≥3 ∧ direct evidence H2∨H3)
▼
[ 7-bit Mask Assembly: H1H2H3H4-H5H6H7 ]
│
▼
[ Indirect Chain Warning (BFS) ]


---


---

## The seven hypotheses

| Bit | Hypothesis | What it measures |
|---|---|---|
| `H1` | Parseability | Can both be parsed by `ast.parse()`? |
| `H2` | AST Skeleton Match | AST node-type sequence from `ASTSkeletonVisitor.generic_visit()`; includes Load, Store, Del, operators |
| `H3` | Identifier Similarity | 60% Multiset Jaccard + 40% SequenceMatcher over tokenize-derived identifiers |
| `H4` | Cluster Safety Invariant | Only when cluster size ≥3 and direct H2/H3 evidence |
| `H5` | Positional Structure (g_POS) | SHA-256 of `build_pos_tuple()`. Excludes `value`/`id`/`attr` non-AST fields; retains `arg.arg` |
| `H6` | Constant Signature (g_CONST) | Sorted `ast.Constant` values |
| `H7` | Weighted Bi-gram Dice (g_FREQ) | Dice over identifier Bi-grams |

---

## Safety invariant: `H4` requires direct evidence

H4 = 1 ⟺ cluster_size(pair) ≥ 3 ∧ (H2 = 1 ∨ H3 = 1)


`evaluate_pair()` always returns H4=0 because cluster context is unavailable
at pair-evaluation time. `SieveClusterAnalyzerV1_3` promotes H4 only after
corpus-level cluster validation.

---

## Observation Space & Resolution Profile

Sieve Scope v1.3 is an observation model projecting code pairs into a
7-dimensional binary space.

$$f_{v1.3}(C_1, C_2) = (H_1, H_2, H_3, H_4, H_5, H_6, H_7)$$

This defines an equivalence relation where two codes are considered
"observation clones" if their masks match. This does not imply semantic
equivalence.

---

## Known limitation: structural convergence in simple functions

Very short functions with identical AST node types but different semantics
may produce H2=1 and H3=1. H5 and H7 may distinguish some cases, but
semantic equivalence is not guaranteed.