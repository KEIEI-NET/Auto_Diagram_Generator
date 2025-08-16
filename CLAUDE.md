# CLAUDE.md

*バージョン: v2.1.0*
*最終更新: 2025年08月16日 14:30 JST*

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

これは自動図生成ツール（Auto Diagram Generator: ADG）プロジェクトです。Claude Code CLIのカスタムコマンドとして、コードを解析して必要な図を自動生成するインテリジェントなツールです。コード内容から適切な図の種類を自動判定し、複数のフォーマット（Mermaid、PlantUML、Draw.io）で出力します。

### 最新実装状況（2025年8月）
- ✅ **DrawIO生成機能**: Mermaidの構造を基にDrawIO XML形式の図を自動生成
- ✅ **Playwright検証**: ブラウザでのMermaidレンダリング検証と自動エラー修正
- ✅ **セキュリティ強化**: パストラバーサル対策、入力検証、セキュアなファイル処理
- ✅ **Windows完全対応**: uv パッケージマネージャーとPowerShellコマンドのサポート
- ✅ **ASTビジターパターン**: 効率的なコード解析のためのリファクタリング

## プロジェクトアーキテクチャ

### コア機能

1. **自動図判定機能**: コード内容を解析して必要な図を自動で判定
2. **マルチフォーマット対応**: Mermaid、PlantUML、Draw.io形式での出力
3. **バージョン管理**: 東京時間（JST）でのタイムスタンプとセマンティックバージョニング
4. **インクリメンタル更新**: 変更があったファイルのみを対象とした効率的な更新

### 対応図種（30種類以上）

- **構造図**: ER図、クラス図、コンポーネント図、配置図、パッケージ図
- **振る舞い図**: フロー図、アクティビティ図、シーケンス図、ステートチャート図、ユースケース図、コミュニケーション図、タイミング図
- **システム設計図**: システム構成図、ネットワーク図、データフロー図、制御フロー図、コンテキスト図
- **UI設計図**: 画面遷移図、ワイヤーフレーム、モックアップ、サイトマップ
- **分析・管理図**: CRUD図、マトリックス図、ドメインモデル図、プロセス図、決定表、決定木、組織図、ガントチャート、PERT図

## 開発コマンド

### セットアップ（Windows/Mac/Linux）

```bash
# uvを使用したセットアップ（推奨）
uv pip install -e .

# または従来のpip
pip install -r requirements.txt

# Playwright（オプション）
pip install playwright
playwright install chromium
```

### 実行コマンド

```bash
# 基本的な解析と図生成
python -m adg.cli.command analyze <path> --output <output_dir>

# Mermaid図の生成
python -m adg.generators.mermaid_refactored

# DrawIO図の生成（Mermaidから変換）
python -m adg.generators.drawio_from_mermaid

# Playwright検証（自動修正付き）
python -m adg.utils.mermaid_playwright_validator
```

### テストとデバッグ

```bash
# 統合テスト
python test_adg.py

# Playwrightテスト（ブラウザ表示）
python -m adg.utils.mermaid_playwright_validator --headless=false
```

## 実装ガイドライン

### 6フェーズの段階的開発

1. プロジェクト構造のセットアップと基本設定
2. コード解析モジュールの実装
3. 図種別判定ロジックの実装
4. 各フォーマットでの図生成機能
5. バージョン管理とインクリメンタル更新機能
6. テストと最適化

### 重要な技術的考慮事項

- **AI統合**: Claude APIと連携したインテリジェントなコード解析
- **キャッシング**: 変更のない図の再生成を避けるキャッシュ機能
- **エラーハンドリング**: 様々なコードパターンに対する包括的なエラー処理
- **ロギング**: 図生成プロセスのデバッグ用詳細ログ

### ファイル命名規則

生成される図のファイル名パターン：
`{プロジェクト名}_{図種別}_{バージョン}_{タイムスタンプ}.{フォーマット}`

例: `myproject_class-diagram_v1.0.0_20240816-143000.mermaid`

## 実装済み機能

### コア機能
1. **コード解析器** (`src/adg/core/analyzer.py`)
   - ASTベースのPythonコード解析
   - クラス、関数、依存関係の抽出
   - プロジェクト構造の包括的分析

2. **図生成器** (`src/adg/generators/`)
   - **Mermaid生成器**: リファクタリング済み、ビルダーパターン採用
   - **DrawIO生成器**: Mermaid構造からXML形式への変換
   - 自動レイアウト計算機能

3. **検証システム** (`src/adg/utils/`)
   - **Playwright検証器**: ブラウザでの実際のレンダリング検証
   - **自動エラー修正**: 一般的なMermaidエラーの自動修正
   - スクリーンショット生成とレポート機能

4. **セキュリティ機能** (`src/adg/utils/security.py`)
   - パストラバーサル攻撃防御
   - 入力サニタイゼーション
   - セキュアなファイルパス処理

## 技術スタック

- **言語**: Python 3.9+
- **依存管理**: uv (推奨) / pip
- **図生成**: Mermaid, DrawIO XML
- **検証**: Playwright (Chromium)
- **ロギング**: Loguru
- **型チェック**: MyPy
- **フォーマット**: Black, isort

## 重要事項

- ✅ 本番実装コード完成（2025年8月）
- ✅ Claude Code CLIとの統合準備完了
- ✅ すべてのタイムスタンプは東京時間（JST/UTC+9）を使用
- ✅ インクリメンタル更新とキャッシング対応
- ✅ Windows/Mac/Linux完全対応

---

*最終更新: 2025年08月16日 14:30 JST*
*バージョン: v2.1.0*

**更新履歴:**
- v2.1.0 (2025年08月16日): DrawIO生成、Playwright検証、セキュリティ強化の実装完了