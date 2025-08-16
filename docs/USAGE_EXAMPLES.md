# Auto Diagram Generator - 使用例

*バージョン: v2.1.0*
*最終更新: 2025年08月16日 14:55 JST*

## 目次

1. [基本的な使い方](#基本的な使い方)
2. [プロジェクト解析](#プロジェクト解析)
3. [図の生成](#図の生成)
4. [DrawIO形式への変換](#drawio形式への変換)
5. [Playwright検証](#playwright検証)
6. [実践的な例](#実践的な例)
7. [高度な使用例](#高度な使用例)
8. [トラブルシューティング例](#トラブルシューティング例)

## 基本的な使い方

### 1. プロジェクトの解析と図生成

```bash
# 現在のディレクトリを解析
python -m adg.cli.command analyze . --output output

# 特定のディレクトリを解析
python -m adg.cli.command analyze src --output diagrams

# デバッグモードで実行
export ADG_LOG_LEVEL=DEBUG
python -m adg.cli.command analyze src --debug
```

### 2. Windows PowerShellでの使用

```powershell
# 仮想環境をアクティベート
.\venv\Scripts\Activate.ps1

# プロジェクト解析
python -m adg.cli.command analyze src --output output

# 環境変数を設定して実行
$env:ADG_DEV_MODE = "true"
$env:ADG_LOG_LEVEL = "DEBUG"
python -m adg.cli.command analyze src
```

## プロジェクト解析

### 基本的な解析

```python
from adg.core.analyzer import ProjectAnalyzer

# プロジェクトの解析
analyzer = ProjectAnalyzer("src")
analysis_result = analyzer.analyze()

# 結果の確認
print(f"Classes found: {len(analysis_result['classes'])}")
print(f"Functions found: {len(analysis_result['functions'])}")
print(f"Files analyzed: {len(analysis_result['files'])}")
```

### 詳細な解析結果の取得

```python
from adg.core.analyzer import ProjectAnalyzer
import json

analyzer = ProjectAnalyzer("src/adg")
result = analyzer.analyze()

# クラス情報の表示
for class_name, class_info in result['classes'].items():
    print(f"\nClass: {class_name}")
    print(f"  File: {class_info['file']}")
    print(f"  Methods: {', '.join(class_info['methods'])}")
    print(f"  Attributes: {', '.join(class_info['attributes'])}")
    if class_info['bases']:
        print(f"  Inherits from: {', '.join(class_info['bases'])}")

# 解析結果をJSONで保存
with open("analysis_result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
```

## 図の生成

### Mermaid図の生成

```python
from adg.generators.mermaid_refactored import MermaidGeneratorRefactored
from adg.core.analyzer import ProjectAnalyzer
from pathlib import Path

# プロジェクト解析
analyzer = ProjectAnalyzer("src")
analysis_result = analyzer.analyze()

# Mermaid図生成器の初期化
generator = MermaidGeneratorRefactored(analysis_result)

# 出力ディレクトリの作成
output_dir = Path("output/mermaid")
output_dir.mkdir(parents=True, exist_ok=True)

# 各種図の生成
# クラス図
class_result = generator.generate('class', output_dir)
if class_result.success:
    print(f"Class diagram generated: {class_result.file_path}")

# シーケンス図
sequence_result = generator.generate('sequence', output_dir)
if sequence_result.success:
    print(f"Sequence diagram generated: {sequence_result.file_path}")

# フロー図
flow_result = generator.generate('flow', output_dir)
if flow_result.success:
    print(f"Flow diagram generated: {flow_result.file_path}")

# ER図
er_result = generator.generate('er', output_dir)
if er_result.success:
    print(f"ER diagram generated: {er_result.file_path}")
```

### すべての図を一括生成

```python
from adg.generators.mermaid_refactored import MermaidGeneratorRefactored
from adg.core.analyzer import ProjectAnalyzer
from pathlib import Path

# 解析と生成
analyzer = ProjectAnalyzer("src")
analysis_result = analyzer.analyze()

generator = MermaidGeneratorRefactored(analysis_result)
output_dir = Path("output/all_diagrams")

# すべての図を生成
results = generator.generate_all(output_dir)

# 結果のサマリー表示
successful = sum(1 for r in results if r.success)
failed = sum(1 for r in results if not r.success)

print(f"\n=== Generation Summary ===")
print(f"Total: {len(results)}")
print(f"Successful: {successful}")
print(f"Failed: {failed}")

for result in results:
    status = "✓" if result.success else "✗"
    print(f"{status} {result.diagram_type}: {result.file_path or result.error}")
```

## DrawIO形式への変換

### Mermaid図からDrawIO図を生成

```python
from adg.generators.drawio_from_mermaid import MermaidBasedDrawIOGenerator
from adg.core.analyzer import ProjectAnalyzer
from pathlib import Path

# プロジェクト解析
analyzer = ProjectAnalyzer("src")
analysis_result = analyzer.analyze()

# DrawIO生成器の初期化
generator = MermaidBasedDrawIOGenerator(analysis_result)

# 出力ディレクトリ
output_dir = Path("output/drawio")
output_dir.mkdir(parents=True, exist_ok=True)

# すべての図をMermaid→DrawIOの順で生成
results = generator.generate_all(output_dir)

# 生成されたファイルの確認
for result in results:
    if result.success and result.format == 'drawio':
        print(f"DrawIO file: {result.file_path}")
```

### 個別のDrawIO変換

```python
from adg.generators.drawio_from_mermaid import DrawIOGenerator, MermaidToDrawIOParser
from adg.generators.mermaid_refactored import ClassDiagramBuilder
from adg.core.analyzer import ProjectAnalyzer
from pathlib import Path

# 解析
analyzer = ProjectAnalyzer("src")
analysis_result = analyzer.analyze()

# Mermaidクラス図を生成
builder = ClassDiagramBuilder(analysis_result)
mermaid_diagram = builder.build()

# DrawIOに変換
drawio_generator = DrawIOGenerator()
output_dir = Path("output/custom_drawio")
output_dir.mkdir(parents=True, exist_ok=True)

result = drawio_generator.generate_from_mermaid(mermaid_diagram, output_dir)

if result.success:
    print(f"DrawIO diagram created: {result.file_path}")
    # DrawIO Desktopで開く（インストール済みの場合）
    import subprocess
    subprocess.run(["open", result.file_path])  # macOS
    # subprocess.run(["start", result.file_path], shell=True)  # Windows
```

## Playwright検証

### Mermaid図の検証と自動修正

```python
from adg.utils.mermaid_playwright_validator import validate_mermaid_with_playwright
from pathlib import Path

# 単一ファイルの検証
mermaid_file = Path("output/mermaid/class_diagram.mmd")
result = validate_mermaid_with_playwright(
    mermaid_file,
    auto_fix=True,  # 自動修正を有効化
    headless=True    # ヘッドレスモードで実行
)

if result.is_valid:
    print(f"✓ Valid Mermaid diagram: {mermaid_file}")
    if result.fix_applied:
        print("  Auto-fix was applied")
    if result.screenshot_path:
        print(f"  Screenshot: {result.screenshot_path}")
else:
    print(f"✗ Invalid diagram: {result.errors}")
```

### ディレクトリ内のすべてのMermaid図を検証

```python
from adg.utils.mermaid_playwright_validator import validate_directory_with_playwright
from pathlib import Path
import json

# ディレクトリ内のすべてのMermaid図を検証
output_dir = Path("output/mermaid")
results = validate_directory_with_playwright(
    output_dir,
    pattern="*.mmd",
    auto_fix=True,
    headless=False  # ブラウザを表示（デバッグ用）
)

# 検証レポートの生成
report = {
    'total': len(results),
    'valid': sum(1 for r in results if r.is_valid),
    'fixed': sum(1 for r in results if r.fix_applied),
    'results': [r.to_dict() for r in results]
}

with open("validation_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print(f"\n=== Validation Summary ===")
print(f"Total files: {report['total']}")
print(f"Valid: {report['valid']}")
print(f"Auto-fixed: {report['fixed']}")
```

### 非同期での検証（高度な使用例）

```python
import asyncio
from adg.utils.mermaid_playwright_validator import MermaidPlaywrightValidator
from pathlib import Path

async def validate_multiple_files():
    async with MermaidPlaywrightValidator(headless=True) as validator:
        files = list(Path("output/mermaid").glob("*.mmd"))
        
        tasks = []
        for file in files:
            task = validator.validate_mermaid_file(file, auto_fix=True)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        for file, result in zip(files, results):
            status = "✓" if result.is_valid else "✗"
            print(f"{status} {file.name}")
        
        return results

# 実行
results = asyncio.run(validate_multiple_files())
```

## 実践的な例

### 1. Djangoプロジェクトの解析と図生成

```python
from adg.core.analyzer import ProjectAnalyzer
from adg.generators.mermaid_refactored import MermaidGeneratorRefactored
from adg.generators.drawio_from_mermaid import MermaidBasedDrawIOGenerator
from pathlib import Path

def analyze_django_project(project_path: str):
    """Djangoプロジェクトの解析と図生成"""
    
    # models.pyファイルを重点的に解析
    analyzer = ProjectAnalyzer(project_path)
    result = analyzer.analyze()
    
    # Django特有のフィルタリング
    django_classes = {
        name: info for name, info in result['classes'].items()
        if 'models.py' in info.get('file', '') or 
           'views.py' in info.get('file', '') or
           'serializers.py' in info.get('file', '')
    }
    
    # フィルタリングされた結果で図生成
    filtered_result = {**result, 'classes': django_classes}
    
    generator = MermaidGeneratorRefactored(filtered_result)
    output_dir = Path("output/django_diagrams")
    
    # ER図とクラス図を生成
    er_result = generator.generate('er', output_dir)
    class_result = generator.generate('class', output_dir)
    
    print(f"Django ER Diagram: {er_result.file_path}")
    print(f"Django Class Diagram: {class_result.file_path}")
    
    return [er_result, class_result]

# 使用例
results = analyze_django_project("path/to/django/project")
```

### 2. FastAPIプロジェクトの解析

```python
from adg.core.analyzer import ProjectAnalyzer
from adg.generators.mermaid_refactored import MermaidGeneratorRefactored
from pathlib import Path

def analyze_fastapi_project(project_path: str):
    """FastAPIプロジェクトの解析"""
    
    analyzer = ProjectAnalyzer(project_path)
    result = analyzer.analyze()
    
    # API エンドポイントの抽出
    api_functions = {}
    for func_name, func_info in result['functions'].items():
        decorators = func_info.get('decorators', [])
        # FastAPIのデコレータを持つ関数を抽出
        if any('@app.' in str(d) or '@router.' in str(d) for d in decorators):
            api_functions[func_name] = func_info
    
    # シーケンス図とフロー図を生成
    filtered_result = {**result, 'functions': api_functions}
    generator = MermaidGeneratorRefactored(filtered_result)
    
    output_dir = Path("output/fastapi_diagrams")
    sequence_result = generator.generate('sequence', output_dir)
    flow_result = generator.generate('flow', output_dir)
    
    return [sequence_result, flow_result]

# 使用例
results = analyze_fastapi_project("path/to/fastapi/project")
```

### 3. CI/CDパイプラインでの使用

```yaml
# .github/workflows/generate-docs.yml
name: Generate Documentation Diagrams

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  generate-diagrams:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install playwright
        playwright install chromium
    
    - name: Generate diagrams
      run: |
        python -m adg.cli.command analyze src --output docs/diagrams
    
    - name: Validate diagrams
      run: |
        python -m adg.utils.mermaid_playwright_validator \
          --directory docs/diagrams \
          --auto-fix
    
    - name: Commit diagrams
      if: github.event_name == 'push'
      run: |
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add docs/diagrams
        git commit -m "Update documentation diagrams" || exit 0
        git push
```

## 高度な使用例

### カスタムフィルターとトランスフォーマー

```python
from adg.core.analyzer import ProjectAnalyzer
from adg.generators.mermaid_refactored import MermaidGeneratorRefactored
from typing import Dict, Any

class CustomAnalyzer:
    """カスタム解析ロジック"""
    
    def __init__(self, project_path: str):
        self.analyzer = ProjectAnalyzer(project_path)
    
    def analyze_with_filters(self, 
                            include_private: bool = False,
                            min_method_count: int = 3) -> Dict[str, Any]:
        """フィルタリング付き解析"""
        result = self.analyzer.analyze()
        
        # プライベートメソッドのフィルタリング
        if not include_private:
            for class_info in result['classes'].values():
                class_info['methods'] = [
                    m for m in class_info.get('methods', [])
                    if not m.startswith('_')
                ]
        
        # メソッド数によるクラスのフィルタリング
        filtered_classes = {
            name: info for name, info in result['classes'].items()
            if len(info.get('methods', [])) >= min_method_count
        }
        
        result['classes'] = filtered_classes
        return result
    
    def generate_custom_diagram(self, output_path: str):
        """カスタマイズされた図の生成"""
        analysis = self.analyze_with_filters(
            include_private=False,
            min_method_count=3
        )
        
        generator = MermaidGeneratorRefactored(analysis)
        result = generator.generate('class', Path(output_path))
        
        return result

# 使用例
custom_analyzer = CustomAnalyzer("src")
result = custom_analyzer.generate_custom_diagram("output/custom")
```

### バッチ処理スクリプト

```python
#!/usr/bin/env python
"""
複数のプロジェクトを一括処理するスクリプト
"""

from pathlib import Path
from adg.core.analyzer import ProjectAnalyzer
from adg.generators.drawio_from_mermaid import MermaidBasedDrawIOGenerator
import json
from datetime import datetime
import pytz

def batch_process_projects(project_dirs: list, output_base: str):
    """複数プロジェクトの一括処理"""
    
    tokyo_tz = pytz.timezone('Asia/Tokyo')
    timestamp = datetime.now(tokyo_tz).strftime("%Y%m%d_%H%M%S")
    results = []
    
    for project_dir in project_dirs:
        project_path = Path(project_dir)
        if not project_path.exists():
            print(f"Skipping {project_dir}: not found")
            continue
        
        print(f"\nProcessing: {project_path.name}")
        
        try:
            # 解析
            analyzer = ProjectAnalyzer(str(project_path))
            analysis_result = analyzer.analyze()
            
            # 出力ディレクトリ
            output_dir = Path(output_base) / project_path.name / timestamp
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 図生成
            generator = MermaidBasedDrawIOGenerator(analysis_result)
            diagram_results = generator.generate_all(output_dir)
            
            # 結果を記録
            project_result = {
                'project': project_path.name,
                'timestamp': timestamp,
                'success': True,
                'diagrams': [
                    {
                        'type': r.diagram_type,
                        'format': r.format,
                        'path': r.file_path
                    }
                    for r in diagram_results if r.success
                ],
                'errors': [r.error for r in diagram_results if not r.success]
            }
            
        except Exception as e:
            project_result = {
                'project': project_path.name,
                'timestamp': timestamp,
                'success': False,
                'error': str(e)
            }
        
        results.append(project_result)
    
    # サマリーレポート生成
    report_file = Path(output_base) / f"batch_report_{timestamp}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': timestamp,
            'total_projects': len(results),
            'successful': sum(1 for r in results if r['success']),
            'failed': sum(1 for r in results if not r['success']),
            'results': results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nBatch processing complete. Report: {report_file}")
    return results

# 使用例
projects = [
    "/path/to/project1",
    "/path/to/project2",
    "/path/to/project3"
]

results = batch_process_projects(projects, "output/batch")
```

## トラブルシューティング例

### エラーハンドリング

```python
from adg.core.analyzer import ProjectAnalyzer
from adg.generators.mermaid_refactored import MermaidGeneratorRefactored
from pathlib import Path
import traceback

def safe_generate_diagrams(project_path: str):
    """エラーハンドリング付き図生成"""
    
    try:
        # 解析フェーズ
        print(f"Analyzing {project_path}...")
        analyzer = ProjectAnalyzer(project_path)
        analysis_result = analyzer.analyze()
        
        if not analysis_result.get('classes') and not analysis_result.get('functions'):
            print("Warning: No classes or functions found in the project")
            return []
        
        # 生成フェーズ
        print("Generating diagrams...")
        generator = MermaidGeneratorRefactored(analysis_result)
        output_dir = Path("output/safe")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results = []
        diagram_types = ['class', 'sequence', 'flow', 'er']
        
        for diagram_type in diagram_types:
            try:
                result = generator.generate(diagram_type, output_dir)
                results.append(result)
                
                if result.success:
                    print(f"✓ {diagram_type} diagram generated")
                else:
                    print(f"✗ {diagram_type} diagram failed: {result.error}")
                    
            except Exception as e:
                print(f"Error generating {diagram_type} diagram: {e}")
                traceback.print_exc()
        
        return results
        
    except FileNotFoundError as e:
        print(f"Error: Project path not found: {e}")
    except PermissionError as e:
        print(f"Error: Permission denied: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()
    
    return []

# 使用例
results = safe_generate_diagrams("src")
```

### デバッグ情報の取得

```python
import logging
from loguru import logger
from adg.core.analyzer import ProjectAnalyzer
from pathlib import Path

# デバッグログの設定
logger.add("debug.log", level="DEBUG", rotation="10 MB")

def debug_analysis(project_path: str):
    """デバッグ情報付き解析"""
    
    logger.info(f"Starting analysis of {project_path}")
    
    analyzer = ProjectAnalyzer(project_path)
    
    # ファイル一覧の取得
    py_files = list(Path(project_path).rglob("*.py"))
    logger.debug(f"Found {len(py_files)} Python files")
    
    # 解析実行
    result = analyzer.analyze()
    
    # 統計情報
    logger.info(f"Classes found: {len(result.get('classes', {}))}")
    logger.info(f"Functions found: {len(result.get('functions', {}))}")
    logger.info(f"Files analyzed: {len(result.get('files', {}))}")
    
    # 詳細情報
    for class_name in result.get('classes', {}).keys():
        logger.debug(f"Class: {class_name}")
    
    return result

# 使用例
result = debug_analysis("src")
```

### パフォーマンス計測

```python
import time
from adg.core.analyzer import ProjectAnalyzer
from adg.generators.mermaid_refactored import MermaidGeneratorRefactored
from pathlib import Path

def benchmark_generation(project_path: str):
    """パフォーマンス計測付き図生成"""
    
    times = {}
    
    # 解析時間の計測
    start = time.time()
    analyzer = ProjectAnalyzer(project_path)
    analysis_result = analyzer.analyze()
    times['analysis'] = time.time() - start
    
    # 生成器の初期化
    generator = MermaidGeneratorRefactored(analysis_result)
    output_dir = Path("output/benchmark")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 各図の生成時間を計測
    diagram_types = ['class', 'sequence', 'flow', 'er']
    
    for diagram_type in diagram_types:
        start = time.time()
        result = generator.generate(diagram_type, output_dir)
        times[f'{diagram_type}_generation'] = time.time() - start
    
    # 結果表示
    print("\n=== Performance Benchmark ===")
    for operation, duration in times.items():
        print(f"{operation}: {duration:.3f} seconds")
    
    print(f"\nTotal time: {sum(times.values()):.3f} seconds")
    
    return times

# 使用例
times = benchmark_generation("src")
```

---

*最終更新: 2025年08月16日 14:55 JST*
*バージョン: v2.1.0*

**更新履歴:**
- v2.1.0 (2025年08月16日): DrawIO生成、Playwright検証、実践例を追加
- v2.0.0 (2025年08月14日): 本番実装に基づく使用例を追加
- v1.0.0 (2025年01月16日): 初版作成