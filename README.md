# 🎨 Auto Diagram Generator (ADG)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![GitHub](https://img.shields.io/badge/GitHub-KEIEI--NET-green)](https://github.com/KEIEI-NET/Auto_Diagram_Generator)

コードを解析して必要な図を自動生成するインテリジェントなツール。Claude Code CLIのカスタムコマンドとして設計されています。

## ✨ 特徴

- 🔍 **自動判定**: コード内容から必要な図を自動で判定
- 📊 **多様な図種対応**: 30種類以上の図に対応予定
- 🎯 **マルチフォーマット**: Mermaid、PlantUML、Draw.io形式で出力
- ⚡ **インクリメンタル更新**: 変更があったファイルのみを効率的に更新
- 🌏 **東京時間対応**: すべてのタイムスタンプはJST（UTC+9）

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

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/KEIEI-NET/Auto_Diagram_Generator.git
cd Auto_Diagram_Generator

# 仮想環境を作成（推奨）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# パッケージをインストール
pip install -e .
```

### 基本的な使い方

```bash
# プロジェクトを解析
adg analyze

# 図を自動生成
adg generate --auto

# 特定の図種を生成
adg generate --types class er sequence

# ヘルプを表示
adg --help
```

## 📊 対応図種

### 実装済み ✅
- クラス図（基本実装）

### 実装中 🚧
- ER図
- シーケンス図
- フロー図
- コンポーネント図

### 計画中 📋
- アクティビティ図、ステートチャート図、ユースケース図
- システム構成図、ネットワーク図、データフロー図
- 画面遷移図、ワイヤーフレーム、サイトマップ
- その他20種類以上

## 🏗️ プロジェクト構造

```
Auto_Diagram_Generator/
├── docs/               # ドキュメント
├── src/adg/           # ソースコード
│   ├── core/          # コア機能
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
- [Tree-sitter](https://tree-sitter.github.io/) - コード解析

## 📊 プロジェクトステータス

- **バージョン**: 0.1.0 (Alpha)
- **Python**: 3.9+
- **ステータス**: 🚧 開発中

---

⭐ このプロジェクトが役に立ったら、スターをお願いします！