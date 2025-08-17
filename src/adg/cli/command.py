"""
CLI コマンドインターフェース
"""

import click
import sys
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import track
from loguru import logger

# セキュアなインポート方法
try:
    from adg.core.analyzer import ProjectAnalyzer
    from adg.core.detector import DiagramDetector
    from adg.generators.mermaid import MermaidGenerator
    from adg.generators.drawio_from_mermaid import DrawIOFromMermaid
    from adg.utils.security import validate_path
except ImportError:
    # 開発環境用のフォールバック（環境変数で制御）
    if os.getenv('ADG_DEV_MODE') == '1':
        parent_dir = Path(__file__).parent.parent.parent
        if parent_dir.exists() and (parent_dir / 'adg').exists():
            sys.path.insert(0, str(parent_dir))
            from adg.core.analyzer import ProjectAnalyzer
            from adg.core.detector import DiagramDetector
            from adg.generators.mermaid import MermaidGenerator
            from adg.generators.drawio_from_mermaid import DrawIOFromMermaid
            from adg.utils.security import validate_path
        else:
            raise ImportError("ADG modules not found in development mode")
    else:
        raise ImportError("ADG modules not found. Please install the package properly.")

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="adg")
def cli():
    """Auto Diagram Generator - コードから図を自動生成"""
    pass


@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option('--output', '-o', type=click.Path(), default='output', help='出力ディレクトリ')
@click.option('--format', '-f', type=click.Choice(['mermaid', 'plantuml', 'drawio', 'all']), 
              default='mermaid', help='出力フォーマット')
@click.option('--verbose', '-v', is_flag=True, help='詳細情報を表示')
def analyze(path, output, format, verbose):
    """プロジェクトを解析して必要な図を判定"""
    
    try:
        # パスの検証（セキュリティチェック含む）
        path_obj = Path(path).resolve()  # 絶対パスに変換
        
        # セキュリティ検証（validate_pathがあれば使用）
        try:
            validated_path = validate_path(str(path_obj))
            path_obj = Path(validated_path)
        except Exception as validation_error:
            console.print(f"[red]エラー: パスの検証に失敗しました: {validation_error}[/red]")
            sys.exit(1)
        
        if not path_obj.exists():
            console.print(f"[red]Error: Path '{path}' does not exist[/red]")
            sys.exit(1)
        
        console.print(f"[bold blue]Analyzing project: {path}[/bold blue]")
        
        # プロジェクト解析
        analyzer = ProjectAnalyzer(path)
        with console.status("[bold green]Analyzing code..."):
            analysis_result = analyzer.analyze()
        
        if not analysis_result or not analysis_result.get('files'):
            console.print("[yellow]Warning: No files found to analyze[/yellow]")
            return analysis_result
    except Exception as e:
        console.print(f"[red]Error: Analysis failed: {e}[/red]")
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)
    
    # 結果サマリーを表示
    summary = analysis_result["summary"]
    table = Table(title="Analysis Summary")
    table.add_column("Item", style="cyan")
    table.add_column("Count", style="magenta")
    
    table.add_row("Files", str(summary["total_files"]))
    table.add_row("Classes", str(summary["total_classes"]))
    table.add_row("Functions", str(summary["total_functions"]))
    
    console.print(table)
    
    if verbose:
        console.print("\n[bold yellow]Analyzed files:[/bold yellow]")
        for file_path in analysis_result["files"]:
            console.print(f"  - {file_path}")
    
    # 図の判定
    detector = DiagramDetector()
    recommended_diagrams = detector.detect(analysis_result)
    
    console.print(f"\n[bold green]Recommended diagrams:[/bold green]")
    for diagram in recommended_diagrams:
        console.print(f"  - {diagram['type']}: {diagram['reason']}")
    
    return analysis_result


