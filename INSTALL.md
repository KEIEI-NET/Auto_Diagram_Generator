# 📦 Auto Diagram Generator - Installation Guide / インストールガイド

[English](#english) | [日本語](#japanese)

---

<a name="english"></a>
## 🇬🇧 English

### Prerequisites

Before installing ADG, ensure you have:

- **Python 3.10 or higher** (3.12 recommended)
- **Git** (for cloning the repository)
- **pip** or **uv** package manager
- **Windows/macOS/Linux** operating system

### Installation Methods

#### Method 1: Install from GitHub using pip (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/Auto_Diagram_Generator.git
cd Auto_Diagram_Generator

# Create virtual environment (optional but recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install in development mode
pip install -e .

# Verify installation
adg --version
```

#### Method 2: Install from GitHub using uv (Faster)

```bash
# Install uv if not already installed
# Windows PowerShell:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/yourusername/Auto_Diagram_Generator.git
cd Auto_Diagram_Generator

# Install with uv
uv pip install -e .

# Run with uv
uv run adg --version
```

#### Method 3: Direct pip install from GitHub

```bash
# Install directly from GitHub
pip install git+https://github.com/yourusername/Auto_Diagram_Generator.git

# Verify installation
adg --version
```

### Quick Start

1. **Analyze a Python file:**
```bash
adg analyze myfile.py
```

2. **Generate class diagram:**
```bash
adg generate myfile.py --output diagrams --format mermaid --types class
```

3. **Generate all recommended diagrams:**
```bash
adg generate . --output all_diagrams --format all --auto
```

### Configuration

Create a configuration file at `~/.adg/config.yaml`:

```yaml
# ADG Configuration
default_output_dir: "./diagrams"
default_format: "all"
encoding_fallback:
  - utf-8
  - shift-jis
  - cp932
  - latin-1
```

### Troubleshooting

#### Issue: Command not found
```bash
# Use python module execution
python -m adg.cli.command --help
```

#### Issue: Encoding errors with non-ASCII files
```bash
# Set environment variable
export PYTHONIOENCODING=utf-8
```

#### Issue: Missing dependencies
```bash
# Reinstall all dependencies
pip install -r requirements.txt
```

---

<a name="japanese"></a>
## 🇯🇵 日本語

### 前提条件

ADGをインストールする前に、以下を確認してください：

- **Python 3.10以上** （3.12推奨）
- **Git** （リポジトリのクローン用）
- **pip** または **uv** パッケージマネージャー
- **Windows/macOS/Linux** オペレーティングシステム

### インストール方法

#### 方法1: GitHubからpipでインストール（推奨）

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/Auto_Diagram_Generator.git
cd Auto_Diagram_Generator

# 仮想環境の作成（オプションですが推奨）
python -m venv venv

# 仮想環境の有効化
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 開発モードでインストール
pip install -e .

# インストール確認
adg --version
```

#### 方法2: GitHubからuvでインストール（高速）

```bash
# uvがインストールされていない場合
# Windows PowerShell:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# リポジトリをクローン
git clone https://github.com/yourusername/Auto_Diagram_Generator.git
cd Auto_Diagram_Generator

# uvでインストール
uv pip install -e .

# uvで実行
uv run adg --version
```

#### 方法3: GitHubから直接pipインストール

```bash
# GitHubから直接インストール
pip install git+https://github.com/yourusername/Auto_Diagram_Generator.git

# インストール確認
adg --version
```

### クイックスタート

1. **Pythonファイルを解析:**
```bash
adg analyze myfile.py
```

2. **クラス図を生成:**
```bash
adg generate myfile.py --output diagrams --format mermaid --types class
```

3. **推奨される全ての図を生成:**
```bash
adg generate . --output all_diagrams --format all --auto
```

### 設定

設定ファイルを `~/.adg/config.yaml` に作成：

```yaml
# ADG設定
default_output_dir: "./diagrams"
default_format: "all"
encoding_fallback:
  - utf-8
  - shift-jis
  - cp932
  - latin-1
```

### トラブルシューティング

#### 問題: コマンドが見つからない
```bash
# Pythonモジュールとして実行
python -m adg.cli.command --help
```

#### 問題: 非ASCIIファイルのエンコーディングエラー
```bash
# 環境変数を設定
export PYTHONIOENCODING=utf-8
```

#### 問題: 依存関係が不足
```bash
# 全ての依存関係を再インストール
pip install -r requirements.txt
```

## Supported Languages / 対応言語

### Full Support (AST Parsing)
- Python (.py)
- JavaScript/TypeScript (.js, .ts, .jsx, .tsx)
- Java (.java)
- C/C++ (.c, .cpp, .h, .hpp)
- C# (.cs)
- Go (.go)
- Rust (.rs)
- Ruby (.rb)
- PHP (.php)

### Regex-based Support
- Delphi/Pascal (.pas, .dpr, .dfm)
- Kotlin (.kt)
- Swift (.swift)
- Objective-C (.m, .h)
- Scala (.scala)
- R (.r, .R)
- MATLAB (.m)
- Julia (.jl)
- Dart (.dart)
- Lua (.lua)
- Perl (.pl, .pm)
- Shell Script (.sh, .bash)
- PowerShell (.ps1)
- SQL (.sql)
- YAML (.yaml, .yml)
- XML (.xml)
- HTML (.html, .htm)

## Output Formats / 出力フォーマット

- **Mermaid** (.mmd) - Text-based diagrams
- **DrawIO** (.drawio) - Visual diagram editor format
- **PlantUML** (.puml) - Coming soon

## Diagram Types / 図の種類

- Class Diagram / クラス図
- Flowchart / フローチャート
- Component Diagram / コンポーネント図
- Sequence Diagram / シーケンス図
- ER Diagram / ER図
- State Diagram / 状態遷移図
- Activity Diagram / アクティビティ図
- Use Case Diagram / ユースケース図

## System Requirements / システム要件

### Minimum
- CPU: 2 cores
- RAM: 4GB
- Storage: 500MB

### Recommended
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 1GB+

## License

MIT License - See LICENSE file for details

## Support

- GitHub Issues: https://github.com/yourusername/Auto_Diagram_Generator/issues
- Documentation: https://github.com/yourusername/Auto_Diagram_Generator/wiki
- Email: support@example.com

## Contributing

We welcome contributions! Please see CONTRIBUTING.md for guidelines.

---

**Version**: 2.2.1  
**Last Updated**: 2025-01-17 (JST)