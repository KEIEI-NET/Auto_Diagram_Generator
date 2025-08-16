"""
PlaywrightによるMermaidダイアグラムの検証と自動修正
ブラウザでの実際のレンダリングをテストし、エラーを検出して修正
"""

import asyncio
import json
import re
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import pytz
from loguru import logger

try:
    from playwright.async_api import async_playwright, Page, Browser, Error as PlaywrightError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not installed. Run: pip install playwright && playwright install")


@dataclass
class MermaidValidationResult:
    """Mermaid検証結果"""
    file_path: str
    is_valid: bool
    render_success: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    screenshot_path: Optional[str] = None
    fixed_content: Optional[str] = None
    fix_applied: bool = False
    render_time_ms: float = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'file_path': self.file_path,
            'is_valid': self.is_valid,
            'render_success': self.render_success,
            'errors': self.errors,
            'warnings': self.warnings,
            'screenshot_path': self.screenshot_path,
            'fix_applied': self.fix_applied,
            'render_time_ms': self.render_time_ms
        }


class MermaidErrorFixer:
    """Mermaidエラーの自動修正"""
    
    def __init__(self):
        self.fix_patterns = {
            'syntax_error': self._fix_syntax_error,
            'undefined_participant': self._fix_undefined_participant,
            'invalid_arrow': self._fix_invalid_arrow,
            'missing_end': self._fix_missing_end,
            'duplicate_class': self._fix_duplicate_class,
            'invalid_character': self._fix_invalid_character,
        }
    
    def fix_content(self, content: str, errors: List[str]) -> Tuple[str, bool, List[str]]:
        """
        エラーを解析して内容を修正
        
        Returns:
            (fixed_content, was_fixed, applied_fixes)
        """
        fixed_content = content
        applied_fixes = []
        was_fixed = False
        
        for error in errors:
            error_type = self._identify_error_type(error)
            if error_type in self.fix_patterns:
                try:
                    fixed_content, fixed = self.fix_patterns[error_type](fixed_content, error)
                    if fixed:
                        was_fixed = True
                        applied_fixes.append(f"Applied fix for: {error_type}")
                except Exception as e:
                    logger.warning(f"Failed to apply fix for {error_type}: {e}")
        
        return fixed_content, was_fixed, applied_fixes
    
    def _identify_error_type(self, error: str) -> str:
        """エラータイプを識別"""
        error_lower = error.lower()
        
        if 'syntax' in error_lower:
            return 'syntax_error'
        elif 'undefined' in error_lower and 'participant' in error_lower:
            return 'undefined_participant'
        elif 'arrow' in error_lower or '->' in error or '-->>' in error:
            return 'invalid_arrow'
        elif 'missing end' in error_lower:
            return 'missing_end'
        elif 'duplicate' in error_lower and 'class' in error_lower:
            return 'duplicate_class'
        elif 'invalid character' in error_lower:
            return 'invalid_character'
        
        return 'unknown'
    
    def _fix_syntax_error(self, content: str, error: str) -> Tuple[str, bool]:
        """構文エラーを修正"""
        lines = content.split('\n')
        fixed_lines = []
        was_fixed = False
        
        for line in lines:
            # コメントでない行をチェック
            if not line.strip().startswith('%%'):
                # 不正な空白を修正
                if line and not line[0].isspace() and '  ' in line:
                    line = re.sub(r'\s+', ' ', line)
                    was_fixed = True
                
                # 閉じ括弧の不足を修正
                if line.count('{') > line.count('}'):
                    line += '}'
                    was_fixed = True
                elif line.count('(') > line.count(')'):
                    line += ')'
                    was_fixed = True
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines), was_fixed
    
    def _fix_undefined_participant(self, content: str, error: str) -> Tuple[str, bool]:
        """未定義の参加者を修正（シーケンス図）"""
        # エラーから参加者名を抽出
        match = re.search(r"undefined.*?['\"](\w+)['\"]", error, re.IGNORECASE)
        if not match:
            return content, False
        
        participant = match.group(1)
        lines = content.split('\n')
        
        # sequenceDiagramの後に参加者を追加
        for i, line in enumerate(lines):
            if 'sequenceDiagram' in line:
                # 既存の参加者定義を確認
                has_participant = any(f'participant {participant}' in l for l in lines)
                if not has_participant:
                    lines.insert(i + 1, f'    participant {participant}')
                    return '\n'.join(lines), True
                break
        
        return content, False
    
    def _fix_invalid_arrow(self, content: str, error: str) -> Tuple[str, bool]:
        """不正な矢印記法を修正"""
        # よくある間違いを修正
        replacements = [
            (r'-->\>', '-->'),  # 二重矢印の修正
            (r'->>', '->>'),    # シーケンス図の矢印
            (r'<--<', '<--'),   # 逆矢印の修正
            (r'=>>', '==>'),    # 太い矢印
            (r'\.\.>', '..>'),  # 点線矢印
        ]
        
        fixed_content = content
        was_fixed = False
        
        for pattern, replacement in replacements:
            if re.search(pattern, fixed_content):
                fixed_content = re.sub(pattern, replacement, fixed_content)
                was_fixed = True
        
        return fixed_content, was_fixed
    
    def _fix_missing_end(self, content: str, error: str) -> Tuple[str, bool]:
        """endステートメントの不足を修正"""
        lines = content.split('\n')
        
        # subgraphのカウント
        subgraph_count = sum(1 for line in lines if 'subgraph' in line.lower())
        end_count = sum(1 for line in lines if line.strip().lower() == 'end')
        
        if subgraph_count > end_count:
            # 不足しているendを追加
            for _ in range(subgraph_count - end_count):
                lines.append('end')
            return '\n'.join(lines), True
        
        return content, False
    
    def _fix_duplicate_class(self, content: str, error: str) -> Tuple[str, bool]:
        """重複クラス定義を修正"""
        lines = content.split('\n')
        seen_classes = set()
        fixed_lines = []
        was_fixed = False
        
        for line in lines:
            # クラス定義をチェック
            class_match = re.match(r'\s*class\s+(\w+)', line)
            if class_match:
                class_name = class_match.group(1)
                if class_name in seen_classes:
                    # 重複を番号付きで修正
                    counter = 2
                    while f"{class_name}{counter}" in seen_classes:
                        counter += 1
                    line = line.replace(class_name, f"{class_name}{counter}", 1)
                    was_fixed = True
                else:
                    seen_classes.add(class_name)
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines), was_fixed
    
    def _fix_invalid_character(self, content: str, error: str) -> Tuple[str, bool]:
        """不正な文字を修正"""
        # Mermaidで問題となる文字を置換
        replacements = {
            '"': "'",  # ダブルクォートをシングルに
            '&': 'and',  # アンパサンドを文字に
            '<': 'lt',   # 小なり記号
            '>': 'gt',   # 大なり記号
            '\t': '    ',  # タブをスペースに
        }
        
        fixed_content = content
        was_fixed = False
        
        for char, replacement in replacements.items():
            if char in fixed_content:
                fixed_content = fixed_content.replace(char, replacement)
                was_fixed = True
        
        # 非ASCII文字を除去（必要に応じて）
        if re.search(r'[^\x00-\x7F]', fixed_content):
            fixed_content = re.sub(r'[^\x00-\x7F]', '', fixed_content)
            was_fixed = True
        
        return fixed_content, was_fixed


