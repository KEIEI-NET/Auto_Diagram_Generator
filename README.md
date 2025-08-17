# 🎨 Auto Diagram Generator (ADG)

*バージョン: v2.2.1*
*最終更新: 2025年01月17日 18:45 JST*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![GitHub](https://img.shields.io/badge/GitHub-KEIEI--NET-green)](https://github.com/KEIEI-NET/Auto_Diagram_Generator)
[![Status](https://img.shields.io/badge/status-production--ready-success)](https://github.com/KEIEI-NET/Auto_Diagram_Generator)

コードを解析して必要な図を自動生成するインテリジェントなツール。Claude Code CLIのカスタムコマンド（スラッシュコマンド）として設計されています。

Intelligent tool for automatically generating diagrams from code analysis. Designed as a custom command (slash command) for Claude Code CLI.

## ✨ 特徴 / Features

### 日本語
- 🔍 **自動判定**: コード内容から必要な図を自動で判定
- 📊 **多様な図種対応**: 30種類以上の図に対応
- 🎯 **マルチフォーマット**: Mermaid、DrawIO形式で出力（PlantUML準備中）
- ⚡ **インクリメンタル更新**: 変更があったファイルのみを効率的に更新
- 🌏 **東京時間対応**: すべてのタイムスタンプはJST（UTC+9）
- 🔒 **セキュリティ強化**: パストラバーサル対策、入力検証実装済み
- 🎭 **Playwright検証**: ブラウザでの実際のレンダリング検証と自動修正
- 💎 **DrawIO生成**: Mermaid構造からDrawIO XML形式への自動変換
- 🪟 **Windows完全対応**: uvパッケージマネージャーとPowerShellサポート
- 🧬 **AST解析統合**: 25言語以上の高精度AST解析（誤検出率<1%）
- 🏛️ **Delphi/Pascal対応**: レガシーDelphiコードの完全サポート

### English
- 🔍 **Auto Detection**: Automatically determines required diagrams from code
- 📊 **30+ Diagram Types**: Support for various diagram types
- 🎯 **Multi-Format**: Output in Mermaid and DrawIO formats (PlantUML coming soon)
- ⚡ **Incremental Updates**: Efficiently updates only changed files
- 🌏 **Tokyo Time**: All timestamps in JST (UTC+9)
- 🔒 **Enhanced Security**: Path traversal protection and input validation
- 🎭 **Playwright Validation**: Browser rendering validation with auto-fix
- 💎 **DrawIO Generation**: Automatic conversion from Mermaid to DrawIO XML
- 🪟 **Full Windows Support**: uv package manager and PowerShell support
- 🧬 **AST Integration**: High-precision AST analysis for 25+ languages (<1% false positive rate)
- 🏛️ **Delphi/Pascal Support**: Full support for legacy Delphi code

## 📚 ドキュメント / Documentation

### 日本語
- 📖 [インストールガイド](docs/INSTALLATION_GUIDE.md)
- 🚀 [使用例](docs/USAGE_EXAMPLES.md)
- 💻 [CLIコマンド詳細](docs/CLI_USAGE.md)
- 📊 [対応フォーマット一覧](docs/SUPPORTED_FORMATS.md)
- 🏗️ [アーキテクチャ](docs/ARCHITECTURE.md)
- 📝 [API仕様](docs/API_SPECIFICATION.md)
- 🔧 [トラブルシューティング](docs/TROUBLESHOOTING.md)
- 🔒 [セキュリティガイド](docs/SECURITY.md)
- 👩‍💻 [開発者ガイド](docs/DEVELOPER_GUIDE.md)
- 💻 [Windows PowerShell ガイド](README_Windows.md)

### English
- 📖 [Installation Guide](docs/INSTALLATION_GUIDE.md)
- 🚀 [Usage Examples](docs/USAGE_EXAMPLES.md)
- 💻 [CLI Command Details](docs/CLI_USAGE.md)
- 📊 [Supported Formats](docs/SUPPORTED_FORMATS.md)
- 🏗️ [Architecture](docs/ARCHITECTURE.md)
- 📝 [API Specification](docs/API_SPECIFICATION.md)
- 🔧 [Troubleshooting](docs/TROUBLESHOOTING.md)
- 🔒 [Security Guide](docs/SECURITY.md)
- 👩‍💻 [Developer Guide](docs/DEVELOPER_GUIDE.md)
- 💻 [Windows PowerShell Guide](README_Windows.md)

## 🚀 クイックスタート / Quick Start

### インストール（Windows/Mac/Linux対応） / Installation

#### uvを使用（推奨・高速） / Using uv (Recommended, Fast)
```bash
# uvのインストール（初回のみ） / Install uv (first time only)
# Windows PowerShell
irm https://astral.sh/uv/install.ps1 | iex
# Mac/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# リポジトリをクローン / Clone repository
git clone https://github.com/KEIEI-NET/Auto_Diagram_Generator.git
cd Auto_Diagram_Generator

# 依存関係をインストール / Install dependencies
uv pip install -e .

# AST解析機能を追加（推奨） / Add AST analysis (recommended)
uv pip install -r requirements_ast_parsers.txt

# Playwright検証を追加（オプション） / Add Playwright validation (optional)
uv pip install playwright
playwright install chromium
```

#### 従来のpipを使用
```bash
# リポジトリをクローン
git clone https://github.com/KEIEI-NET/Auto_Diagram_Generator.git
cd Auto_Diagram_Generator

# 仮想環境を作成（推奨）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# パッケージをインストール
pip install -r requirements.txt

# AST解析機能（推奨）
pip install -r requirements_ast_parsers.txt

# Playwright（オプション）
pip install playwright
playwright install chromium
```

### 基本的な使い方 / Basic Usage

#### スラッシュコマンドとして使用 / As Slash Command
```bash
# Claude Code CLI内で使用 / Use within Claude Code CLI
/adg analyze <path> --format mermaid
/adg generate <path> --types class,flow --output diagrams
```

#### Pythonモジュールとして使用 / As Python Module
```bash
# プロジェクトを解析して図を生成 / Analyze project and generate diagrams
python -m adg.cli.command analyze <path> --output output

# 特定の図種を生成 / Generate specific diagram types
python -m adg.cli.command generate <path> --types class,er,sequence --format mermaid

# Delphiプロジェクトを解析 / Analyze Delphi project
python analyze_delphi_direct.py --input path/to/delphi/file.pas

# Mermaid図の生成 / Generate Mermaid diagrams
python -m adg.generators.mermaid_refactored

# DrawIO図の生成（Mermaid構造から変換） / Generate DrawIO diagrams
python -m adg.generators.drawio_from_mermaid

# Playwright検証（自動修正付き） / Playwright validation with auto-fix
python -m adg.utils.mermaid_playwright_validator

# 統合テスト / Integration test
python test_adg.py

# AST解析テスト / AST analysis test
python test_ast_integration.py
```

### Windows PowerShellでの使用例 / Windows PowerShell Examples
```powershell
# 仮想環境をアクティベート / Activate virtual environment
.\venv\Scripts\Activate.ps1

# プロジェクト解析 / Analyze project
python -m adg analyze src --output diagrams

# DrawIO形式で生成 / Generate in DrawIO format
python -m adg analyze src --format drawio

# Delphiファイル解析 / Analyze Delphi file
python analyze_delphi_direct.py --input "C:\Projects\DelphiApp\Main.pas"
```

## 📊 対応図種

### 実装済み ✅
- **クラス図**: 完全実装（継承、関連、属性、メソッド）
- **ER図**: エンティティと属性の表現
- **シーケンス図**: 参加者とメッセージフロー
- **フロー図**: ノードとエッジの関係
- **DrawIO変換**: 上記すべての図をDrawIO XML形式で出力

### 実装中 🚧
- **コンポーネント図**: 基本構造実装中
- **アクティビティ図**: フロー制御の拡張
- **ステートチャート図**: 状態遷移の実装

### 計画中 📋
- ユースケース図、コミュニケーション図、タイミング図
- システム構成図、ネットワーク図、データフロー図
- 画面遷移図、ワイヤーフレーム、サイトマップ
- その他15種類以上

## 🏗️ プロジェクト構造

```
Auto_Diagram_Generator/
├── docs/               # ドキュメント
├── src/adg/           # ソースコード
│   ├── core/          # コア機能
│   │   ├── analyzer.py          # プロジェクト解析
│   │   ├── ast_analyzers.py     # AST解析器（25言語対応）
│   │   ├── integrated_analyzer.py # 統合アナライザー
│   │   └── language_parsers.py  # 言語別パーサー
│   ├── generators/    # 図生成器
│   ├── utils/         # ユーティリティ
│   └── cli/           # CLIインターフェース
├── tests/             # テストコード
├── config/            # 設定ファイル
└── output/            # 生成図出力先
```

## 🔒 セキュリティ

このプロジェクトはセキュリティを重視して開発されています：

- ✅ パストラバーサル攻撃対策
- ✅ 入力検証とサニタイゼーション
- ✅ セキュアなファイルパス処理
- ✅ 環境変数による開発モード制御

詳細は[セキュリティガイド](docs/SECURITY.md)をご覧ください。

## 🤝 コントリビューション

プルリクエストを歓迎します！

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/AmazingFeature`)
3. 変更をコミット (`git commit -m 'Add some AmazingFeature'`)
4. ブランチにプッシュ (`git push origin feature/AmazingFeature`)
5. プルリクエストを作成

開発に参加する前に[開発者ガイド](docs/DEVELOPER_GUIDE.md)をご確認ください。

## 📝 ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルをご覧ください。

## 👥 作者

**KEIEI-NET**
- GitHub: [@KEIEI-NET](https://github.com/KEIEI-NET)

## 🙏 謝辞

このプロジェクトは以下のツールとライブラリに依存しています：

- [Click](https://click.palletsprojects.com/) - CLIフレームワーク
- [Rich](https://rich.readthedocs.io/) - 美しいターミナル出力
- [Loguru](https://github.com/Delgan/loguru) - ロギング
- [Tree-sitter](https://tree-sitter.github.io/) - 20言語以上のAST解析
- [Esprima](https://esprima.org/) - JavaScript/TypeScript AST解析
- [Javalang](https://github.com/c2nes/javalang) - Java AST解析

## 🌐 対応言語 / Supported Languages

### プログラミング言語（AST解析対応） / Programming Languages (with AST analysis)
- **主要言語**: Python, JavaScript, TypeScript, Java, C++, C#, Go, Rust
- **Web言語**: PHP, Ruby, HTML/CSS, JSX/TSX
- **レガシー言語**: Delphi/Pascal, Visual Basic, COBOL
- **スクリプト言語**: Shell Script, PowerShell, Perl
- **その他**: Swift, Kotlin, Scala, R, MATLAB, SQL

詳細は[対応フォーマット一覧](docs/SUPPORTED_FORMATS.md)を参照してください。

## 📊 プロジェクトステータス

- **バージョン**: 2.2.1 (Production Ready)
- **Python**: 3.9+
- **ステータス**: ✅ 本番実装完了
- **AST対応言語**: 25+ （Python, JavaScript, Java, Go, Rust, C/C++, C#, Ruby, PHP, Delphi等）

---

*最終更新: 2025年01月17日 18:45 JST*
*バージョン: v2.2.1*

**更新履歴:**
- v2.2.1 (2025年01月17日): ドキュメント更新、CLIコマンド詳細追加、Delphi対応強化
- v2.2.0 (2025年08月17日): AST解析統合により25言語以上対応、誤検出率を<1%に改善
- v2.1.0 (2025年08月16日): DrawIO生成、Playwright検証、セキュリティ強化の実装完了
- v2.0.0 (2025年08月14日): コア機能の本番実装完了
- v1.0.0 (2025年08月01日): 初期リリース

---

⭐ このプロジェクトが役に立ったら、スターをお願いします！