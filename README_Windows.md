# Auto Diagram Generator - Windows PowerShell 使用ガイド

## 概要
このガイドはWindows PowerShellを使用してAuto Diagram Generatorをセットアップ・実行する方法を説明します。

## 前提条件

### 必須ソフトウェア
- Windows 10/11
- PowerShell 5.0以上
- Python 3.9以上
- Git for Windows

### 確認コマンド（PowerShell）
```powershell
# PowerShellバージョン確認
$PSVersionTable.PSVersion

# Python確認
python --version

# Git確認
git --version
```

## セットアップ手順

### 1. リポジトリのクローン
```powershell
# プロジェクトディレクトリに移動
cd $HOME\Documents

# リポジトリをクローン
git clone https://github.com/KEIEI-NET/Auto_Diagram_Generator.git

# プロジェクトディレクトリに移動
cd Auto_Diagram_Generator
```

### 2. Python仮想環境のセットアップ
```powershell
# 仮想環境を作成
python -m venv venv

# 仮想環境をアクティベート
.\venv\Scripts\Activate.ps1

# もしスクリプト実行ポリシーエラーが出る場合
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. 依存関係のインストール
```powershell
# pipをアップグレード
python -m pip install --upgrade pip

# 必要なパッケージをインストール
pip install -r requirements.txt

# Playwrightのインストール（オプション）
pip install playwright
playwright install chromium
```

### 4. 環境変数の設定
```powershell
# 開発モード環境変数を設定（現在のセッションのみ）
$env:ADG_DEV_MODE = "true"

# 永続的に設定する場合
[System.Environment]::SetEnvironmentVariable("ADG_DEV_MODE", "true", "User")
```

## 使用方法

### 基本的な実行
```powershell
# プロジェクト解析とダイアグラム生成
python -m adg analyze . --output output

# 特定のディレクトリを解析
python -m adg analyze src --output diagrams

# Mermaid図のみ生成
python -m adg analyze src --format mermaid
```

### DrawIO図の生成（Mermaid図を基に）
```powershell
# DrawIO形式で生成
python -m adg analyze src --format drawio

# すべての形式で生成
python -m adg analyze src --format all
```

### Playwrightによる検証（オプション）
```powershell
# Mermaid図の検証とスクリーンショット生成
python -m adg validate output --screenshot

# 自動修正付き検証
python -m adg validate output --auto-fix
```

### プロジェクト構造の確認
```powershell
# ツリー表示（PowerShellの場合）
tree /F

# またはカスタムスクリプト
Get-ChildItem -Recurse | Where-Object { -not $_.PSIsContainer } | Select-Object FullName
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. 仮想環境のアクティベートができない
```powershell
# 実行ポリシーを変更
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# 再度アクティベート
.\venv\Scripts\Activate.ps1
```

#### 2. pipインストールエラー
```powershell
# プロキシ環境の場合
$env:HTTP_PROXY = "http://proxy.example.com:8080"
$env:HTTPS_PROXY = "http://proxy.example.com:8080"

# キャッシュをクリア
pip cache purge

# 再インストール
pip install --no-cache-dir -r requirements.txt
```

#### 3. Playwrightエラー
```powershell
# ブラウザを再インストール
playwright uninstall
playwright install chromium

# または全ブラウザをインストール
playwright install
```

#### 4. 文字コードエラー
```powershell
# UTF-8エンコーディングを設定
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
```

## 開発者向けコマンド

### テストの実行
```powershell
# 単体テスト
python -m pytest tests/

# カバレッジ付きテスト
python -m pytest tests/ --cov=adg --cov-report=html

# 特定のテストのみ
python -m pytest tests/test_analyzer.py -v
```

### リンターとフォーマッター
```powershell
# コード品質チェック
python -m flake8 src/

# 自動フォーマット
python -m black src/

# 型チェック
python -m mypy src/
```

### ドキュメント生成
```powershell
# Sphinx ドキュメント生成
cd docs
.\make.bat html

# ドキュメントを開く
Start-Process docs\_build\html\index.html
```

## Gitコマンド（PowerShell）

### 基本的なGit操作
```powershell
# ステータス確認
git status

# 変更をステージング
git add -A

# コミット
git commit -m "feat: Add DrawIO generation from Mermaid structure"

# プッシュ
git push origin main

# ブランチ作成と切り替え
git checkout -b feature/new-diagram-type

# プルリクエスト作成（GitHub CLIが必要）
gh pr create --title "Add new diagram type" --body "Description of changes"
```

