# 📖 CLI コマンド詳細ガイド / CLI Command Detailed Guide

*バージョン: v1.0.0*
*最終更新: 2025年01月17日 18:45 JST*

## 📑 目次 / Table of Contents

1. [概要 / Overview](#概要--overview)
2. [インストールと設定 / Installation and Setup](#インストールと設定--installation-and-setup)
3. [基本コマンド / Basic Commands](#基本コマンド--basic-commands)
4. [高度な使用方法 / Advanced Usage](#高度な使用方法--advanced-usage)
5. [スラッシュコマンドとして使用 / Using as Slash Command](#スラッシュコマンドとして使用--using-as-slash-command)
6. [実践例 / Practical Examples](#実践例--practical-examples)
7. [トラブルシューティング / Troubleshooting](#トラブルシューティング--troubleshooting)

## 概要 / Overview

Auto Diagram Generator (ADG) は、コマンドラインから簡単に使用できる図生成ツールです。Claude Code CLIのスラッシュコマンドとしても動作します。

ADG is a diagram generation tool that can be easily used from the command line. It also works as a slash command for Claude Code CLI.

## インストールと設定 / Installation and Setup

### uvを使用した高速インストール / Fast Installation with uv

```bash
# uvのインストール / Install uv
# Windows PowerShell
irm https://astral.sh/uv/install.ps1 | iex

# Mac/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# パッケージインストール / Install package
cd Auto_Diagram_Generator
uv pip install -e .
uv pip install -r requirements_ast_parsers.txt  # AST解析機能 / AST analysis
```

### 環境変数の設定 / Environment Variables

```bash
# 開発モードの有効化 / Enable development mode
export ADG_DEV_MODE=1  # Linux/Mac
set ADG_DEV_MODE=1     # Windows CMD
$env:ADG_DEV_MODE="1"  # Windows PowerShell

# タイムゾーン設定（東京時間） / Set timezone (Tokyo)
export TZ='Asia/Tokyo'  # Linux/Mac
set TZ=Asia/Tokyo       # Windows CMD
$env:TZ="Asia/Tokyo"    # Windows PowerShell
```

## 基本コマンド / Basic Commands

### 1. analyze - プロジェクト解析 / Project Analysis

```bash
# 基本構文 / Basic syntax
adg analyze [PATH] [OPTIONS]
python -m adg.cli.command analyze [PATH] [OPTIONS]

# オプション / Options
--output, -o    : 出力ディレクトリ（デフォルト: output）
--format, -f    : 出力フォーマット（mermaid|plantuml|drawio|all）
--verbose, -v   : 詳細情報を表示

# 例 / Examples
adg analyze ./src --output ./diagrams --format mermaid
adg analyze . --verbose  # カレントディレクトリを詳細解析
```

### 2. generate - 図の生成 / Generate Diagrams

```bash
# 基本構文 / Basic syntax
adg generate [PATH] [OPTIONS]
python -m adg.cli.command generate [PATH] [OPTIONS]

# オプション / Options
--output, -o    : 出力ディレクトリ
--format, -f    : 出力フォーマット（mermaid|plantuml|drawio|all）
--types, -t     : 生成する図の種類（複数指定可）
--auto, -a      : 自動判定した図をすべて生成

# 例 / Examples
adg generate ./src --types class,er,sequence --format mermaid
adg generate . --auto --output ./docs/diagrams
adg generate ./project --types flow --format drawio
```

### 3. list-types - 対応図種一覧 / List Diagram Types

```bash
# すべての対応図種を表示 / Show all supported diagram types
adg list-types
python -m adg.cli.command list-types
```

## 高度な使用方法 / Advanced Usage

### Delphiプロジェクトの解析 / Analyzing Delphi Projects

```bash
# Delphiファイルの直接解析 / Direct Delphi file analysis
python analyze_delphi_direct.py --input path/to/file.pas

# Windows環境での例 / Windows example
python analyze_delphi_direct.py --input "C:\DelphiProjects\Main.pas"

# 出力ディレクトリ指定 / Specify output directory
python analyze_delphi_direct.py --input file.pas --output ./delphi_diagrams
```

### バッチ処理 / Batch Processing

```bash
# 複数プロジェクトの一括処理 / Process multiple projects
for dir in project1 project2 project3; do
    adg generate "./$dir" --auto --output "./$dir/docs"
done

# Windows PowerShell
@("project1", "project2", "project3") | ForEach-Object {
    python -m adg generate "./$_" --auto --output "./$_/docs"
}
```

### カスタム設定ファイルの使用 / Using Custom Configuration

```yaml
# config/diagram-generator.yaml
output:
  format: mermaid
  directory: ./diagrams
  timestamp: true
  version: true

analysis:
  languages:
    - python
    - javascript
    - delphi
  exclude:
    - "*.test.*"
    - "*_test.*"
    - "test_*"

diagrams:
  auto_detect: true
  types:
    - class
    - er
    - sequence
    - flow
```

```bash
# 設定ファイルを使用 / Use configuration file
adg generate . --config config/diagram-generator.yaml
```

## スラッシュコマンドとして使用 / Using as Slash Command

### Claude Code CLI内での使用 / Usage in Claude Code CLI

```bash
# Claude Code CLI内で直接実行 / Direct execution in Claude Code CLI
/adg analyze ./src
/adg generate . --types class,flow
/adg list-types

# カスタムコマンドとして登録 / Register as custom command
# ~/.claude/commands/adg.yaml
name: adg
description: Auto Diagram Generator
command: python -m adg.cli.command
args:
  - analyze
  - generate
  - list-types
```

### VSCode統合 / VSCode Integration

```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Generate Diagrams",
      "type": "shell",
      "command": "python",
      "args": [
        "-m",
        "adg.cli.command",
        "generate",
        "${workspaceFolder}",
        "--auto",
        "--format",
        "drawio"
      ],
      "problemMatcher": [],
      "group": {
        "kind": "build",
        "isDefault": true
      }
    }
  ]
}
```

## 実践例 / Practical Examples

### 例1: Pythonプロジェクトの完全解析 / Example 1: Complete Python Project Analysis

```bash
# プロジェクトをクローン / Clone project
git clone https://github.com/example/python-app.git
cd python-app

# 完全解析と図生成 / Complete analysis and diagram generation
adg analyze . --verbose
adg generate . --auto --format all --output ./documentation/diagrams

# 結果確認 / Check results
ls -la ./documentation/diagrams/
```

### 例2: Delphiレガシーコードのドキュメント化 / Example 2: Documenting Delphi Legacy Code

```powershell
# Windows PowerShell
$delphiPath = "C:\LegacySystem\DelphiApp"
$outputPath = "C:\Documentation\DelphiDiagrams"

# 解析と図生成 / Analysis and diagram generation
python analyze_delphi_direct.py --input "$delphiPath\Main.pas"
python -m adg generate $delphiPath --types class,flow,component --output $outputPath

# DrawIO形式に変換 / Convert to DrawIO format
python -m adg.generators.drawio_from_mermaid --input $outputPath --output "$outputPath\drawio"
```

### 例3: CI/CDパイプラインでの自動化 / Example 3: CI/CD Pipeline Automation

```yaml
# .github/workflows/generate-docs.yml
name: Generate Documentation Diagrams

on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - '*.py'

jobs:
  generate-diagrams:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      
      - name: Install ADG
        run: |
          uv pip install -e .
          uv pip install -r requirements_ast_parsers.txt
      
      - name: Generate Diagrams
        run: |
          python -m adg.cli.command analyze . --verbose
          python -m adg.cli.command generate . --auto --format mermaid --output ./docs/diagrams
      
      - name: Commit Diagrams
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add docs/diagrams/
          git commit -m "Auto-generate diagrams [skip ci]" || exit 0
          git push
```

### 例4: 複数言語プロジェクトの解析 / Example 4: Multi-Language Project Analysis

```bash
# Node.js + Python + Goのマルチ言語プロジェクト
# Multi-language project with Node.js + Python + Go

# 言語別に解析 / Analyze by language
adg analyze ./frontend --output ./docs/frontend  # JavaScript/TypeScript
adg analyze ./backend --output ./docs/backend    # Python
adg analyze ./services --output ./docs/services  # Go

# 統合図の生成 / Generate integrated diagrams
adg generate . --types component,system --output ./docs/architecture

# Mermaid検証とDrawIO変換 / Validate Mermaid and convert to DrawIO
python -m adg.utils.mermaid_playwright_validator --input ./docs
python -m adg.generators.drawio_from_mermaid --input ./docs --recursive
```

## トラブルシューティング / Troubleshooting

### よくある問題と解決方法 / Common Issues and Solutions

#### 1. モジュールが見つからない / Module not found

```bash
# エラー / Error
ModuleNotFoundError: No module named 'adg'

# 解決方法 / Solution
pip install -e .  # または / or
uv pip install -e .
```

#### 2. パスのセキュリティエラー / Path security error

```bash
# エラー / Error
Error: Path validation failed: Path traversal detected

# 解決方法 / Solution
# 絶対パスを使用 / Use absolute path
adg analyze /home/user/project  # Linux/Mac
adg analyze C:\Users\user\project  # Windows
```

#### 3. Delphiファイルの文字化け / Delphi file encoding issues

```bash
# エラー / Error
UnicodeDecodeError: 'utf-8' codec can't decode

# 解決方法 / Solution
# エンコーディングを指定 / Specify encoding
python analyze_delphi_direct.py --input file.pas --encoding shift-jis
```

#### 4. 図の生成が失敗する / Diagram generation fails

```bash
# Playwright検証で自動修正 / Auto-fix with Playwright validation
python -m adg.utils.mermaid_playwright_validator --input ./output --fix

# ログを確認 / Check logs
cat adg.log | grep ERROR
```

### パフォーマンス最適化 / Performance Optimization

```bash
# キャッシュを有効化 / Enable caching
export ADG_CACHE_ENABLED=1

# 並列処理を使用 / Use parallel processing
adg generate . --parallel --workers 4

# 特定の言語のみ解析 / Analyze specific languages only
adg analyze . --languages python,javascript
```

## 📝 設定ファイルの詳細 / Configuration File Details

### 完全な設定例 / Complete Configuration Example

```yaml
# config/diagram-generator.yaml
version: "1.0"
project:
  name: "MyProject"
  description: "Project diagram generation configuration"

output:
  base_directory: "./documentation/diagrams"
  formats:
    - mermaid
    - drawio
  structure:
    by_type: true  # 図種別でディレクトリ分け
    by_date: false # 日付別ディレクトリ
  naming:
    pattern: "{project}_{type}_{version}_{timestamp}"
    timestamp_format: "%Y%m%d_%H%M%S"
    timezone: "Asia/Tokyo"

analysis:
  languages:
    python:
      enabled: true
      extensions: [".py", ".pyx"]
    javascript:
      enabled: true
      extensions: [".js", ".jsx", ".ts", ".tsx"]
    delphi:
      enabled: true
      extensions: [".pas", ".dpr", ".dfm"]
  exclude_patterns:
    - "**/test/**"
    - "**/tests/**"
    - "**/__pycache__/**"
    - "**/node_modules/**"
    - "**/vendor/**"
  max_file_size: 10485760  # 10MB

diagrams:
  auto_detect: true
  default_types:
    - class
    - er
    - flow
  type_settings:
    class:
      show_private: false
      show_methods: true
      show_attributes: true
    er:
      show_relationships: true
      show_cardinality: true
    flow:
      max_depth: 5
      show_conditions: true

security:
  validate_paths: true
  max_path_length: 260
  allowed_extensions:
    - ".py"
    - ".js"
    - ".ts"
    - ".java"
    - ".pas"
    - ".cpp"
    - ".cs"
    - ".go"
    - ".rs"
    - ".rb"
    - ".php"

cache:
  enabled: true
  directory: "./.adg_cache"
  ttl: 3600  # 1 hour
  max_size: 104857600  # 100MB

logging:
  level: "INFO"
  file: "./adg.log"
  max_size: 10485760  # 10MB
  backup_count: 5
  format: "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
```

## 📚 関連ドキュメント / Related Documentation

- [対応フォーマット一覧](SUPPORTED_FORMATS.md) - 生成可能な図の詳細
- [インストールガイド](INSTALLATION_GUIDE.md) - 詳細なインストール手順
- [トラブルシューティング](TROUBLESHOOTING.md) - 問題解決ガイド
- [開発者ガイド](DEVELOPER_GUIDE.md) - カスタマイズと拡張

---

*最終更新: 2025年01月17日 18:45 JST*
*バージョン: v1.0.0*

**更新履歴:**
- v1.0.0 (2025年01月17日): 初版作成、包括的なCLIコマンドガイド