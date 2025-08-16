"""
CLI コマンドインターフェース
"""

import click
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import track
from loguru import logger

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from adg.core.analyzer import ProjectAnalyzer
from adg.core.detector import DiagramDetector
from adg.generators.mermaid import MermaidGenerator

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
    
    console.print(f"[bold blue]🔍 プロジェクトを解析中: {path}[/bold blue]")
    
    # プロジェクト解析
    analyzer = ProjectAnalyzer(path)
    with console.status("[bold green]コードを解析中..."):
        analysis_result = analyzer.analyze()
    
    # 結果サマリーを表示
    summary = analysis_result["summary"]
    table = Table(title="解析結果サマリー")
    table.add_column("項目", style="cyan")
    table.add_column("数", style="magenta")
    
    table.add_row("ファイル数", str(summary["total_files"]))
    table.add_row("クラス数", str(summary["total_classes"]))
    table.add_row("関数数", str(summary["total_functions"]))
    
    console.print(table)
    
    if verbose:
        console.print("\n[bold yellow]📁 解析されたファイル:[/bold yellow]")
        for file_path in analysis_result["files"]:
            console.print(f"  • {file_path}")
    
    # 図の判定
    detector = DiagramDetector()
    recommended_diagrams = detector.detect(analysis_result)
    
    console.print(f"\n[bold green]✨ 推奨される図:[/bold green]")
    for diagram in recommended_diagrams:
        console.print(f"  • {diagram['type']}: {diagram['reason']}")
    
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
    
    console.print(f"[bold blue]🎨 図を生成中: {path}[/bold blue]")
    
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
        console.print("[red]エラー: --types または --auto オプションを指定してください[/red]")
        sys.exit(1)
    
    # 図の生成
    generated_files = []
    
    for diagram_type in track(types, description="図を生成中..."):
        if format in ['mermaid', 'all']:
            generator = MermaidGenerator(analysis_result)
            if diagram_type == 'class':
                file_path = generator.generate_class_diagram(output_path)
                if file_path:
                    generated_files.append(file_path)
            # 他の図種も追加予定
    
    # 結果表示
    console.print(f"\n[bold green]✅ 生成完了![/bold green]")
    console.print(f"[cyan]生成された図:[/cyan]")
    for file in generated_files:
        console.print(f"  • {file}")


@cli.command()
def list_types():
    """生成可能な図の種類を表示"""
    
    diagram_types = [
        ("class", "クラス図", "クラスの構造と関係を表示"),
        ("er", "ER図", "データベースのエンティティと関係を表示"),
        ("sequence", "シーケンス図", "処理の流れを時系列で表示"),
        ("flow", "フロー図", "処理フローを表示"),
        ("component", "コンポーネント図", "システムコンポーネントを表示"),
        ("activity", "アクティビティ図", "活動の流れを表示"),
        ("state", "状態遷移図", "状態の遷移を表示"),
        ("usecase", "ユースケース図", "機能要件を表示"),
    ]
    
    table = Table(title="生成可能な図の種類")
    table.add_column("タイプ", style="cyan")
    table.add_column("名称", style="magenta")
    table.add_column("説明", style="yellow")
    
    for type_id, name, description in diagram_types:
        table.add_row(type_id, name, description)
    
    console.print(table)


def main():
    """メインエントリーポイント"""
    logger.add("adg.log", rotation="10 MB")
    cli()


if __name__ == '__main__':
    main()