class MermaidPlaywrightValidator:
    """PlaywrightによるMermaid検証"""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Args:
            headless: ヘッドレスモードで実行
            timeout: タイムアウト時間（ミリ秒）
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is not installed")
        
        self.headless = headless
        self.timeout = timeout
        self.error_fixer = MermaidErrorFixer()
        self.browser: Optional[Browser] = None
        self.playwright = None
    
    async def __aenter__(self):
        """非同期コンテキストマネージャー開始"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー終了"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def validate_mermaid_file(
        self, 
        mermaid_file: Path,
        auto_fix: bool = True,
        save_screenshot: bool = True,
        max_fix_attempts: int = 3
    ) -> MermaidValidationResult:
        """
        Mermaidファイルを検証
        
        Args:
            mermaid_file: 検証するMermaidファイル
            auto_fix: エラーを自動修正するか
            save_screenshot: スクリーンショットを保存するか
            max_fix_attempts: 最大修正試行回数
        
        Returns:
            検証結果
        """
        result = MermaidValidationResult(
            file_path=str(mermaid_file),
            is_valid=False,
            render_success=False
        )
        
        try:
            # ファイル読み込み
            with open(mermaid_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            content = original_content
            fix_attempt = 0
            
            while fix_attempt <= max_fix_attempts:
                # HTMLページを生成
                html_content = self._generate_test_html(content)
                
                # ブラウザでテスト
                test_result = await self._test_in_browser(
                    html_content, 
                    save_screenshot,
                    mermaid_file.stem
                )
                
                result.errors = test_result['errors']
                result.warnings = test_result['warnings']
                result.render_success = test_result['success']
                result.render_time_ms = test_result['render_time']
                
                if test_result['screenshot_path']:
                    result.screenshot_path = test_result['screenshot_path']
                
                # 成功した場合
                if test_result['success'] and not test_result['errors']:
                    result.is_valid = True
                    
                    # 修正が適用されていた場合、ファイルを更新
                    if auto_fix and fix_attempt > 0 and content != original_content:
                        backup_file = mermaid_file.with_suffix('.mmd.bak')
                        with open(backup_file, 'w', encoding='utf-8') as f:
                            f.write(original_content)
                        
                        with open(mermaid_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        result.fixed_content = content
                        result.fix_applied = True
                        logger.info(f"Fixed Mermaid file: {mermaid_file}")
                    
                    break
                
                # エラーがある場合、自動修正を試みる
                if auto_fix and fix_attempt < max_fix_attempts and test_result['errors']:
                    fixed_content, was_fixed, applied_fixes = self.error_fixer.fix_content(
                        content, 
                        test_result['errors']
                    )
                    
                    if was_fixed:
                        content = fixed_content
                        fix_attempt += 1
                        logger.info(f"Attempting fix #{fix_attempt}: {applied_fixes}")
                        continue
                
                break
            
        except Exception as e:
            result.errors.append(f"Validation error: {e}")
            logger.error(f"Failed to validate {mermaid_file}: {e}")
        
        return result
    
    def _generate_test_html(self, mermaid_content: str) -> str:
        """テスト用HTMLを生成"""
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Mermaid Validation Test</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{ margin: 20px; font-family: Arial; }}
        #errors {{ color: red; font-weight: bold; }}
        #warnings {{ color: orange; }}
        .mermaid {{ background: white; padding: 20px; border: 1px solid #ccc; }}
    </style>
</head>
<body>
    <div id="status">Rendering...</div>
    <div id="errors"></div>
    <div id="warnings"></div>
    <div id="render-time"></div>
    <div class="mermaid" id="diagram">
{mermaid_content}
    </div>
    
    <script>
        let errors = [];
        let warnings = [];
        let renderStart = performance.now();
        
        // Mermaidエラーハンドリング
        window.mermaidErrors = [];
        
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose',
            logLevel: 'error',
            parseError: function(err, hash) {{
                errors.push(err.toString());
                document.getElementById('errors').innerHTML = 'Errors: ' + errors.join(', ');
                window.mermaidErrors.push(err.toString());
            }}
        }});
        
        // カスタムエラーハンドラー
        window.addEventListener('error', function(e) {{
            errors.push(e.message);
            window.mermaidErrors.push(e.message);
        }});
        
        // レンダリング完了チェック
        mermaid.init(undefined, document.querySelector('.mermaid')).then(() => {{
            let renderEnd = performance.now();
            let renderTime = renderEnd - renderStart;
            
            document.getElementById('status').innerHTML = 'Render complete';
            document.getElementById('render-time').innerHTML = 'Render time: ' + renderTime.toFixed(2) + 'ms';
            
            // SVGが生成されたかチェック
            const svg = document.querySelector('.mermaid svg');
            if (svg) {{
                window.renderSuccess = true;
                window.renderTime = renderTime;
            }} else {{
                window.renderSuccess = false;
                errors.push('No SVG generated');
            }}
            
            window.validationComplete = true;
        }}).catch((err) => {{
            errors.push('Render failed: ' + err.toString());
            window.mermaidErrors.push(err.toString());
            window.renderSuccess = false;
            window.validationComplete = true;
        }});
    </script>
</body>
</html>'''
    
    async def _test_in_browser(
        self,
        html_content: str,
        save_screenshot: bool,
        filename_prefix: str
    ) -> Dict[str, Any]:
        """ブラウザでテスト実行"""
        page = await self.browser.new_page()
        result = {
            'success': False,
            'errors': [],
            'warnings': [],
            'render_time': 0,
            'screenshot_path': None
        }
        
        try:
            # HTMLを一時ファイルに保存
            tmp_file = None
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix='.html',
                    delete=False,
                    encoding='utf-8'
                ) as tmp:
                    tmp.write(html_content)
                    tmp_path = tmp.name
                    tmp_file = tmp
                
                # ページを開く
                await page.goto(f'file:///{tmp_path}', wait_until='networkidle')
            except Exception as e:
                # エラーが発生した場合も一時ファイルを削除
                if tmp_path and Path(tmp_path).exists():
                    Path(tmp_path).unlink(missing_ok=True)
                raise e
            
            # レンダリング完了を待つ
            await page.wait_for_function(
                'window.validationComplete === true',
                timeout=self.timeout
            )
            
            # 結果を取得
            result['success'] = await page.evaluate('window.renderSuccess || false')
            result['errors'] = await page.evaluate('window.mermaidErrors || []')
            result['render_time'] = await page.evaluate('window.renderTime || 0')
            
            # コンソールメッセージを収集
            page.on('console', lambda msg: self._handle_console_message(msg, result))
            
            # スクリーンショット保存
            if save_screenshot and result['success']:
                screenshot_dir = Path('output/screenshots')
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y%m%d_%H%M%S')
                screenshot_path = screenshot_dir / f'{filename_prefix}_{timestamp}.png'
                
                # ダイアグラム要素のみをキャプチャ
                element = await page.query_selector('.mermaid')
                if element:
                    await element.screenshot(path=str(screenshot_path))
                    result['screenshot_path'] = str(screenshot_path)
            
            # 一時ファイルを削除
            Path(tmp_path).unlink(missing_ok=True)
            
        except PlaywrightError as e:
            result['errors'].append(f"Playwright error: {e}")
        except Exception as e:
            result['errors'].append(f"Test error: {e}")
        finally:
            await page.close()
        
        return result
    
    def _handle_console_message(self, msg, result: Dict[str, Any]):
        """コンソールメッセージを処理"""
        if msg.type == 'error':
            result['errors'].append(msg.text)
        elif msg.type == 'warning':
            result['warnings'].append(msg.text)
    
    async def validate_batch(
        self,
        directory: Path,
        pattern: str = "*.mmd",
        auto_fix: bool = True
    ) -> List[MermaidValidationResult]:
        """
        ディレクトリ内のMermaidファイルを一括検証
        
        Args:
            directory: 検証対象ディレクトリ
            pattern: ファイルパターン
            auto_fix: 自動修正を有効にする
        
        Returns:
            検証結果のリスト
        """
        results = []
        mermaid_files = list(directory.glob(pattern))
        
        logger.info(f"Found {len(mermaid_files)} Mermaid files to validate")
        
        for mermaid_file in mermaid_files:
            logger.info(f"Validating: {mermaid_file}")
            result = await self.validate_mermaid_file(mermaid_file, auto_fix=auto_fix)
            results.append(result)
            
            if result.is_valid:
                logger.success(f"✓ Valid: {mermaid_file.name}")
            else:
                logger.error(f"✗ Invalid: {mermaid_file.name} - {result.errors}")
        
        return results
    
    def generate_validation_report(
        self,
        results: List[MermaidValidationResult],
        output_file: Path
    ) -> None:
        """検証レポートを生成"""
        report = {
            'timestamp': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat(),
            'total': len(results),
            'valid': sum(1 for r in results if r.is_valid),
            'invalid': sum(1 for r in results if not r.is_valid),
            'fixed': sum(1 for r in results if r.fix_applied),
            'average_render_time_ms': sum(r.render_time_ms for r in results) / len(results) if results else 0,
            'results': [r.to_dict() for r in results]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Validation report saved: {output_file}")


# 同期的なラッパー関数
def validate_mermaid_with_playwright(
    mermaid_file: Path,
    auto_fix: bool = True,
    headless: bool = True
) -> MermaidValidationResult:
    """
    同期的にMermaidファイルを検証
    
    Args:
        mermaid_file: 検証するファイル
        auto_fix: 自動修正を有効にする
        headless: ヘッドレスモードで実行
    
    Returns:
        検証結果
    """
    async def _validate():
        async with MermaidPlaywrightValidator(headless=headless) as validator:
            return await validator.validate_mermaid_file(mermaid_file, auto_fix=auto_fix)
    
    return asyncio.run(_validate())


def validate_directory_with_playwright(
    directory: Path,
    pattern: str = "*.mmd",
    auto_fix: bool = True,
    headless: bool = True
) -> List[MermaidValidationResult]:
    """
    ディレクトリ内のMermaidファイルを一括検証
    
    Args:
        directory: 検証対象ディレクトリ
        pattern: ファイルパターン  
        auto_fix: 自動修正を有効にする
        headless: ヘッドレスモードで実行
    
    Returns:
        検証結果のリスト
    """
    async def _validate():
        async with MermaidPlaywrightValidator(headless=headless) as validator:
            return await validator.validate_batch(directory, pattern, auto_fix)
    
    return asyncio.run(_validate())


# テスト関数
def test_mermaid_validation():
    """Mermaid検証のテスト"""
    from adg.core.analyzer import ProjectAnalyzer
    from adg.generators.mermaid_refactored import MermaidGeneratorRefactored
    
    # プロジェクト解析
    analyzer = ProjectAnalyzer("src")
    analysis_result = analyzer.analyze()
    
    # Mermaidファイル生成
    output_dir = Path("output/playwright_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generator = MermaidGeneratorRefactored(analysis_result)
    generator.generate_all(output_dir)
    
    # Playwrightで検証
    results = validate_directory_with_playwright(
        output_dir,
        auto_fix=True,
        headless=False  # デバッグ用に表示
    )
    
    # レポート生成
    validator = MermaidPlaywrightValidator()
    validator.generate_validation_report(
        results,
        output_dir / "playwright_validation_report.json"
    )
    
    # 結果サマリー
    valid_count = sum(1 for r in results if r.is_valid)
    fixed_count = sum(1 for r in results if r.fix_applied)
    
    print(f"\n=== Validation Summary ===")
    print(f"Total files: {len(results)}")
    print(f"Valid: {valid_count}")
    print(f"Fixed: {fixed_count}")
    print(f"Invalid: {len(results) - valid_count}")
    
    return results


if __name__ == "__main__":
    # Playwrightのインストール確認
    if not PLAYWRIGHT_AVAILABLE:
        print("Installing Playwright...")
        import subprocess
        subprocess.run(["pip", "install", "playwright"])
        subprocess.run(["playwright", "install", "chromium"])
    
    # テスト実行
    test_results = test_mermaid_validation()