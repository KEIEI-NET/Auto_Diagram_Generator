# 推奨コマンド

## 開発コマンド

### コードフォーマット
```bash
black src/ tests/ --line-length 100
```

### リンティング
```bash
flake8 src/ tests/
```

### 型チェック
```bash
mypy src/
```

### テスト実行
```bash
pytest tests/ --cov=src --cov-report=html --cov-report=term
```

### パッケージインストール（開発モード）
```bash
pip install -e .
```

## アプリケーションコマンド

### プロジェクト解析
```bash
adg analyze [PATH] --output output --verbose
```

### 図生成
```bash
adg generate [PATH] --output output --format mermaid --auto
adg generate [PATH] --types class er sequence
```

### 利用可能な図種類表示
```bash
adg list-types
```

## Windows固有のコマンド
```cmd
# ディレクトリ一覧
dir /s

# ファイル検索
where python
where pip

# 環境変数確認
echo %PATH%
```