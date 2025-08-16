# Auto Diagram Generator (ADG) 使用例とベストプラクティス

*バージョン: v1.0.0*
*最終更新: 2025年01月16日 16:45 JST*

## 目次

1. [基本的な使用例](#基本的な使用例)
2. [高度な使用例](#高度な使用例)
3. [実践的なシナリオ](#実践的なシナリオ)
4. [ベストプラクティス](#ベストプラクティス)
5. [パフォーマンス最適化](#パフォーマンス最適化)
6. [CI/CD統合](#cicd統合)

## 基本的な使用例

### 1. プロジェクトの解析

#### カレントディレクトリの解析

```bash
# 現在のディレクトリを解析
adg analyze

# 出力例：
# 🔍 プロジェクトを解析中: .
# 
# ╭────────────────────────╮
# │   解析結果サマリー      │
# ├────────────┬───────────┤
# │ 項目       │ 数        │
# ├────────────┼───────────┤
# │ ファイル数  │ 23        │
# │ クラス数   │ 15        │
# │ 関数数     │ 47        │
# ╰────────────┴───────────╯
# 
# ✨ 推奨される図:
#   • class: クラス構造が検出されました
#   • sequence: API呼び出しパターンが検出されました
```

#### 特定ディレクトリの解析

```bash
# 特定のディレクトリを解析
adg analyze /path/to/project

# 詳細モードで解析
adg analyze /path/to/project --verbose

# 出力ディレクトリを指定
adg analyze /path/to/project --output ./analysis_output
```

### 2. 図の自動生成

#### 自動判定による生成

```bash
# 推奨される図をすべて生成
adg generate --auto

# 特定のフォーマットで生成
adg generate --auto --format mermaid

# 出力ディレクトリを指定
adg generate --auto --output ./diagrams
```

#### 図種別を指定して生成

```bash
# クラス図のみ生成
adg generate --types class

# 複数の図を生成
adg generate --types class er sequence

# すべてのフォーマットで生成
adg generate --types class --format all
```

### 3. 利用可能な図種別の確認

```bash
# 生成可能な図の一覧を表示
adg list-types

# 出力例：
# ╭─────────────────────────────────────────╮
# │      生成可能な図の種類                  │
# ├──────────┬──────────────┬──────────────┤
# │ タイプ   │ 名称         │ 説明         │
# ├──────────┼──────────────┼──────────────┤
# │ class    │ クラス図     │ クラスの構造... │
# │ er       │ ER図        │ データベース... │
# │ sequence │ シーケンス図  │ 処理の流れ... │
# ╰──────────┴──────────────┴──────────────╯
```

## 高度な使用例

### 1. 設定ファイルの使用

#### カスタム設定ファイルの作成

`adg-config.yaml`:

```yaml
# プロジェクト設定
project:
  name: "My Project"
  version: "1.0.0"
  
# 解析設定
analysis:
  exclude_patterns:
    - "test_*.py"
    - "*_test.py"
    - "migrations/*"
  max_file_size: 2097152  # 2MB
  
# 図生成設定
generation:
  default_format: "mermaid"
  output_directory: "./docs/diagrams"
  timestamp_format: "JST"
  
# 図種別ごとの設定
diagrams:
  class:
    include_private: false
    show_methods: true
    show_attributes: true
  er:
    show_indexes: true
    show_constraints: true
```

#### 設定ファイルを指定して実行

```bash
# カスタム設定で解析
adg analyze --config adg-config.yaml

# 環境変数で設定ファイルを指定
export ADG_CONFIG_FILE=adg-config.yaml
adg generate --auto
```

### 2. フィルタリングとカスタマイズ

#### ファイルパターンによるフィルタリング

```bash
# 特定のパターンのファイルのみ解析
adg analyze --include "src/**/*.py" --exclude "test_*.py"

# 複数のパターンを指定
adg analyze \
  --include "app/**/*.py" \
  --include "lib/**/*.py" \
  --exclude "**/test_*.py" \
  --exclude "**/migrations/*.py"
```

#### 出力のカスタマイズ

```bash
# JSON形式で解析結果を出力
adg analyze --output-format json > analysis.json

# 特定の情報のみ抽出
adg analyze --only classes,functions

# サマリーのみ表示
adg analyze --summary-only
```

### 3. バッチ処理

#### 複数プロジェクトの一括処理

```bash
#!/bin/bash
# batch_analyze.sh

projects=(
  "/path/to/project1"
  "/path/to/project2"
  "/path/to/project3"
)

for project in "${projects[@]}"; do
  echo "Analyzing $project..."
  adg analyze "$project" --output "./results/$(basename $project)"
  adg generate "$project" --auto --output "./diagrams/$(basename $project)"
done
```

#### 並列処理による高速化

```bash
#!/bin/bash
# parallel_generate.sh

# GNU parallelを使用
find . -type d -name "src" | parallel -j 4 adg analyze {} --output {}/diagrams

# xargsを使用
find . -type d -maxdepth 2 | xargs -P 4 -I {} adg generate {} --auto
```

## 実践的なシナリオ

### シナリオ1: マイクロサービスアーキテクチャの可視化

```bash
# 1. 全サービスの構造を解析
for service in services/*; do
  adg analyze "$service" --output "docs/analysis/$(basename $service)"
done

# 2. サービス間の依存関係を検出
adg analyze services/ --detect-dependencies --output docs/dependencies.json

# 3. アーキテクチャ図を生成
adg generate services/ \
  --types component deployment \
  --format mermaid \
  --output docs/architecture

# 4. 各サービスの詳細図を生成
for service in services/*; do
  adg generate "$service" \
    --types class sequence \
    --output "docs/diagrams/$(basename $service)"
done
```

### シナリオ2: レガシーコードの理解

```bash
# 1. プロジェクト全体の概要を取得
adg analyze legacy-project/ --verbose > analysis_report.txt

# 2. 複雑度の高い部分を特定
adg analyze legacy-project/ \
  --complexity-threshold high \
  --output complex_areas.json

# 3. 主要なコンポーネントの図を生成
adg generate legacy-project/ \
  --types class er flow \
  --format all \
  --output documentation/

# 4. リファクタリング候補を特定
adg analyze legacy-project/ \
  --detect-code-smells \
  --output refactoring_suggestions.md
```

### シナリオ3: API ドキュメント生成

```bash
# 1. API エンドポイントを解析
adg analyze api/ --detect-endpoints --output api_analysis.json

# 2. API 仕様図を生成
adg generate api/ \
  --types sequence flow \
  --api-mode \
  --output api_docs/

# 3. データモデルの図を生成
adg generate api/models/ \
  --types er class \
  --output api_docs/data_models/

# 4. OpenAPI仕様と統合（将来機能）
adg export api/ --format openapi --output openapi.yaml
```

## ベストプラクティス

### 1. プロジェクト構造の整理

```
project/
├── .adg/                 # ADG設定とキャッシュ
│   ├── config.yaml      # プロジェクト固有の設定
│   └── cache/           # 解析キャッシュ
├── docs/
│   └── diagrams/        # 生成された図
├── src/                 # ソースコード
└── tests/               # テストコード
```

### 2. 継続的なドキュメント更新

#### Git フックの設定

`.git/hooks/pre-commit`:

```bash
#!/bin/bash
# 変更されたファイルを解析
changed_files=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

if [ -n "$changed_files" ]; then
  echo "Updating diagrams..."
  adg generate --auto --output docs/diagrams/
  git add docs/diagrams/
fi
```

#### GitHub Actions ワークフロー

`.github/workflows/update-diagrams.yml`:

```yaml
name: Update Diagrams

on:
  push:
    branches: [main, develop]
    paths:
      - '**.py'
      - '**.js'
      - '**.java'

jobs:
  generate-diagrams:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install ADG
      run: |
        pip install auto-diagram-generator
    
    - name: Generate diagrams
      run: |
        adg analyze . --output analysis/
        adg generate . --auto --output docs/diagrams/
    
    - name: Commit changes
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add docs/diagrams/
        git diff --staged --quiet || git commit -m "Update diagrams [skip ci]"
        git push
```

### 3. 大規模プロジェクトの処理

#### インクリメンタル解析

```bash
# 初回: フル解析とキャッシュ作成
adg analyze large-project/ --cache-enabled --output initial_analysis/

# 以降: 変更部分のみ解析
adg analyze large-project/ --incremental --output updated_analysis/

# キャッシュをクリア
adg cache clear
```

#### メモリ効率的な処理

```bash
# ストリーミングモードで大規模ファイルを処理
adg analyze huge-project/ --streaming --max-memory 2G

# ファイルを分割して処理
adg analyze huge-project/ --chunk-size 100 --parallel 4
```

## パフォーマンス最適化

### 1. キャッシングの活用

```bash
# キャッシュを有効化
adg analyze . --cache-enabled

# キャッシュの統計を表示
adg cache stats

# キャッシュサイズ：1.2 GB
# ヒット率：87%
# 最終更新：2025-01-16 15:30 JST
```

### 2. 並列処理の設定

```bash
# CPUコア数に応じて並列度を調整
adg analyze . --parallel $(nproc)

# 明示的に並列度を指定
adg analyze . --parallel 8

# 並列処理を無効化（デバッグ用）
adg analyze . --no-parallel
```

### 3. 選択的な処理

```bash
# 特定の言語のみ処理
adg analyze . --languages python,javascript

# 特定のサイズ以下のファイルのみ処理
adg analyze . --max-file-size 100KB

# 最近変更されたファイルのみ処理
adg analyze . --modified-since "2025-01-01"
```

## CI/CD統合

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Analyze Code') {
            steps {
                sh 'adg analyze . --output reports/analysis/'
            }
        }
        
        stage('Generate Diagrams') {
            steps {
                sh 'adg generate . --auto --output docs/diagrams/'
            }
        }
        
        stage('Archive Artifacts') {
            steps {
                archiveArtifacts artifacts: 'docs/diagrams/**/*', 
                                 allowEmptyArchive: false
            }
        }
    }
    
    post {
        always {
            publishHTML([
                reportDir: 'docs/diagrams',
                reportFiles: 'index.html',
                reportName: 'Architecture Diagrams'
            ])
        }
    }
}
```

### GitLab CI

`.gitlab-ci.yml`:

```yaml
stages:
  - analyze
  - generate
  - deploy

analyze:
  stage: analyze
  image: python:3.11
  script:
    - pip install auto-diagram-generator
    - adg analyze . --output analysis/
  artifacts:
    paths:
      - analysis/
    expire_in: 1 week

generate-diagrams:
  stage: generate
  image: python:3.11
  dependencies:
    - analyze
  script:
    - pip install auto-diagram-generator
    - adg generate . --auto --output diagrams/
  artifacts:
    paths:
      - diagrams/
    expire_in: 1 month

deploy-docs:
  stage: deploy
  dependencies:
    - generate-diagrams
  script:
    - cp -r diagrams/ public/
  artifacts:
    paths:
      - public/
  only:
    - main
```

## トラブルシューティング例

### メモリ不足エラーの対処

```bash
# メモリ使用量を制限
adg analyze . --max-memory 1G

# ファイルを分割処理
find . -name "*.py" | split -l 100 - batch_
for batch in batch_*; do
  adg analyze --file-list "$batch" --output "results/$batch/"
done
```

### 解析速度の改善

```bash
# プロファイリングを有効化
adg analyze . --profile --output profile_report.html

# ボトルネックを特定して最適化
adg analyze . --skip-heavy-operations --fast-mode
```

---

*最終更新: 2025年01月16日 16:45 JST*
*バージョン: v1.0.0*

**更新履歴:**
- v1.0.0 (2025年01月16日): 初版作成、包括的な使用例とベストプラクティスを文書化