# Sieve Scope v1.3

[English](README.md) | **日本語**

> **「コードのフォーマットを透過し、アルゴリズムの純粋なロジックだけを覗き込む」**  
> 完全ローカル実行・外部依存ゼロ・決定論的（100%再現可能）なコード盗用・構造類似検証エンジンです。  
> [Sieve-Core](https://github.com/neguseatama/sieve-core) の決定論的類似度エンジンと、[Sieve-Referee](https://github.com/neguseatama/sieve-referee) の多軸仮説・LUT判定思想を、**ソースコードドメイン**へ拡張したプロジェクトです。

[![PyPI Version](https://img.shields.io/pypi/v/sieve-scope.svg)](https://pypi.org/project/sieve-scope/)
[![Python Version](https://img.shields.io/pypi/pyversions/sieve-scope.svg)](https://pypi.org/project/sieve-scope/)
[![CI](https://github.com/neguseatama/sieve-scope/actions/workflows/test.yml/badge.svg)](https://github.com/neguseatama/sieve-scope/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

---

## 💡 コンセプトと開発思想

本プロジェクトの起点は「エラトステネスの篩」に着想を得て設計した「集合論の篩」 Sieve-AI の設計思想を、より汎用的なテキスト・データ処理ドメインに適用したコアエンジンが Sieve-Core です。  
次に、その Sieve-Core に「組み合わせ論の篩」を追加設計した　`Sieve Referee` は、複数の独立した情報源による裏付けに基づき、ノイズから確かな情報を抽出するゼロディペンデンシーのPythonライブラリです。  
そして、Sieve Scope はさらに2軸評価を加えて再設計したことで、コードの「表面的なフォーマット（変数名・コメント・空白）」と「本質的なロジック（アルゴリズム構造）」を分離して観測する、説明可能なコード盗用検知エンジンです。

従来の文字列比較や単純な類似度判定では、  
- 変数名を変えただけの盗用（**変数名ロンダリング**）  
- 共通テンプレートによる偶然の一致（**ボイラープレート**）  

を区別することが困難でした。

`Sieve Scope` は、  
- **AST（抽象構文木）** から識別子を捨てた「ロジックの骨格」  
- **tokenize** から抽出した「識別子の語彙・順序」  

の2軸を独立に観測し、Sieve-Referee から継承した**仮説マスク（H1〜H7）とLUT**によって、なぜその判定になったのかを完全に説明します。

> 「Sieve Scope」という名称は、コードの表面（フォーマット）を透過し、顕微鏡（Microscope）のようにアルゴリズムの純粋なロジックだけを覗き込んで比較する、という設計思想に由来します。

---

## 🔥 主な特徴

- **7-bit 観測空間（H1〜H7）**  
  AST骨格・識別子語彙・位置/順序（g_POS）・定数（g_CONST）・語彙文脈（g_FREQ）を独立して評価。
- **v0_mask 互換性**  
  従来の4-bitマスク（`v0_mask`）は回帰テストによって維持・保証。
- **厳密なクラスタ安全不変式**  
  クラスタサイズ3以上、かつ直接類似証拠（H2∨H3）がある場合のみ H4=1 に昇格。
- **ショートサーキット最適化**  
  構造・語彙ともに無関係なペアを即座に `1000-000` として返却。
- **ゼロ依存・決定論**  
  Python標準ライブラリのみで実装。誰が実行しても同じ結果になります。

---

## 📐 7-bit 観測空間

| 仮説 | 名称 | 評価内容 | 判定基準 / 閾値 |
| :--- | :--- | :--- | :--- |
| **H1** | Parseability | Python 構文として解析可能か | AST 構文木生成の成否 |
| **H2** | AST Skeleton | AST ノード型の順序列が完全一致するか | 骨格文字列の完全一致 |
| **H3** | Identifier Similarity | 識別子の Jaccard + 順序類似度 | スコア `> 0.50` |
| **H4** | Cluster Safety | 直接類似＋サイズ3以上の有効クラスタ所属 | 不変式条件の成立 |
| **H5** | g_POS | 再帰的ASTフィールド表現のSHA-256ハッシュ | ハッシュ完全一致 |
| **H6** | g_CONST | 定数・リテラル集合の一致 | ソート済み定数リストの完全一致 |
| **H7** | g_FREQ | 重み付き識別子 Bi-gram Dice 係数 | スコア `>= 0.60` |

---

## 💻 クイックスタート

```python
from sieve_scope import SieveScopeEngineV1_3

engine = SieveScopeEngineV1_3(jaccard_threshold=0.50, freq_dice_threshold=0.60)

code_a = "def calc_sum(a, b):\n    return a + b"
code_b = "def calc_sum(x, y):\n    return x + y"

result = engine.evaluate_pair(code_a, code_b)

print(result["v0_mask"])   # 例: 1100
print(result["mask"])      # 例: 1100-110

---

### パラメータ設定 (Thresholds)

- `jaccard_threshold` (デフォルト: `0.50`): H3 Multiset Jaccard + 系列類似度フィルタリングの閾値。
- `freq_dice_threshold` (デフォルト: `0.60`): H7 識別子 N-gram Dice 係数フィルタリングの閾値。

> **キャリブレーションとデフォルト閾値に関する注意 (v1.3)**:
> 合成ベンチマークデータを用いたグリッドサーチ評価では、`0.35` 〜 `0.75` の広範囲で最高分類精度（$F1 = 1.0000$）を達成することが確認されています。しかしながら、v0 との互換性維持、既存リグレッションテストの決定性確保、および実際のコードベースにおける共通語彙（ボイラープレート）に起因する過剰検出（False Positive）を防止するため、標準のデフォルト値は **`0.50` / `0.60`** を堅持しています。

---

## 🔬 テストと検証
Cross-Python Validation Summary
24 regression cases (test_v1_3_full_suite.py): PASSED

5 compatibility tests (test_v1_3_regression.py): PASSED

6 edge-case & parallel determinism tests (test_v1_3_edge_cases.py): PASSED

81 synthetic threshold configurations (threshold_tuning.py): PASSED

All test suites and synthetic experiments passed completely without errors across Python 3.9, 3.10, 3.11, and 3.12.

Threshold Calibration & Synthetic Validation
閾値パラメータ（H3 Multiset Jaccard: 0.50, H7 Weighted Bi-gram Dice: 0.60）は、合成検証ペアセット（Positive 6ペア / Negative 3ペア）を用いて設計・キャリブレーションされました。
本エンジンが出力する 1110-111 は、現在の7観測空間における完全一致（Observation Clones）を示すものであり、完全な意味論的等価性（Semantic Clones）を保証するものではありません。

---

## 📚 ドキュメント

- 🏛️ アーキテクチャ仕様書

- 🔌 API & 統合ガイド

- 🚀 デプロイメントガイド

- 🔐 CI/CD & セキュリティガイド

## 📄 ライセンス
MIT License。詳細は LICENSE を参照してください。

## 👤 Author
Kai IWASAKI
