# Auto Diagram Generator (ADG) API仕様書

*バージョン: v1.0.0*
*最終更新: 2025年01月16日 16:30 JST*

## 目次

1. [概要](#概要)
2. [コアAPI](#コアapi)
3. [CLI API](#cli-api)
4. [ジェネレーターAPI](#ジェネレーターapi)
5. [データモデル](#データモデル)
6. [エラーハンドリング](#エラーハンドリング)
7. [拡張ポイント](#拡張ポイント)

## 概要

Auto Diagram Generator (ADG) は、ソースコードを解析して各種ダイアグラムを自動生成するツールです。本書では、ADGの内部APIおよび拡張用インターフェースについて詳細に説明します。

### APIバージョニング

- **現在のバージョン**: 1.0.0
- **APIレベル**: Alpha
- **Python要件**: 3.9以上

## コアAPI

### CodeAnalyzer基底クラス

```python
class CodeAnalyzer:
    """
    コード解析の基底クラス
    
    Args:
        file_path (str): 解析対象ファイルのパス
    
    Attributes:
        file_path (Path): ファイルパスのPathオブジェクト
        content (str): ファイルの内容
        elements (List[CodeElement]): 抽出されたコード要素のリスト
    """
    
    def __init__(self, file_path: str):
        """
        アナライザーの初期化
        
        Raises:
            FileNotFoundError: ファイルが存在しない場合
            ValueError: パスがファイルでない場合
            UnicodeDecodeError: ファイルのエンコーディングエラー
            PermissionError: ファイルの読み取り権限がない場合
        """
    
    def analyze(self) -> Dict[str, Any]:
        """
        コードを解析して構造を抽出
        
        Returns:
            Dict[str, Any]: 解析結果の辞書
                - classes: ClassInfoオブジェクトのリスト
                - functions: FunctionInfoオブジェクトのリスト
                - imports: ImportInfoオブジェクトのリスト
                - variables: 変数情報のリスト
                - error: エラーメッセージ（エラー時のみ）
        
        Note:
            サブクラスで必ず実装する必要があります
        """
```

### PythonAnalyzer

```python
class PythonAnalyzer(CodeAnalyzer):
    """
    Python専用のコード解析器
    
    ASTを使用してPythonコードの構造を詳細に解析します。
    """
    
    def analyze(self) -> Dict[str, Any]:
        """
        Pythonコードを解析
        
        Returns:
            Dict[str, Any]: 解析結果
                - classes: クラス情報のリスト
                - functions: 関数情報のリスト
                - imports: インポート情報のリスト
                - variables: グローバル変数のリスト
        
        Example:
            >>> analyzer = PythonAnalyzer("example.py")
            >>> result = analyzer.analyze()
            >>> print(f"Classes found: {len(result['classes'])}")
        """
```

### ProjectAnalyzer

```python
class ProjectAnalyzer:
    """
    プロジェクト全体の解析を管理
    
    Args:
        project_path (str): プロジェクトのルートパス
    
    Attributes:
        project_path (Path): プロジェクトパス
        analyzers (Dict[str, Type[CodeAnalyzer]]): 拡張子別アナライザーマッピング
    """
    
    def analyze(self) -> Dict[str, Any]:
        """
        プロジェクト全体を解析
        
        Returns:
            Dict[str, Any]: プロジェクト解析結果
                - project_path: プロジェクトのパス
                - files: ファイル別の解析結果
                - summary: 統計情報
                    - total_files: 総ファイル数
                    - total_classes: 総クラス数
                    - total_functions: 総関数数
        
        Note:
            以下のディレクトリは自動的に除外されます:
            - __pycache__, .git, .venv, venv
            - node_modules, .pytest_cache, .mypy_cache
            - dist, build
            
            1MB以上のファイルも自動的にスキップされます。
        """
```

### DiagramDetector

```python
class DiagramDetector:
    """
    解析結果から必要な図を自動判定
    """
    
    def detect(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        推奨される図を検出
        
        Args:
            analysis_result: ProjectAnalyzerの解析結果
        
        Returns:
            List[Dict[str, Any]]: 推奨される図のリスト
                各要素は以下の形式:
                - type: 図の種類（'class', 'er', 'sequence'等）
                - reason: 推奨理由
                - priority: 優先度（1-10）
                - confidence: 信頼度（0.0-1.0）
        
        判定基準:
            - クラスが3個以上: クラス図を推奨
            - データベース関連のインポート: ER図を推奨
            - 非同期関数の存在: シーケンス図を推奨
            - API関連のデコレーター: API仕様図を推奨
        """
```

## CLI API

### コマンド構造

```bash
adg [OPTIONS] COMMAND [ARGS]...

Commands:
  analyze     プロジェクトを解析して必要な図を判定
  generate    図を生成
  list-types  生成可能な図の種類を表示
```

### analyzeコマンド

```python
@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option('--output', '-o', type=click.Path(), default='output')
@click.option('--format', '-f', type=click.Choice(['mermaid', 'plantuml', 'drawio', 'all']))
@click.option('--verbose', '-v', is_flag=True)
def analyze(path, output, format, verbose):
    """
    プロジェクトを解析して必要な図を判定
    
    Args:
        path: 解析対象のパス（デフォルト: カレントディレクトリ）
        output: 出力ディレクトリ（デフォルト: output）
        format: 出力フォーマット（デフォルト: mermaid）
        verbose: 詳細情報の表示フラグ
    
    Returns:
        Dict[str, Any]: 解析結果
    
    Exit Codes:
        0: 成功
        1: パスが存在しない、または解析エラー
    """
```

### generateコマンド

```python
@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option('--output', '-o', type=click.Path(), default='output')
@click.option('--format', '-f', type=click.Choice(['mermaid', 'plantuml', 'drawio', 'all']))
@click.option('--types', '-t', multiple=True)
@click.option('--auto', '-a', is_flag=True)
def generate(path, output, format, types, auto):
    """
    図を生成
    
    Args:
        path: 解析対象のパス
        output: 出力ディレクトリ
        format: 出力フォーマット
        types: 生成する図の種類（複数指定可）
        auto: 自動判定した図をすべて生成
    
    Note:
        --types または --auto のいずれかを指定する必要があります
    """
```

## ジェネレーターAPI

### MermaidGenerator

```python
class MermaidGenerator:
    """
    Mermaid形式の図生成器
    
    Args:
        analysis_result: ProjectAnalyzerの解析結果
    """
    
    def generate_class_diagram(self, output_path: Path) -> Optional[str]:
        """
        クラス図を生成
        
        Args:
            output_path: 出力ディレクトリのパス
        
        Returns:
            Optional[str]: 生成されたファイルのパス（生成失敗時はNone）
        
        生成される図の形式:
            ```mermaid
            classDiagram
                class ClassName {
                    +attribute1: type
                    +method1() return_type
                }
                BaseClass <|-- DerivedClass
            ```
        """
    
    def generate_er_diagram(self, output_path: Path) -> Optional[str]:
        """ER図を生成（未実装）"""
    
    def generate_sequence_diagram(self, output_path: Path) -> Optional[str]:
        """シーケンス図を生成（未実装）"""
```

## データモデル

### CodeElement

```python
@dataclass
class CodeElement:
    """
    コード要素の基本クラス
    
    Attributes:
        name: 要素の名前
        type: 要素の種類（'class', 'function', 'import'等）
        file_path: ファイルパス
        line_number: 行番号
        metadata: 追加のメタデータ
    """
    name: str
    type: str
    file_path: str
    line_number: int
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### ClassInfo

```python
@dataclass
class ClassInfo(CodeElement):
    """
    クラス情報
    
    Attributes:
        methods: メソッド名のリスト
        attributes: 属性名のリスト
        base_classes: 基底クラス名のリスト
        decorators: デコレーター名のリスト
    """
    methods: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
```

### FunctionInfo

```python
@dataclass
class FunctionInfo(CodeElement):
    """
    関数/メソッド情報
    
    Attributes:
        parameters: パラメータ名のリスト
        return_type: 戻り値の型（Optional）
        decorators: デコレーター名のリスト
        is_async: 非同期関数かどうか
    """
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
```

### ImportInfo

```python
@dataclass
class ImportInfo(CodeElement):
    """
    インポート情報
    
    Attributes:
        module: モジュール名
        imported_names: インポートされた名前のリスト
        is_from_import: from importかどうか
    """
    module: str
    imported_names: List[str] = field(default_factory=list)
    is_from_import: bool = False
```

## エラーハンドリング

### エラーレスポンス形式

```python
{
    "error": "エラーメッセージ",
    "error_type": "FileNotFoundError",
    "file_path": "/path/to/file",
    "line_number": 42,  # 該当する場合
    "suggestion": "修正提案"  # 可能な場合
}
```

### 主要なエラータイプ

| エラータイプ | 説明 | 対処法 |
|------------|------|--------|
| FileNotFoundError | ファイルが存在しない | パスを確認 |
| PermissionError | 読み取り権限がない | 権限を確認 |
| SyntaxError | コードの構文エラー | コードを修正 |
| UnicodeDecodeError | エンコーディングエラー | UTF-8形式に変換 |
| ValueError | 不正な値 | 入力値を確認 |

## 拡張ポイント

### 新しい言語サポートの追加

```python
# 1. CodeAnalyzerを継承
class JavaScriptAnalyzer(CodeAnalyzer):
    def analyze(self) -> Dict[str, Any]:
        # JavaScriptコードの解析ロジック
        pass

# 2. ProjectAnalyzerに登録
analyzer = ProjectAnalyzer(project_path)
analyzer.analyzers['.js'] = JavaScriptAnalyzer
analyzer.analyzers['.jsx'] = JavaScriptAnalyzer
```

### 新しい図形式の追加

```python
# 1. 基底ジェネレータークラスを作成（推奨）
class DiagramGenerator:
    def __init__(self, analysis_result: Dict[str, Any]):
        self.analysis_result = analysis_result
    
    def generate(self, diagram_type: str, output_path: Path) -> Optional[str]:
        raise NotImplementedError

# 2. 具体的な実装
class CustomGenerator(DiagramGenerator):
    def generate_custom_diagram(self, output_path: Path) -> Optional[str]:
        # カスタム図の生成ロジック
        pass
```

### プラグインシステム（将来実装予定）

```python
# プラグインインターフェース
class ADGPlugin:
    def on_analysis_start(self, project_path: str):
        """解析開始時のフック"""
        pass
    
    def on_file_analyzed(self, file_path: str, result: Dict[str, Any]):
        """ファイル解析完了時のフック"""
        pass
    
    def on_diagram_generated(self, diagram_type: str, file_path: str):
        """図生成完了時のフック"""
        pass
```

## 使用例

### 基本的な使用例

```python
from adg.core.analyzer import ProjectAnalyzer
from adg.core.detector import DiagramDetector
from adg.generators.mermaid import MermaidGenerator
from pathlib import Path

# プロジェクト解析
analyzer = ProjectAnalyzer("/path/to/project")
analysis_result = analyzer.analyze()

# 推奨図の検出
detector = DiagramDetector()
recommended = detector.detect(analysis_result)

# 図の生成
generator = MermaidGenerator(analysis_result)
output_path = Path("./output")
for diagram in recommended:
    if diagram['type'] == 'class':
        generator.generate_class_diagram(output_path)
```

### カスタム解析の実装例

```python
class CustomAnalyzer(CodeAnalyzer):
    def analyze(self) -> Dict[str, Any]:
        # カスタム解析ロジック
        result = {
            "custom_elements": [],
            "metrics": {}
        }
        
        # ファイル内容を解析
        for line_num, line in enumerate(self.content.splitlines(), 1):
            if "TODO" in line:
                result["custom_elements"].append({
                    "type": "todo",
                    "line": line_num,
                    "content": line.strip()
                })
        
        return result
```

### エラーハンドリングの例

```python
from adg.core.analyzer import PythonAnalyzer
import logging

logger = logging.getLogger(__name__)

try:
    analyzer = PythonAnalyzer("example.py")
    result = analyzer.analyze()
    
    if "error" in result:
        logger.error(f"Analysis error: {result['error']}")
        # エラー時の処理
    else:
        # 正常時の処理
        print(f"Found {len(result['classes'])} classes")
        
except FileNotFoundError as e:
    logger.error(f"File not found: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

---

*最終更新: 2025年01月16日 16:30 JST*
*バージョン: v1.0.0*

**更新履歴:**
- v1.0.0 (2025年01月16日): 初版作成、包括的なAPI仕様書を追加