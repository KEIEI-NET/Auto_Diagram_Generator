# Auto Diagram Generator (ADG) インストールガイド

*バージョン: v2.1.0*
*最終更新: 2025年08月16日 14:45 JST*

## 目次

1. [システム要件](#システム要件)
2. [クイックインストール](#クイックインストール)
3. [詳細インストール手順](#詳細インストール手順)
4. [開発環境セットアップ](#開発環境セットアップ)
5. [Docker環境](#docker環境)
6. [トラブルシューティング](#トラブルシューティング)
7. [アンインストール](#アンインストール)

## システム要件

### 必須要件

| 項目 | 最小要件 | 推奨要件 |
|------|---------|----------|
| OS | Windows 10, macOS 10.15, Ubuntu 20.04 | 最新バージョン |
| Python | 3.9.0 | 3.11以上 |
| メモリ | 4GB RAM | 8GB RAM以上 |
| ディスク | 500MB | 1GB以上 |
| プロセッサ | 2コア | 4コア以上 |

### 必須ソフトウェア

```bash
# Pythonバージョン確認
python --version  # 3.9.0以上が必要

# pipバージョン確認
pip --version  # 21.0以上を推奨

# Gitバージョン確認（開発用）
git --version  # 2.25以上を推奨
```

### オプショナルソフトウェア

- **uv**: 高速パッケージマネージャー（推奨）
- **Playwright**: ブラウザベースのMermaid検証用
- **Node.js**: Playwright実行時に必要（14.0以上）
- **Chromium**: Playwright検証用ブラウザ

## クイックインストール

### 方法1: uvを使用（推奨・高速）

```bash
# uvのインストール
# Windows PowerShell
irm https://astral.sh/uv/install.ps1 | iex

# Mac/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# リポジトリをクローン
git clone https://github.com/KEIEI-NET/Auto_Diagram_Generator.git
cd Auto_Diagram_Generator

# 依存関係のインストール
uv pip install -e .

# Playwright（オプション）
uv pip install playwright
playwright install chromium
```

### 方法2: 従来のpipを使用

```bash
# リポジトリをクローン
git clone https://github.com/KEIEI-NET/Auto_Diagram_Generator.git
cd Auto_Diagram_Generator

# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# インストール
pip install -r requirements.txt
pip install -e .

# Playwright（オプション）
pip install playwright
playwright install chromium
```

### インストール確認

```bash
# モジュールとして実行
python -m adg.cli.command --help

# テストスクリプトの実行
python test_adg.py

# 各コンポーネントの確認
python -c "from adg.core.analyzer import ProjectAnalyzer; print('✓ Analyzer OK')"
python -c "from adg.generators.mermaid_refactored import MermaidGeneratorRefactored; print('✓ Mermaid OK')"
python -c "from adg.generators.drawio_from_mermaid import DrawIOGenerator; print('✓ DrawIO OK')"
```

## 詳細インストール手順

### Windows環境

#### 1. Python環境の準備

```powershell
# Python公式サイトからインストーラーをダウンロード
# https://www.python.org/downloads/

# または、Chocolateyを使用
choco install python

# または、Windows Storeから
# "Python 3.11"を検索してインストール
```

#### 2. 仮想環境の作成

```powershell
# プロジェクトディレクトリに移動
cd C:\Users\%USERNAME%\Projects

# リポジトリをクローン
git clone https://github.com/KEIEI-NET/Auto_Diagram_Generator.git
cd Auto_Diagram_Generator

# 仮想環境を作成
python -m venv venv

# 仮想環境を有効化
.\venv\Scripts\Activate.ps1

# 実行ポリシーエラーが出る場合
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# pipをアップグレード
python -m pip install --upgrade pip
```

#### 3. 依存関係のインストール

```powershell
# 基本パッケージのインストール
pip install -r requirements.txt

# 開発用パッケージのインストール（開発者向け）
pip install -e ".[dev]"
```

#### 4. Playwrightのインストール（オプション）

```powershell
# Playwrightパッケージのインストール
pip install playwright

# ブラウザのインストール
playwright install chromium

# すべてのブラウザをインストールする場合
playwright install

# 依存関係付きでインストール（必要に応じて）
playwright install --with-deps
```

#### 5. 環境変数の設定

```powershell
# 開発モードの有効化
$env:ADG_DEV_MODE = "true"
$env:ADG_LOG_LEVEL = "DEBUG"
$env:PYTHONPATH = "$env:PYTHONPATH;$(pwd)\src"

# 永続的に設定する場合
[System.Environment]::SetEnvironmentVariable("ADG_DEV_MODE", "true", "User")
```

### macOS環境

#### 1. Homebrewのインストール（未インストールの場合）

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. Python環境の準備

```bash
# Homebrewを使用してPythonをインストール
brew install python@3.11

# pyenvを使用する場合
brew install pyenv
pyenv install 3.11.0
pyenv global 3.11.0
```

#### 3. プロジェクトのセットアップ

```bash
# 作業ディレクトリに移動
cd ~/Projects

# リポジトリをクローン
git clone https://github.com/KEIEI-NET/Auto_Diagram_Generator.git
cd Auto_Diagram_Generator

# 仮想環境を作成
python3 -m venv venv

# 仮想環境を有効化
source venv/bin/activate

# pipをアップグレード
pip install --upgrade pip
```

#### 4. 依存関係のインストール

```bash
# 基本パッケージのインストール
pip install -r requirements.txt

# 開発用パッケージのインストール
pip install -e ".[dev]"
```

#### 5. 追加ツールのインストール（オプション）

```bash
# uvのインストール（高速パッケージマネージャー）
curl -LsSf https://astral.sh/uv/install.sh | sh

# Playwrightのインストール
pip install playwright
playwright install chromium

# Node.js（Playwright用）
brew install node
```

### Linux (Ubuntu/Debian)環境

#### 1. システムパッケージの更新

```bash
sudo apt update
sudo apt upgrade -y
```

#### 2. Python環境の準備

```bash
# Python 3.9以上をインストール
sudo apt install python3.11 python3.11-venv python3-pip

# または、deadsnakes PPAを使用
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11
```

#### 3. プロジェクトのセットアップ

```bash
# 作業ディレクトリに移動
cd ~/projects

# リポジトリをクローン
git clone https://github.com/KEIEI-NET/Auto_Diagram_Generator.git
cd Auto_Diagram_Generator

# 仮想環境を作成
python3.11 -m venv venv

# 仮想環境を有効化
source venv/bin/activate

# pipをアップグレード
pip install --upgrade pip
```

#### 4. 依存関係のインストール

```bash
# 開発ツールのインストール（必要に応じて）
sudo apt install build-essential

# 基本パッケージのインストール
pip install -r requirements.txt

# 開発用パッケージのインストール
pip install -e ".[dev]"
```

#### 5. 追加ツールのインストール（オプション）

```bash
# uvのインストール（高速パッケージマネージャー）
curl -LsSf https://astral.sh/uv/install.sh | sh

# Playwrightのインストール
pip install playwright
playwright install chromium --with-deps

# Node.js（Playwright用）
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs
```

## 開発環境セットアップ

### 1. 開発用依存関係のインストール

```bash
# 開発用パッケージをインストール
pip install -e ".[dev]"

# 個別にインストールする場合
pip install pytest pytest-cov black flake8 mypy pre-commit
```

### 2. pre-commitフックの設定

```bash
# pre-commitをインストール
pip install pre-commit

# フックを設定
pre-commit install

# 手動実行（すべてのファイルに対して）
pre-commit run --all-files
```

### 3. VSCode設定（推奨）

`.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

### 4. PyCharm設定（代替）

1. File → Settings → Project → Project Interpreter
2. 仮想環境を選択: `venv/bin/python`
3. Tools → Python Integrated Tools
   - Default test runner: pytest
   - Docstring format: Google

## Docker環境

### Dockerfileの作成

```dockerfile
FROM python:3.11-slim

# 作業ディレクトリ設定
WORKDIR /app

# システムパッケージのインストール
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# uvのインストール
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# 依存関係のコピーとインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwrightのインストール
RUN pip install playwright && \
    playwright install chromium --with-deps

# アプリケーションのコピー
COPY . .

# インストール
RUN pip install -e .

# エントリーポイント
CMD ["python", "-m", "adg.cli.command"]
```

### Docker Composeの設定

`docker-compose.yml`:

```yaml
version: '3.8'

services:
  adg:
    build: .
    volumes:
      - .:/app
      - ./output:/output
    working_dir: /app
    environment:
      - PYTHONUNBUFFERED=1
    command: analyze /app --output /output
```

### Dockerの使用

```bash
# イメージのビルド
docker build -t adg:latest .

# コンテナの実行
docker run -v $(pwd):/workspace adg:latest analyze /workspace

# Docker Composeを使用
docker-compose run adg analyze
```

## トラブルシューティング

### 一般的な問題と解決策

#### 1. Windows PowerShell実行ポリシーエラー

```powershell
# エラー: "cannot be loaded because running scripts is disabled on this system"

# 解決方法
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# 再度仮想環境をアクティベート
.\venv\Scripts\Activate.ps1
```

#### 2. ImportError: No module named 'adg'

```bash
# Pythonパスを確認
python -c "import sys; print(sys.path)"

# PYTHONPATH環境変数を設定
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

#### 3. Permission denied エラー

```bash
# Linux/macOSの場合
chmod +x $(which adg)

# Windowsの場合（管理者権限で実行）
# PowerShellを管理者として実行してインストール
```

#### 4. 依存関係の競合

```bash
# 仮想環境をクリーンアップ
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate  # Linux/macOS
# または
.\venv\Scripts\activate  # Windows

# 依存関係を再インストール
pip install -r requirements.txt
```

#### 5. Playwrightエラー

```bash
# "Playwright Host validation failed"エラーの場合

# ブラウザを再インストール
playwright uninstall
playwright install chromium --with-deps

# 権限エラーの場合（Linux）
sudo playwright install-deps
```

#### 6. 文字エンコーディングエラー（Windows）

```powershell
# "UnicodeDecodeError: 'cp932' codec can't decode"エラーの場合

# 環境変数を設定
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

### ログの確認

```bash
# ログファイルの場所
cat adg.log

# デバッグモードで実行
adg --debug analyze .

# 環境変数でログレベル設定
export ADG_LOG_LEVEL=DEBUG
adg analyze .
```

## アンインストール

### pipでインストールした場合

```bash
# アンインストール
pip uninstall auto-diagram-generator

# 依存関係も含めて削除
pip freeze | grep -v "^-e" | xargs pip uninstall -y
```

### ソースからインストールした場合

```bash
# 仮想環境を無効化
deactivate

# ディレクトリを削除
cd ..
rm -rf Auto_Diagram_Generator

# 仮想環境を削除
rm -rf venv
```

### 設定ファイルの削除

```bash
# Linux/macOS
rm -rf ~/.config/adg
rm -rf ~/.cache/adg

# Windows
rmdir /s %APPDATA%\adg
rmdir /s %LOCALAPPDATA%\adg
```

## サポート

### 問題報告

問題が発生した場合は、以下の情報を含めて報告してください：

1. OSとバージョン
2. Pythonバージョン (`python --version`)
3. ADGバージョン (`adg --version`)
4. エラーメッセージの全文
5. 実行したコマンド
6. ログファイル（可能であれば）

### コミュニティサポート

- GitHub Issues: https://github.com/KEIEI-NET/Auto_Diagram_Generator/issues
- Discord: [コミュニティサーバー]（将来設置予定）
- Stack Overflow: タグ `auto-diagram-generator`

---

*最終更新: 2025年08月16日 14:45 JST*
*バージョン: v2.1.0*

**更新履歴:**
- v2.1.0 (2025年08月16日): uv対応、Playwright検証、DrawIO生成機能を追加
- v2.0.0 (2025年08月14日): 本番実装完了、セキュリティ強化
- v1.0.0 (2025年01月16日): 初版作成、包括的なインストール手順を文書化