### GitHub CLIのインストール
```powershell
# Chocolateyを使用
choco install gh

# またはScoopを使用
scoop install gh

# または直接ダウンロード
Invoke-WebRequest -Uri https://github.com/cli/cli/releases/latest/download/gh_*_windows_amd64.msi -OutFile gh.msi
Start-Process msiexec.exe -Wait -ArgumentList '/i gh.msi /quiet'
```

## PowerShell便利スクリプト

### プロジェクト解析スクリプト
```powershell
# analyze.ps1
param(
    [string]$Path = ".",
    [string]$Output = "output",
    [string]$Format = "all"
)

# 仮想環境をアクティベート
& .\venv\Scripts\Activate.ps1

# 解析実行
python -m adg analyze $Path --output $Output --format $Format

# 結果を開く
if (Test-Path "$Output\index.html") {
    Start-Process "$Output\index.html"
}
```

### バッチ処理スクリプト
```powershell
# batch_analyze.ps1
$projects = @(
    "C:\Projects\Project1",
    "C:\Projects\Project2",
    "C:\Projects\Project3"
)

foreach ($project in $projects) {
    Write-Host "Analyzing: $project" -ForegroundColor Green
    python -m adg analyze $project --output "output\$(Split-Path $project -Leaf)"
}
```

### ウォッチモード（ファイル変更監視）
```powershell
# watch.ps1
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = "src"
$watcher.Filter = "*.py"
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

$action = {
    $path = $Event.SourceEventArgs.FullPath
    $changeType = $Event.SourceEventArgs.ChangeType
    Write-Host "[$changeType] $path" -ForegroundColor Yellow
    python -m adg analyze src --output output
}

Register-ObjectEvent -InputObject $watcher -EventName "Changed" -Action $action
Register-ObjectEvent -InputObject $watcher -EventName "Created" -Action $action
Register-ObjectEvent -InputObject $watcher -EventName "Deleted" -Action $action

Write-Host "Watching for changes... Press Ctrl+C to stop" -ForegroundColor Green
while ($true) { Start-Sleep -Seconds 1 }
```

## 環境固有の設定

### プロキシ設定
```powershell
# システムプロキシを使用
[System.Net.WebRequest]::DefaultWebProxy = [System.Net.WebRequest]::GetSystemWebProxy()
[System.Net.WebRequest]::DefaultWebProxy.Credentials = [System.Net.CredentialCache]::DefaultCredentials

# 環境変数で設定
$env:HTTP_PROXY = "http://proxy.example.com:8080"
$env:HTTPS_PROXY = "http://proxy.example.com:8080"
$env:NO_PROXY = "localhost,127.0.0.1"
```

### パス設定
```powershell
# PYTHONPATHを設定
$env:PYTHONPATH = "$PWD\src"

# システムPATHに追加
$env:Path += ";$PWD\scripts"
```

## 推奨エディタ設定

### Visual Studio Code
```powershell
# VS Codeで開く
code .

# 推奨拡張機能をインストール
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-vscode.powershell
```

### 設定ファイル（.vscode/settings.json）
```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}\\venv\\Scripts\\python.exe",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "terminal.integrated.defaultProfile.windows": "PowerShell",
    "files.encoding": "utf8",
    "files.eol": "\n"
}
```

## セキュリティノート

### PowerShell実行ポリシー
```powershell
# 現在のポリシーを確認
Get-ExecutionPolicy -List

# 推奨設定（ユーザースコープ）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# より制限的な設定（必要に応じて）
Set-ExecutionPolicy -ExecutionPolicy AllSigned -Scope CurrentUser
```

### 仮想環境の重要性
- 常に仮想環境を使用してください
- グローバルPython環境を汚染しないようにしてください
- requirements.txtを最新に保ってください

## サポート

問題が発生した場合は、以下を確認してください：

1. [GitHub Issues](https://github.com/KEIEI-NET/Auto_Diagram_Generator/issues)
2. [プロジェクトWiki](https://github.com/KEIEI-NET/Auto_Diagram_Generator/wiki)
3. エラーログ: `logs/adg_error.log`

## ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照してください。