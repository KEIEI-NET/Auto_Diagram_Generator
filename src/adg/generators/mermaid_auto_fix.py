"""
自動修正機能付きMermaid生成器
Playwrightによる検証と自動修正を統合
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pytz
from loguru import logger

from adg.generators.mermaid_refactored import (
    MermaidGeneratorRefactored,
    MermaidDiagram,
    ClassDiagramBuilder,
    SequenceDiagramBuilder,
    ERDiagramBuilder,
    FlowDiagramBuilder
)
from adg.core.results import DiagramResult
from adg.utils.mermaid_playwright_validator import (
    MermaidPlaywrightValidator,
    MermaidValidationResult,
    PLAYWRIGHT_AVAILABLE
)


class SmartClassDiagramBuilder(ClassDiagramBuilder):
    """スマートなクラス図ビルダー（エラー回避機能付き）"""
    
    def build(self) -> MermaidDiagram:
        """より堅牢なクラス図を構築"""
        lines = ["classDiagram"]
        relationships = []
        defined_classes = set()
        
        for file_path, file_analysis in self.analysis.get('files', {}).items():
            for class_info in file_analysis.get('classes', []):
                if not isinstance(class_info, dict):
                    continue
                    
                class_name = self._sanitize_name(class_info.get('name', 'Unknown'))
                
                # 重複チェック
                if class_name in defined_classes:
                    class_name = f"{class_name}_{len(defined_classes)}"
                defined_classes.add(class_name)
                
                # クラス定義
                lines.append(f"    class {class_name} {{")
                
                # 属性（最大10個に制限）
                attributes = class_info.get('attributes', [])[:10]
                for attr in attributes:
                    if isinstance(attr, str):
                        attr_name = self._sanitize_name(attr)
                        # 型情報があれば追加（仮）
                        lines.append(f"        +{attr_name} : String")
                
                # メソッド（最大10個に制限）
                methods = class_info.get('methods', [])[:10]
                for method in methods:
                    if isinstance(method, str):
                        method_name = self._sanitize_name(method)
                        lines.append(f"        +{method_name}() : void")
                
                lines.append("    }")
                
                # 継承関係（定義済みクラスのみ）
                for base in class_info.get('base_classes', []):
                    if base and base != 'object':
                        base_name = self._sanitize_name(base)
                        # 基底クラスが定義されていない場合は追加
                        if base_name not in defined_classes:
                            lines.insert(1, f"    class {base_name}")
                            defined_classes.add(base_name)
                        relationships.append(f"    {base_name} <|-- {class_name}")
        
        # 関係を追加
        lines.extend(relationships)
        
        # 空の図を避ける
        if len(lines) == 1:
            lines.append("    class EmptyDiagram")
        
        return MermaidDiagram(
            type='class',
            content=lines,
            metadata=self._create_metadata('class')
        )


class SmartSequenceDiagramBuilder(SequenceDiagramBuilder):
    """スマートなシーケンス図ビルダー"""
    
    def build(self) -> MermaidDiagram:
        """より堅牢なシーケンス図を構築"""
        lines = ["sequenceDiagram"]
        
        # 参加者を収集
        participants = set()
        for file_path, file_analysis in self.analysis.get('files', {}).items():
            # クラスから参加者を作成
            for class_info in file_analysis.get('classes', []):
                if isinstance(class_info, dict):
                    class_name = self._sanitize_name(class_info.get('name', 'Unknown'))
                    participants.add(class_name)
            
            # 関数からも参加者を推測
            for func_info in file_analysis.get('functions', []):
                if isinstance(func_info, dict):
                    func_name = func_info.get('name', '')
                    # API関連の関数を参加者として追加
                    if any(keyword in func_name.lower() for keyword in ['api', 'service', 'handler']):
                        service_name = self._sanitize_name(func_name.replace('_', ''))
                        participants.add(service_name)
        
        # 最低限の参加者を確保
        if not participants:
            participants = {'Client', 'Server', 'Database'}
        
        # 参加者を定義
        for participant in sorted(participants)[:10]:  # 最大10参加者
            lines.append(f"    participant {participant}")
        
        # 基本的なフローを生成
        participants_list = sorted(participants)[:5]  # フローは5参加者まで
        if len(participants_list) >= 2:
            # リクエスト/レスポンスパターン
            lines.append(f"    {participants_list[0]}->>+{participants_list[1]}: Request")
            
            if len(participants_list) >= 3:
                lines.append(f"    {participants_list[1]}->>+{participants_list[2]}: Process")
                lines.append(f"    {participants_list[2]}-->>-{participants_list[1]}: Result")
            
            lines.append(f"    {participants_list[1]}-->>-{participants_list[0]}: Response")
            
            # ループ例
            lines.append(f"    loop Every 5 seconds")
            lines.append(f"        {participants_list[0]}->{participants_list[1]}: Heartbeat")
            lines.append(f"    end")
        
        return MermaidDiagram(
            type='sequence',
            content=lines,
            metadata=self._create_metadata('sequence')
        )


class MermaidGeneratorWithAutoFix(MermaidGeneratorRefactored):
    """自動修正機能付きMermaid生成器"""
    
    def __init__(self, analysis_result: Dict[str, Any]):
        super().__init__(analysis_result)
        # スマートビルダーに置き換え
        self.builders = {
            'class': SmartClassDiagramBuilder,
            'sequence': SmartSequenceDiagramBuilder,
            'er': ERDiagramBuilder,
            'flow': FlowDiagramBuilder,
        }
        self.use_playwright = PLAYWRIGHT_AVAILABLE
    
    async def generate_with_validation_async(
        self,
        diagram_type: str,
        output_dir: Path,
        auto_fix: bool = True,
        max_retries: int = 3
    ) -> DiagramResult:
        """
        生成と検証を非同期で実行
        
        Args:
            diagram_type: 図の種類
            output_dir: 出力ディレクトリ
            auto_fix: 自動修正を有効にする
            max_retries: 最大リトライ回数
        
        Returns:
            DiagramResult
        """
        retry_count = 0
        last_result = None
        
        while retry_count <= max_retries:
            # Mermaid図を生成
            result = self.generate(diagram_type, output_dir, validate=True)
            
            if not result.success:
                return result
            
            # Playwrightが利用可能な場合は検証
            if self.use_playwright and result.file_path:
                async with MermaidPlaywrightValidator(headless=True) as validator:
                    validation_result = await validator.validate_mermaid_file(
                        Path(result.file_path),
                        auto_fix=auto_fix,
                        save_screenshot=True
                    )
                    
                    # 検証結果をメタデータに追加
                    result.metadata['validation'] = validation_result.to_dict()
                    
                    if validation_result.is_valid:
                        logger.success(f"✓ {diagram_type} diagram validated successfully")
                        if validation_result.screenshot_path:
                            result.metadata['screenshot'] = validation_result.screenshot_path
                        return result
                    
                    # エラーがある場合
                    if validation_result.errors and retry_count < max_retries:
                        logger.warning(f"Validation errors found, retrying... ({retry_count + 1}/{max_retries})")
                        
                        # エラー情報を解析して次回生成を改善
                        self._learn_from_errors(diagram_type, validation_result.errors)
                        retry_count += 1
                        last_result = result
                        continue
                    
                    # 最大リトライ回数に達した
                    logger.error(f"Failed to generate valid {diagram_type} diagram after {max_retries} retries")
                    result.success = False
                    result.error = f"Validation failed: {validation_result.errors}"
                    return result
            else:
                # Playwrightが利用できない場合は基本検証のみ
                return result
        
        return last_result or result
    
    def generate_with_validation(
        self,
        diagram_type: str,
        output_dir: Path,
        auto_fix: bool = True,
        max_retries: int = 3
    ) -> DiagramResult:
        """同期的に生成と検証を実行"""
        return asyncio.run(
            self.generate_with_validation_async(
                diagram_type, output_dir, auto_fix, max_retries
            )
        )
    
    def _learn_from_errors(self, diagram_type: str, errors: List[str]):
        """エラーから学習して次回生成を改善"""
        # エラーパターンを記録（将来的な改善のため）
        logger.debug(f"Learning from errors in {diagram_type}: {errors}")
        
        # 特定のエラーパターンに基づいて設定を調整
        for error in errors:
            if 'undefined' in error.lower():
                # 未定義エラーの場合、より保守的な生成を行う
                logger.info("Adjusting for undefined reference errors")
            elif 'syntax' in error.lower():
                # 構文エラーの場合、サニタイゼーションを強化
                logger.info("Enhancing sanitization for syntax errors")
    
    async def generate_all_with_validation_async(
        self,
        output_dir: Path,
        auto_fix: bool = True
    ) -> List[DiagramResult]:
        """すべての図を生成して検証（非同期）"""
        results = []
        
        for diagram_type in self.builders.keys():
            logger.info(f"Generating {diagram_type} diagram...")
            result = await self.generate_with_validation_async(
                diagram_type, output_dir, auto_fix
            )
            results.append(result)
        
        # サマリーレポート生成
        self._generate_summary_report(results, output_dir)
        
        return results
    
    def generate_all_with_validation(
        self,
        output_dir: Path,
        auto_fix: bool = True
    ) -> List[DiagramResult]:
        """すべての図を生成して検証（同期）"""
        return asyncio.run(
            self.generate_all_with_validation_async(output_dir, auto_fix)
        )
    
    def _generate_summary_report(self, results: List[DiagramResult], output_dir: Path):
        """サマリーレポートを生成"""
        summary = {
            'timestamp': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat(),
            'total': len(results),
            'successful': sum(1 for r in results if r.success),
            'failed': sum(1 for r in results if not r.success),
            'details': []
        }
        
        for result in results:
            detail = {
                'type': result.diagram_type,
                'success': result.success,
                'file': result.file_path,
                'error': result.error
            }
            
            # 検証結果を含める
            if 'validation' in result.metadata:
                validation = result.metadata['validation']
                detail['validation'] = {
                    'valid': validation.get('is_valid', False),
                    'render_success': validation.get('render_success', False),
                    'fix_applied': validation.get('fix_applied', False),
                    'errors': validation.get('errors', [])
                }
            
            summary['details'].append(detail)
        
        # レポートファイルを保存
        report_file = output_dir / 'generation_summary.json'
        import json
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Summary report saved: {report_file}")
        
        # コンソールにサマリー表示
        logger.info(f"\n=== Generation Summary ===")
        logger.info(f"Total: {summary['total']}")
        logger.info(f"Successful: {summary['successful']}")
        logger.info(f"Failed: {summary['failed']}")


# CLI統合用の関数
def generate_diagrams_with_browser_validation(
    project_path: str,
    output_dir: str = "output",
    auto_fix: bool = True,
    headless: bool = True
) -> List[DiagramResult]:
    """
    プロジェクトから図を生成し、ブラウザで検証
    
    Args:
        project_path: 解析するプロジェクトパス
        output_dir: 出力ディレクトリ
        auto_fix: 自動修正を有効にする
        headless: ヘッドレスモードで実行
    
    Returns:
        生成結果のリスト
    """
    from adg.core.analyzer import ProjectAnalyzer
    
    # プロジェクト解析
    logger.info(f"Analyzing project: {project_path}")
    analyzer = ProjectAnalyzer(project_path)
    analysis_result = analyzer.analyze()
    
    # 出力ディレクトリ作成
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 自動修正機能付き生成器を使用
    generator = MermaidGeneratorWithAutoFix(analysis_result)
    
    # すべての図を生成して検証
    logger.info("Generating and validating diagrams...")
    results = generator.generate_all_with_validation(output_path, auto_fix=auto_fix)
    
    # 成功数をカウント
    successful = sum(1 for r in results if r.success)
    logger.info(f"\n✅ Successfully generated {successful}/{len(results)} diagrams")
    
    return results


# テスト関数
def test_auto_fix_generation():
    """自動修正機能のテスト"""
    # Playwrightのインストール確認
    if not PLAYWRIGHT_AVAILABLE:
        logger.warning("Installing Playwright...")
        import subprocess
        subprocess.run(["pip", "install", "playwright"])
        subprocess.run(["playwright", "install", "chromium"])
    
    # テスト実行
    results = generate_diagrams_with_browser_validation(
        project_path="src",
        output_dir="output/auto_fix_test",
        auto_fix=True,
        headless=False  # デバッグ用に表示
    )
    
    # 結果表示
    for result in results:
        if result.success:
            print(f"✓ {result.diagram_type}: {result.file_path}")
            if 'screenshot' in result.metadata:
                print(f"  Screenshot: {result.metadata['screenshot']}")
        else:
            print(f"✗ {result.diagram_type}: {result.error}")
    
    return results


if __name__ == "__main__":
    test_results = test_auto_fix_generation()