@cli.command()
@click.argument('path', type=click.Path(exists=True), default='.')
@click.option('--output', '-o', type=click.Path(), default='output', help='出力ディレクトリ')
@click.option('--format', '-f', type=click.Choice(['mermaid', 'plantuml', 'drawio', 'all']), 
              default='mermaid', help='出力フォーマット')
@click.option('--types', '-t', multiple=True, 
              help='生成する図の種類 (例: class, er, sequence)')
@click.option('--auto', '-a', is_flag=True, help='自動判定した図をすべて生成')
def generate(path, output, format, types, auto):
    """図を生成"""
    
    console.print(f"[bold blue]Generating diagrams: {path}[/bold blue]")
    
    # 出力ディレクトリ作成
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # プロジェクト解析
    analyzer = ProjectAnalyzer(path)
    analysis_result = analyzer.analyze()
    
    # 生成する図の決定
    if auto:
        detector = DiagramDetector()
        diagrams_to_generate = detector.detect(analysis_result)
        types = [d['type'] for d in diagrams_to_generate]
    elif not types:
        console.print("[red]Error: Please specify --types or --auto option[/red]")
        sys.exit(1)
    
    # 図の生成
    generated_files = []
    
    for diagram_type in track(types, description="Generating diagrams..."):
        if format in ['mermaid', 'all']:
            generator = MermaidGenerator(analysis_result)
            if diagram_type == 'class':
                file_path = generator.generate_class_diagram(output_path)
                if file_path:
                    generated_files.append(file_path)
            elif diagram_type == 'flow':
                file_path = generator.generate_flowchart(output_path)
                if file_path:
                    generated_files.append(file_path)
            elif diagram_type == 'component':
                file_path = generator.generate_component_diagram(output_path)
                if file_path:
                    generated_files.append(file_path)
            elif diagram_type == 'sequence':
                file_path = generator.generate_sequence_diagram(output_path)
                if file_path:
                    generated_files.append(file_path)
        
        # DrawIO形式の生成
        if format in ['drawio', 'all']:
            # Mermaidファイルのみを対象に変換
            mermaid_files = [f for f in generated_files if Path(f).suffix == '.mmd']
            
            if mermaid_files:
                converter = DrawIOFromMermaid()
                for mermaid_file in mermaid_files:
                    mermaid_path = Path(mermaid_file)
                    try:
                        drawio_file = converter.convert_file(mermaid_path, output_path)
                        if drawio_file:
                            generated_files.append(str(drawio_file))
                            console.print(f"  [green]✓[/green] DrawIO変換: {drawio_file.name}")
                    except Exception as e:
                        console.print(f"  [yellow]⚠[/yellow] DrawIO変換失敗 ({mermaid_path.name}): {e}")
                        logger.error(f"DrawIO conversion failed for {mermaid_path}: {e}")
    
    # 結果表示
    console.print(f"\n[bold green]Generation complete![/bold green]")
    console.print(f"[cyan]Generated diagrams:[/cyan]")
    for file in generated_files:
        console.print(f"  - {file}")


@cli.command()
def list_types():
    """Display available diagram types"""
    
    diagram_types = [
        ("class", "Class Diagram", "Display class structure and relationships"),
        ("er", "ER Diagram", "Display database entities and relationships"),
        ("sequence", "Sequence Diagram", "Display process flow in timeline"),
        ("flow", "Flowchart", "Display process flow"),
        ("component", "Component Diagram", "Display system components"),
        ("activity", "Activity Diagram", "Display activity flow"),
        ("state", "State Diagram", "Display state transitions"),
        ("usecase", "Use Case Diagram", "Display functional requirements"),
    ]
    
    table = Table(title="Available Diagram Types")
    table.add_column("Type", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Description", style="yellow")
    
    for type_id, name, description in diagram_types:
        table.add_row(type_id, name, description)
    
    console.print(table)


def main():
    """メインエントリーポイント"""
    logger.add("adg.log", rotation="10 MB")
    cli()


if __name__ == '__main__':
    main()