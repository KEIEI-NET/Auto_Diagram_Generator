# 📚 Auto Diagram Generator ドキュメント

*バージョン: v2.2.0*
*最終更新: 2025年08月17日 16:00 JST*

## ドキュメント体系

Auto Diagram Generator (ADG) の包括的なドキュメントセットです。
目的に応じて適切なドキュメントをご参照ください。

## 🚀 はじめに

- 📖 **[README](../README.md)** - プロジェクト概要とクイックスタート
- 📋 **[CHANGELOG](../CHANGELOG.md)** - バージョン履歴と変更内容
- 📝 **[LICENSE](../LICENSE)** - ライセンス情報

## 🛠️ セットアップと使用方法

- 💾 **[インストールガイド](INSTALLATION_GUIDE.md)** - 詳細なインストール手順
- 🎯 **[使用例](USAGE_EXAMPLES.md)** - 実践的な使用例とベストプラクティス
- 🔧 **[トラブルシューティング](TROUBLESHOOTING.md)** - 問題解決ガイド
- 💻 **[Windows PowerShellガイド](../README_Windows.md)** - Windows環境での使用方法

## 🏗️ 技術仕様

- 🏛️ **[アーキテクチャ](ARCHITECTURE.md)** - システム設計と構成 **[v2.2.0更新]**
- 📡 **[API仕様](API_SPECIFICATION.md)** - APIリファレンス
- 🔒 **[セキュリティガイド](SECURITY.md)** - セキュリティ設計と実装

## 🧬 AST解析機能 (v2.2.0 新機能)

- 🎯 **[AST統合サマリー](AST_INTEGRATION_SUMMARY.md)** - AST解析の技術仕様と実装詳細 **[NEW]**
- ✅ **[AST統合完了報告](AST_INTEGRATION_COMPLETE.md)** - 実装完了レポート
- 📋 **[ASTパーサー要件](AST_PARSER_REQUIREMENTS.md)** - パーサー要件定義

## 👩‍💻 開発者向け

- 📘 **[開発者ガイド](DEVELOPER_GUIDE.md)** - 開発環境構築とコーディング規約 **[v2.2.0更新]**
- 📋 **[仕様書](../SPECIFICATION.md)** - 詳細な機能仕様
- 🗺️ **[実装計画](../IMPLEMENTATION_PLAN.md)** - 開発ロードマップ
- 💬 **[Claude.md](../CLAUDE.md)** - AI開発支援ガイド

## 📊 機能別ドキュメント

### コア機能
- **コード解析**: AST解析による25言語以上のサポート
- **図種判定**: 30種類以上の図の自動判定
- **エラー処理**: 自動フォールバックとエラー修正

### 図生成フォーマット
- **Mermaid**: テキストベース図生成
- **DrawIO**: XML形式での図生成
- **PlantUML**: (準備中)

### 検証機能
- **Playwright検証**: ブラウザベースの検証
- **自動修正**: 構文エラーの自動修正

## 🔄 更新情報

### v2.2.0 (2025年08月17日) の主な更新
- 📚 AST解析統合により25言語以上に対応
- 🎯 誤検出率を30-40%から<1%に改善
- 📖 ドキュメント体系の大幅な拡充
- 🔧 開発者ガイドのAST関連情報追加

## 🎯 クイックリンク

### 新規ユーザー向け
1. [インストールガイド](INSTALLATION_GUIDE.md)
2. [使用例](USAGE_EXAMPLES.md)
3. [トラブルシューティング](TROUBLESHOOTING.md)

### 開発者向け
1. [開発者ガイド](DEVELOPER_GUIDE.md)
2. [アーキテクチャ](ARCHITECTURE.md)
3. [AST統合サマリー](AST_INTEGRATION_SUMMARY.md)

### 管理者向け
1. [セキュリティガイド](SECURITY.md)
2. [API仕様](API_SPECIFICATION.md)
3. [CHANGELOG](../CHANGELOG.md)

## 📝 ドキュメント管理

### バージョニング
すべてのドキュメントは以下の形式でバージョン管理されています：
- バージョン番号: セマンティックバージョニング (v.X.Y.Z)
- タイムスタンプ: 東京時間 (JST) YYYY年MM月DD日 HH:mm

### 更新ポリシー
- **Major更新**: アーキテクチャ変更時
- **Minor更新**: 新機能追加時
- **Patch更新**: バグ修正・誤字修正時

## 🤝 コントリビューション

ドキュメントの改善提案は歓迎します：
1. Issue を作成して議論
2. Pull Request で修正提案
3. [開発者ガイド](DEVELOPER_GUIDE.md)のガイドラインに従う

## 📮 お問い合わせ

- GitHub Issues: バグ報告・機能要望
- GitHub Discussions: 質問・議論
- Pull Requests: コード・ドキュメント改善

---

*最終更新: 2025年08月17日 16:00 JST*
*バージョン: v2.2.0*

**更新履歴:**
- v2.2.0 (2025年08月17日): ドキュメントインデックス作成、AST関連ドキュメントの統合