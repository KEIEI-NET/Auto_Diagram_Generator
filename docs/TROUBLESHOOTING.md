# Auto Diagram Generator (ADG) トラブルシューティングガイド

*バージョン: v1.0.0*
*最終更新: 2025年01月16日 16:50 JST*

## 目次

1. [一般的な問題](#一般的な問題)
2. [インストール関連](#インストール関連)
3. [実行時エラー](#実行時エラー)
4. [解析エラー](#解析エラー)
5. [図生成エラー](#図生成エラー)
6. [パフォーマンス問題](#パフォーマンス問題)
7. [環境固有の問題](#環境固有の問題)
8. [デバッグ方法](#デバッグ方法)

## 一般的な問題

### Q1: "adg: command not found" エラー

**症状:**
```bash
$ adg analyze
bash: adg: command not found
```

**原因:**
- ADGが正しくインストールされていない
- PATHに追加されていない
- 仮想環境が有効化されていない

**解決策:**

```bash
# 1. インストール状態を確認
pip list | grep auto-diagram-generator

# 2. 再インストール
pip uninstall auto-diagram-generator
pip install -e .

# 3. PATHを確認
echo $PATH
which adg

# 4. 仮想環境を確認
which python
# 仮想環境を有効化
source venv/bin/activate  # Linux/macOS
.\venv\Scripts\activate   # Windows

# 5. 直接実行
python -m adg.cli.command analyze
```

### Q2: ImportError: No module named 'adg'

**症状:**
```python
Traceback (most recent call last):
  File "...", line X, in <module>
    from adg.core.analyzer import ProjectAnalyzer
ImportError: No module named 'adg'
```

**解決策:**

```bash
# 1. Pythonパスを確認
python -c "import sys; print('\n'.join(sys.path))"

# 2. PYTHONPATH環境変数を設定
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"  # Linux/macOS
set PYTHONPATH=%PYTHONPATH%;%cd%\src          # Windows

# 3. 開発モードでインストール
pip install -e .

# 4. srcディレクトリの確認
ls -la src/adg/  # ディレクトリ構造を確認
```

### Q3: Permission denied エラー

**症状:**
```bash
Permission denied: '/usr/local/bin/adg'
```

**解決策:**

```bash
# Linux/macOS
# 1. 実行権限を付与
chmod +x $(which adg)

# 2. sudoで実行（非推奨）
sudo adg analyze

# 3. ユーザーディレクトリにインストール
pip install --user auto-diagram-generator

# Windows
# 1. 管理者権限でPowerShellを実行
# 2. 実行ポリシーを確認
Get-ExecutionPolicy
# 3. 必要に応じて変更
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## インストール関連

### Q4: 依存関係の競合

**症状:**
```bash
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
```

**解決策:**

```bash
# 1. 仮想環境を作り直す
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate

# 2. 依存関係を個別にインストール
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt --no-deps
pip install -r requirements.txt

# 3. 競合を解決
pip install --force-reinstall package_name==version

# 4. pipenvやpoetryを使用
pipenv install
# または
poetry install
```

### Q5: C拡張のコンパイルエラー

**症状:**
```bash
error: Microsoft Visual C++ 14.0 or greater is required
```

**解決策:**

```bash
# Windows
# 1. Visual Studio Build Toolsをインストール
# https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022

# 2. プリコンパイル済みホイールを使用
pip install --only-binary :all: package_name

# Linux
# 1. 開発ツールをインストール
sudo apt-get install build-essential python3-dev  # Ubuntu/Debian
sudo yum install gcc python3-devel                 # RHEL/CentOS

# macOS
# 1. Xcodeコマンドラインツールをインストール
xcode-select --install
```

## 実行時エラー

### Q6: FileNotFoundError

**症状:**
```python
FileNotFoundError: [Errno 2] No such file or directory: 'path/to/file'
```

**解決策:**

```python
# 1. パスの存在を確認
from pathlib import Path

file_path = Path("path/to/file")
if not file_path.exists():
    print(f"File not found: {file_path}")
    print(f"Current directory: {Path.cwd()}")

# 2. 相対パスを絶対パスに変換
absolute_path = file_path.resolve()
print(f"Absolute path: {absolute_path}")

# 3. 作業ディレクトリを確認
import os
print(f"Working directory: {os.getcwd()}")
```

### Q7: UnicodeDecodeError

**症状:**
```python
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0
```

**解決策:**

```python
# 1. エンコーディングを指定
with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# 2. エンコーディングを自動検出
import chardet

with open(file_path, 'rb') as f:
    raw_data = f.read()
    result = chardet.detect(raw_data)
    encoding = result['encoding']

with open(file_path, 'r', encoding=encoding) as f:
    content = f.read()

# 3. バイナリファイルを除外
if file_path.suffix in ['.pyc', '.pyo', '.so', '.dll']:
    print(f"Skipping binary file: {file_path}")
```

## 解析エラー

### Q8: SyntaxError in Python code

**症状:**
```python
SyntaxError: invalid syntax
```

**解決策:**

```bash
# 1. Pythonバージョンを確認
python --version

# 2. 構文エラーをチェック
python -m py_compile problematic_file.py

# 3. AST解析をスキップ
adg analyze --skip-syntax-errors

# 4. 特定のファイルを除外
adg analyze --exclude "problematic_file.py"
```

### Q9: メモリ不足エラー

**症状:**
```bash
MemoryError: Unable to allocate array
```

**解決策:**

```bash
# 1. メモリ使用量を制限
adg analyze --max-memory 2G

# 2. ファイルサイズを制限
adg analyze --max-file-size 1M

# 3. 並列処理を無効化
adg analyze --no-parallel

# 4. ストリーミング処理を使用
adg analyze --streaming

# 5. システムメモリを確認
free -h  # Linux
vm_stat  # macOS
wmic OS get TotalVisibleMemorySize,FreePhysicalMemory  # Windows
```

## 図生成エラー

### Q10: Graphvizが見つからない

**症状:**
```bash
GraphvizExecutableNotFound: failed to execute ['dot', '-V']
```

**解決策:**

```bash
# 1. Graphvizをインストール
# Ubuntu/Debian
sudo apt-get install graphviz

# macOS
brew install graphviz

# Windows (Chocolatey)
choco install graphviz

# 2. PATHに追加
# Linux/macOS
export PATH="/usr/local/bin:$PATH"

# Windows
setx PATH "%PATH%;C:\Program Files\Graphviz\bin"

# 3. インストールを確認
dot -V

# 4. Pythonバインディングをインストール
pip install graphviz
```

### Q11: Mermaid CLIエラー

**症状:**
```bash
Error: Cannot find module '@mermaid-js/mermaid-cli'
```

**解決策:**

```bash
# 1. Node.jsをインストール
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install nodejs

# macOS
brew install node

# 2. Mermaid CLIをインストール
npm install -g @mermaid-js/mermaid-cli

# 3. パスを確認
which mmdc

# 4. 代替: Pythonベースのレンダラーを使用
pip install mermaid-py
```

## パフォーマンス問題

### Q12: 解析が遅い

**症状:**
- 大規模プロジェクトの解析に時間がかかる
- CPUやメモリ使用率が高い

**解決策:**

```bash
# 1. キャッシュを有効化
adg analyze --cache-enabled

# 2. 並列処理を調整
adg analyze --parallel $(nproc)

# 3. インクリメンタル解析
adg analyze --incremental

# 4. 不要なファイルを除外
adg analyze \
  --exclude "**/node_modules/**" \
  --exclude "**/.git/**" \
  --exclude "**/venv/**"

# 5. プロファイリング
adg analyze --profile --output profile.html

# 6. 解析対象を限定
adg analyze --languages python --max-depth 3
```

### Q13: 図生成でメモリリーク

**症状:**
- メモリ使用量が徐々に増加
- 長時間実行後にクラッシュ

**解決策:**

```python
# 1. メモリプロファイリング
import tracemalloc

tracemalloc.start()
# ... 処理 ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)

# 2. ガベージコレクションを強制
import gc
gc.collect()

# 3. 大きなオブジェクトを明示的に削除
del large_object
gc.collect()

# 4. ジェネレーターを使用
def process_files():
    for file_path in file_paths:
        yield analyze_file(file_path)  # メモリ効率的
```

## 環境固有の問題

### Q14: Windows環境でのパス問題

**症状:**
```python
OSError: [Errno 22] Invalid argument: 'C:\Users\...'
```

**解決策:**

```python
# 1. raw文字列を使用
path = r"C:\Users\username\project"

# 2. スラッシュを使用
path = "C:/Users/username/project"

# 3. Pathオブジェクトを使用（推奨）
from pathlib import Path
path = Path("C:/Users/username/project")

# 4. 環境変数を使用
import os
path = Path.home() / "project"
```

### Q15: Docker環境での問題

**症状:**
- コンテナ内でファイルが見つからない
- 権限エラー

**解決策:**

```dockerfile
# Dockerfile
FROM python:3.11-slim

# ユーザーを作成
RUN useradd -m -u 1000 adguser

# 作業ディレクトリ
WORKDIR /app

# 所有権を設定
COPY --chown=adguser:adguser . .

# ユーザーを切り替え
USER adguser

# インストール
RUN pip install --user -e .
```

```bash
# 実行時
docker run -v $(pwd):/app:ro \
  -u $(id -u):$(id -g) \
  adg:latest analyze /app
```

## デバッグ方法

### 詳細ログの有効化

```bash
# 1. 環境変数でログレベル設定
export ADG_LOG_LEVEL=DEBUG
adg analyze .

# 2. コマンドラインオプション
adg analyze . --log-level DEBUG

# 3. 設定ファイル
# adg-config.yaml
logging:
  level: DEBUG
  file: adg-debug.log
```

### デバッガーの使用

```python
# 1. pdbを使用
import pdb

def problematic_function():
    pdb.set_trace()  # ここでブレークポイント
    # 問題のあるコード

# 2. ipdbを使用（より高機能）
pip install ipdb
import ipdb

ipdb.set_trace()

# 3. VSCodeでデバッグ
# launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug ADG",
            "type": "python",
            "request": "launch",
            "module": "adg.cli.command",
            "args": ["analyze", "."],
            "console": "integratedTerminal"
        }
    ]
}
```

### エラーレポートの作成

```bash
# エラー情報を収集
adg diagnose > error_report.txt

# 含まれる情報：
# - システム情報
# - Pythonバージョン
# - インストール済みパッケージ
# - 環境変数
# - 最近のログ
# - トレースバック
```

## よくある警告と対処法

### 警告: "File is empty"

```bash
# 空ファイルをスキップ
adg analyze --skip-empty-files
```

### 警告: "Skipping large file"

```bash
# ファイルサイズ制限を変更
adg analyze --max-file-size 5M
```

### 警告: "Cache is outdated"

```bash
# キャッシュをクリア
adg cache clear

# キャッシュを再構築
adg cache rebuild
```

## サポートの受け方

### 問題報告時に必要な情報

1. **エラーメッセージ全文**
```bash
adg analyze 2>&1 | tee error.log
```

2. **環境情報**
```bash
adg --version
python --version
pip list
uname -a  # Linux/macOS
systeminfo  # Windows
```

3. **再現手順**
- 実行したコマンド
- 使用したファイル（可能であれば）
- 期待した結果と実際の結果

4. **デバッグログ**
```bash
ADG_LOG_LEVEL=DEBUG adg analyze . 2>&1 > debug.log
```

---

*最終更新: 2025年01月16日 16:50 JST*
*バージョン: v1.0.0*

**更新履歴:**
- v1.0.0 (2025年01月16日): 初版作成、包括的なトラブルシューティング情報を文書化