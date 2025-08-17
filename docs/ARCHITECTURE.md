# Auto Diagram Generator (ADG) アーキテクチャドキュメント

*バージョン: v2.1.0*
*最終更新: 2025年08月16日 14:50 JST*

## 目次

1. [システム概要](#システム概要)
2. [アーキテクチャ原則](#アーキテクチャ原則)
3. [システム構成](#システム構成)
4. [コンポーネント詳細](#コンポーネント詳細)
5. [データフロー](#データフロー)
6. [技術スタック](#技術スタック)
7. [実装アーキテクチャ](#実装アーキテクチャ)
8. [セキュリティ設計](#セキュリティ設計)
9. [パフォーマンス最適化](#パフォーマンス最適化)

## システム概要

Auto Diagram Generator (ADG) は、ソースコードを解析して各種技術ドキュメント図を自動生成するPythonベースのツールです。2025年8月現在、本番実装が完了し、以下の機能を提供しています：

- **AST（抽象構文木）ベースのコード解析**
- **Mermaid/DrawIO形式での図生成**
- **Playwrightによるブラウザベース検証**
- **自動エラー修正機能**
- **セキュアなファイル処理**

### アーキテクチャスタイル

- **レイヤードアーキテクチャ**: 明確な責任分離と依存関係管理
- **ビジターパターン**: AST解析での効率的なノード処理
- **ビルダーパターン**: 図生成での柔軟な構築プロセス
- **パイプライン＆フィルター**: データ処理の流れ

## アーキテクチャ原則

### 1. 単一責任の原則 (SRP)
各コンポーネントは単一の責任を持ち、明確に定義された役割を果たします。

### 2. 開放/閉鎖の原則 (OCP)
新しい図形式の追加は、既存コードの変更なしに拡張として実装できます。

### 3. 依存性逆転の原則 (DIP)
高レベルモジュールは低レベルモジュールに依存せず、両方が抽象に依存します。

### 4. セキュリティ・バイ・デザイン
パストラバーサル対策、入力検証、セキュアなファイル処理を標準実装。

## システム構成

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Interface Layer                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Command  │  │   Args   │  │  Config  │  │  Logger  │  │
│  │ Handler  │  │  Parser  │  │  Loader  │  │  Setup   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Core Analysis Layer                     │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────┐    │
│  │  Integrated   │  │     AST       │  │   Diagram    │    │
│  │   Analyzer    │  │  Analyzers    │  │   Detector   │    │
│  └───────────────┘  └───────────────┘  └──────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Language Parsers: Python, JS, Java, Tree-sitter    │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Generation Layer                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  Mermaid   │  │   DrawIO   │  │  PlantUML  │           │
│  │ Generator  │  │ Generator  │  │ (Future)   │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Validation Layer                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │ Playwright │  │  Mermaid   │  │   Auto     │           │
│  │ Validator  │  │   Viewer   │  │   Fixer    │           │
│  └────────────┘  └────────────┘  └────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Utility Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Security │  │  Cache   │  │  Version │  │  Export  │  │
│  │  Utils   │  │ Manager  │  │  Control │  │  Manager │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## コンポーネント詳細

### 1. CLI Interface Layer

#### Command Handler (`src/adg/cli/command.py`)
- **責任**: コマンドライン引数の処理とコマンドルーティング
- **実装**: Click framework使用
- **主要機能**:
  - `analyze`: プロジェクト解析と図生成
  - `validate`: Mermaid図の検証
  - `convert`: フォーマット間の変換

### 2. Core Analysis Layer

#### Project Analyzer (`src/adg/core/analyzer.py`)
- **責任**: プロジェクト全体の解析と構造抽出
- **実装詳細**:
  ```python
  class ProjectAnalyzer:
      def __init__(self, project_path: str):
          self.project_path = Path(project_path)
          self.file_cache = {}
          
      def analyze(self) -> Dict[str, Any]:
          # AST解析を実行
          # クラス、関数、依存関係を抽出
          # 結果を構造化データとして返す
  ```

#### AST Visitor (`src/adg/core/ast_visitor.py`)
- **責任**: Pythonコードの抽象構文木を効率的に走査
- **パターン**: ビジターパターン実装
- **抽出情報**:
  - クラス定義（継承、属性、メソッド）
  - 関数定義（引数、戻り値、デコレータ）
  - インポート関係
  - 型アノテーション

#### Diagram Detector (`src/adg/core/detector.py`)
- **責任**: コード内容から適切な図の種類を自動判定
- **判定ロジック**:
  - クラスが多い → クラス図
  - データベース関連 → ER図
  - 関数呼び出しチェーン → シーケンス図
  - 条件分岐が多い → フロー図

### 3. Generation Layer

#### Mermaid Generator (`src/adg/generators/mermaid_refactored.py`)
- **責任**: Mermaid形式の図生成
- **設計パターン**: ビルダーパターン
- **実装クラス**:
  ```python
  class MermaidGeneratorRefactored:
      def __init__(self, analysis_result: Dict[str, Any]):
          self.builders = {
              'class': ClassDiagramBuilder,
              'sequence': SequenceDiagramBuilder,
              'flow': FlowDiagramBuilder,
              'er': ERDiagramBuilder
          }
  ```

#### DrawIO Generator (`src/adg/generators/drawio_from_mermaid.py`)
- **責任**: Mermaid構造からDrawIO XML形式への変換
- **主要機能**:
  - Mermaid図の解析
  - レイアウト計算
  - DrawIO XML生成
  - スタイル適用

### 4. Validation Layer

#### Playwright Validator (`src/adg/utils/mermaid_playwright_validator.py`)
- **責任**: ブラウザでの実際のレンダリング検証
- **機能**:
  - リアルタイムレンダリング
  - エラー検出
  - スクリーンショット生成
  - 自動修正提案

#### Auto Fixer
- **責任**: 検出されたエラーの自動修正
- **修正パターン**:
  - 構文エラー
  - 未定義参加者
  - 不正な矢印記法
  - 重複定義

### 5. Utility Layer

#### Security Utils (`src/adg/utils/security.py`)
- **責任**: セキュアなファイル操作
- **実装機能**:
  ```python
  def secure_path_join(base_path: Path, *paths: str) -> Path:
      # パストラバーサル対策
      # 安全なパス結合
      
  def validate_input(data: str, pattern: str) -> bool:
      # 入力検証
      # SQLインジェクション対策
  ```

## データフロー

### 1. 解析フロー
```
入力ファイル → AST解析 → 構造抽出 → データモデル生成
```

### 2. 生成フロー
```
データモデル → 図種判定 → Mermaid生成 → DrawIO変換 → 出力
```

### 3. 検証フロー
```
Mermaid図 → Playwright検証 → エラー検出 → 自動修正 → 再検証
```

## 技術スタック

### コア技術
- **言語**: Python 3.9+
- **AST処理**: Python ast モジュール
- **CLI**: Click 8.0+
- **ロギング**: Loguru

### 図生成
- **Mermaid**: テキストベース図生成
- **DrawIO**: XML形式図生成
- **Playwright**: ブラウザ自動化（検証用）

### 開発ツール
- **パッケージ管理**: uv (推奨) / pip
- **テスト**: pytest
- **型チェック**: mypy
- **フォーマッター**: black, isort

## 実装アーキテクチャ

### ディレクトリ構造
```
src/adg/
├── cli/              # CLIインターフェース
│   ├── __init__.py
│   └── command.py    # コマンドハンドラー
├── core/             # コア機能
│   ├── __init__.py
│   ├── analyzer.py   # プロジェクト解析
│   ├── ast_visitor.py # AST走査
│   ├── detector.py   # 図種判定
│   └── results.py    # 結果管理
├── generators/       # 図生成器
│   ├── __init__.py
│   ├── mermaid_refactored.py    # Mermaid生成
│   ├── drawio_from_mermaid.py   # DrawIO変換
│   └── mermaid_auto_fix.py      # 自動修正
└── utils/           # ユーティリティ
    ├── __init__.py
    ├── security.py   # セキュリティ
    ├── validation.py # 検証
    └── mermaid_playwright_validator.py # Playwright検証
```

### クラス設計

#### 基底クラス
```python
class DiagramGenerator(ABC):
    """図生成器の基底クラス"""
    @abstractmethod
    def generate(self, data: Dict[str, Any]) -> DiagramResult:
        pass

class DiagramBuilder(ABC):
    """図ビルダーの基底クラス"""
    @abstractmethod
    def build(self) -> MermaidDiagram:
        pass
```

#### データクラス
```python
@dataclass
class DiagramResult:
    """図生成結果"""
    success: bool
    diagram_type: str
    format: str
    content: Optional[str]
    file_path: Optional[str]
    error: Optional[str]

@dataclass
class MermaidDiagram:
    """Mermaid図データ"""
    type: str
    title: str
    content: List[str]
    metadata: Dict[str, Any]
```

## セキュリティ設計

### 1. パストラバーサル対策
```python
def secure_path_join(base_path: Path, *paths: str) -> Path:
    """安全なパス結合"""
    base = base_path.resolve()
    full_path = base.joinpath(*paths).resolve()
    
    if not full_path.is_relative_to(base):
        raise SecurityError("Path traversal detected")
    
    return full_path
```

### 2. 入力検証
- ファイルパスの正規化
- 拡張子のホワイトリスト
- サイズ制限
- 文字エンコーディング検証

### 3. 実行時セキュリティ
- サンドボックス環境での実行
- リソース制限
- タイムアウト設定

## パフォーマンス最適化

### 1. キャッシング戦略
- AST解析結果のキャッシュ
- 生成済み図のキャッシュ
- インクリメンタル更新

### 2. 並列処理
```python
from concurrent.futures import ThreadPoolExecutor

def analyze_files_parallel(files: List[Path]) -> List[Dict]:
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(analyze_file, files)
    return list(results)
```

### 3. メモリ最適化
- ストリーミング処理
- 遅延評価
- 不要なオブジェクトの早期解放

## 拡張ポイント

### 新しい図形式の追加
1. `DiagramBuilder`を継承
2. ビルダークラスを実装
3. ジェネレーターに登録

### 新しい言語サポート
1. パーサーを実装
2. ASTビジターを拡張
3. 言語固有の検出ロジック追加

### カスタムバリデーター
1. `Validator`インターフェースを実装
2. 検証ロジックを定義
3. バリデーションパイプラインに統合

## デプロイメントアーキテクチャ

### Docker構成
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install playwright && playwright install chromium --with-deps
COPY . .
CMD ["python", "-m", "adg.cli.command"]
```

### CI/CDパイプライン
1. **ビルド**: 依存関係インストール
2. **テスト**: ユニットテスト、統合テスト
3. **検証**: 型チェック、リンター
4. **デプロイ**: Dockerイメージ作成

## 監視とロギング

### ロギング戦略
```python
from loguru import logger

logger.add("adg.log", rotation="10 MB", retention="7 days")
logger.add(sys.stderr, level="ERROR")
```

### メトリクス
- 処理時間
- メモリ使用量
- エラー率
- 図生成成功率

## トラブルシューティング

### デバッグモード
```bash
export ADG_LOG_LEVEL=DEBUG
python -m adg.cli.command analyze --debug
```

### パフォーマンスプロファイリング
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# 処理実行
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats()
```

---

*最終更新: 2025年08月16日 14:50 JST*
*バージョン: v2.1.0*

**更新履歴:**
- v2.1.0 (2025年08月16日): 本番実装のアーキテクチャを反映、DrawIO生成とPlaywright検証を追加
- v2.0.0 (2025年08月14日): セキュリティ設計とパフォーマンス最適化を追加
- v1.0.0 (2025年01月16日): 初版作成