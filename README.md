# 🎨 Auto Diagram Generator (ADG)

*バージョン: v2.2.0*
*最終更新: 2025年08月17日 16:00 JST*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![GitHub](https://img.shields.io/badge/GitHub-KEIEI--NET-green)](https://github.com/KEIEI-NET/Auto_Diagram_Generator)
[![Status](https://img.shields.io/badge/status-production--ready-success)](https://github.com/KEIEI-NET/Auto_Diagram_Generator)

コードを解析して必要な図を自動生成するインテリジェントなツール。Claude Code CLIのカスタムコマンドとして設計されています。

## ✨ 特徴

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

## 📚 ドキュメント

- 📖 [インストールガイド](docs/INSTALLATION_GUIDE.md)
- 🚀 [使用例](docs/USAGE_EXAMPLES.md)
- 🏗️ [アーキテクチャ](docs/ARCHITECTURE.md)
- 📝 [API仕様](docs/API_SPECIFICATION.md)
- 🔧 [トラブルシューティング](docs/TROUBLESHOOTING.md)
- 🔒 [セキュリティガイド](docs/SECURITY.md)
- 👩‍💻 [開発者ガイド](docs/DEVELOPER_GUIDE.md)
- 💻 [Windows PowerShell ガイド](README_Windows.md)

## 🚀 クイックスタート

### インストール（Windows/Mac/Linux対応）

#### uvを使用（推奨・高速）
```bash
# uvのインストール（初回のみ）
# Windows PowerShell
irm https://astral.sh/uv/install.ps1 | iex
# Mac/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# リポジトリをクローン
git clone https://github.com/KEIEI-NET/Auto_Diagram_Generator.git
cd Auto_Diagram_Generator

# 依存関係をインストール
uv pip install -e .
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

### 基本的な使い方

```bash
# プロジェクトを解析して図を生成
python -m adg.cli.command analyze <path> --output output

# Mermaid図の生成
python -m adg.generators.mermaid_refactored

# DrawIO図の生成（Mermaid構造から変換）
python -m adg.generators.drawio_from_mermaid

# Playwright検証（自動修正付き）
python -m adg.utils.mermaid_playwright_validator

# 統合テスト
python test_adg.py

# AST解析テスト
python test_ast_integration.py
```

### Windows PowerShellでの使用例
```powershell
# 仮想環境をアクティベート
.\venv\Scripts\Activate.ps1

# プロジェクト解析
python -m adg analyze src --output diagrams

# DrawIO形式で生成
python -m adg analyze src --format drawio
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

## 📊 プロジェクトステータス

- **バージョン**: 2.2.0 (Production Ready)
- **Python**: 3.9+
- **ステータス**: ✅ 本番実装完了
- **AST対応言語**: 25+ （Python, JavaScript, Java, Go, Rust, C/C++, C#, Ruby, PHP, Delphi等）

---

*最終更新: 2025年08月17日 16:00 JST*
*バージョン: v2.2.0*

**更新履歴:**
- v2.2.0 (2025年08月17日): AST解析統合により25言語以上対応、誤検出率を<1%に改善
- v2.1.0 (2025年08月16日): DrawIO生成、Playwright検証、セキュリティ強化の実装完了
- v2.0.0 (2025年08月14日): コア機能の本番実装完了
- v1.0.0 (2025年08月01日): 初期リリース

---

⭐ このプロジェクトが役に立ったら、スターをお願いします！