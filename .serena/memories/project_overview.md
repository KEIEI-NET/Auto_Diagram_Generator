# Auto Diagram Generator (ADG) - プロジェクト概要

## プロジェクトの目的
コードを解析して必要な図を自動生成するインテリジェントなツール。Claude Code CLIのカスタムコマンドとして開発されている。

## 技術スタック
- **言語**: Python 3.9+
- **CLI**: Click
- **UI**: Rich (コンソール表示)
- **ログ**: Loguru
- **コード解析**: AST (標準ライブラリ)、Tree-sitter、Astroid
- **図生成**: Mermaid、GraphViz
- **設定管理**: PyYAML
- **開発ツール**: Black (フォーマッタ), Flake8 (リンタ), MyPy (型チェック), Pytest (テスト)

## 主要機能
1. **自動判定**: コード内容から必要な図を自動で判定
2. **複数図種対応**: クラス図、ER図、シーケンス図、フロー図、コンポーネント図等
3. **多フォーマット**: Mermaid、PlantUML、Draw.io形式
4. **バージョン管理**: 東京時間でのタイムスタンプ付きファイル生成

## ディレクトリ構造
```
src/adg/
├── cli/          # CLIコマンド
├── core/         # コア機能（解析、判定）
├── generators/   # 図生成器
└── utils/        # ユーティリティ
```

## エントリーポイント
- `adg` コマンド（setup.pyで定義）
- メインモジュール: `adg.cli.command`