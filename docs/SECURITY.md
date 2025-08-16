# 🔒 セキュリティガイド

## 概要

Auto Diagram Generator (ADG)は、セキュリティを最優先事項として開発されています。このドキュメントでは、実装されているセキュリティ対策と、安全な使用方法について説明します。

## 実装済みセキュリティ対策

### 1. パストラバーサル攻撃対策

ADGは、すべてのファイルパス操作において厳格な検証を実施します。

```python
from adg.utils.security import validate_path

# 安全なパス検証
safe_path = validate_path(user_input_path, base_dir="/allowed/directory")
```

**実装内容：**
- `..` を含むパスの拒否
- シンボリックリンクの解決と検証
- NULLバイトインジェクションの防止
- ベースディレクトリ外へのアクセス制限

### 2. 入力検証とサニタイゼーション

すべてのユーザー入力は検証とサニタイゼーションが行われます。

```python
from adg.utils.security import sanitize_filename

# ファイル名のサニタイゼーション
safe_filename = sanitize_filename(user_filename)
```

**実装内容：**
- 危険な文字の除去（`<>|&;$` など）
- Windowsの予約語チェック（CON, PRN, AUX など）
- ファイル名長の制限（255文字）

### 3. セキュアなモジュールインポート

動的なモジュールインポートを制限し、安全性を確保します。

```python
from adg.utils.security import is_safe_import

if is_safe_import(module_name):
    # 安全なモジュールのみインポート
    module = importlib.import_module(module_name)
```

**ブラックリスト：**
- `os`, `sys`, `subprocess`
- `eval`, `exec`, `compile`
- `__import__`, `open`, `input`

### 4. ファイルサイズ制限

DoS攻撃を防ぐため、処理するファイルのサイズを制限します。

```python
from adg.utils.security import validate_file_size

if validate_file_size(file_path, max_size_mb=100):
    # ファイルを処理
```

### 5. 環境変数による開発モード制御

開発用の機能は環境変数で明示的に有効化する必要があります。

```bash
# 開発モードを有効化（本番環境では使用しない）
export ADG_DEV_MODE=1
```

## セキュリティベストプラクティス

### インストール時の注意

1. **仮想環境の使用を推奨**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -e .
   ```

2. **依存関係の定期的な更新**
   ```bash
   pip list --outdated
   pip install --upgrade [package_name]
   ```

3. **信頼できるソースからのみインストール**
   - 公式GitHubリポジトリからクローン
   - PyPIからの公式パッケージ（リリース後）

### 実行時の注意

1. **最小権限の原則**
   - 必要最小限の権限で実行
   - rootユーザーでの実行を避ける

2. **入力ファイルの検証**
   - 信頼できないソースからのファイルは注意
   - 大きなファイルや異常なファイル構造に注意

3. **出力ディレクトリの管理**
   - 出力先は専用ディレクトリを使用
   - 重要なシステムディレクトリへの書き込みを避ける

## 既知の脆弱性と対策

### 修正済み（v0.1.0）

| 脆弱性 | 深刻度 | 状態 | 修正バージョン |
|--------|--------|------|---------------|
| パストラバーサル攻撃 | Critical | ✅ 修正済み | 0.1.0 |
| sys.path操作の脆弱性 | Critical | ✅ 修正済み | 0.1.0 |
| 入力検証の不備 | Medium | ✅ 修正済み | 0.1.0 |

### 監視中

現在、新たな脆弱性は報告されていません。

## セキュリティ設定

### config/diagram-generator.yaml

```yaml
security:
  # ファイルサイズ制限（MB）
  max_file_size: 100
  
  # 処理可能な拡張子
  allowed_extensions:
    - .py
    - .js
    - .java
    - .ts
  
  # 除外ディレクトリ
  excluded_paths:
    - /etc
    - /sys
    - /proc
    - C:\Windows
    - C:\Program Files
  
  # タイムアウト設定（秒）
  analysis_timeout: 300
  generation_timeout: 600
```

## セキュリティ監査

### 自動チェック

開発時に以下のツールで定期的にチェック：

```bash
# セキュリティ脆弱性スキャン
pip install safety
safety check

# 静的解析
pip install bandit
bandit -r src/

# 依存関係の脆弱性チェック
pip audit
```

### 手動レビュー

- コードレビューでセキュリティの観点を含める
- 新機能追加時のセキュリティインパクト評価
- 定期的なセキュリティ監査

## インシデント対応

### セキュリティ問題の報告

セキュリティ上の問題を発見した場合：

1. **公開しない**: GitHubのIssueには記載しない
2. **プライベート報告**: メンテナーに直接連絡
3. **詳細情報**: 再現手順と影響範囲を含める

### 対応プロセス

1. **確認**: 24時間以内に受領確認
2. **評価**: 72時間以内に深刻度評価
3. **修正**: 深刻度に応じて修正を実施
4. **公開**: 修正後にセキュリティアドバイザリを公開

## セキュリティチェックリスト

### 開発者向け

- [ ] 新しいファイルパス操作には`validate_path()`を使用
- [ ] ユーザー入力は必ず検証・サニタイゼーション
- [ ] 外部コマンド実行を避ける
- [ ] エラーメッセージに機密情報を含めない
- [ ] ログに個人情報やパスワードを記録しない

### 利用者向け

- [ ] 最新バージョンを使用
- [ ] 仮想環境で実行
- [ ] 信頼できないファイルを処理しない
- [ ] 出力先ディレクトリを適切に設定
- [ ] 定期的に依存関係を更新

## 関連リソース

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.org/dev/security/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)

## 更新履歴

| 日付 | バージョン | 変更内容 |
|------|----------|----------|
| 2024-01-16 | 0.1.0 | 初版作成、基本的なセキュリティ対策実装 |

---

最終更新: 2024年1月16日