"""
Mermaidファイルのビューワーテスト機能
ブラウザでの表示検証とレンダリングテスト
"""

import os
import json
import subprocess
import tempfile
import webbrowser
from pathlib import Path
from typing import Optional, Dict, Any, List
from loguru import logger


class MermaidViewerTest:
    """Mermaidファイルのビューワーテスト"""
    
    def __init__(self):
        self.test_results: List[Dict[str, Any]] = []
    
    def test_mermaid_file(self, mermaid_file: Path) -> Dict[str, Any]:
        """
        Mermaidファイルをテスト
        
        Returns:
            テスト結果の辞書
        """
        result = {
            'file': str(mermaid_file),
            'exists': False,
            'readable': False,
            'valid_syntax': False,
            'html_generated': False,
            'cli_test': False,
            'errors': []
        }
        
        try:
            # ファイル存在チェック
            if not mermaid_file.exists():
                result['errors'].append("ファイルが存在しません")
                return result
            result['exists'] = True
            
            # 読み込みチェック
            try:
                with open(mermaid_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                result['readable'] = True
            except Exception as e:
                result['errors'].append(f"読み込みエラー: {e}")
                return result
            
            # 基本構文チェック
            result['valid_syntax'] = self._check_basic_syntax(content, result)
            
            # HTMLビューワー生成テスト
            html_file = self._generate_html_viewer(mermaid_file, content)
            if html_file:
                result['html_generated'] = True
                result['html_file'] = str(html_file)
            
            # Mermaid CLIテスト（インストールされている場合）
            result['cli_test'] = self._test_mermaid_cli(mermaid_file, result)
            
        except Exception as e:
            result['errors'].append(f"テスト中のエラー: {e}")
        
        self.test_results.append(result)
        return result
    
    def _check_basic_syntax(self, content: str, result: Dict[str, Any]) -> bool:
        """基本的な構文をチェック"""
        if not content.strip():
            result['errors'].append("空のファイル")
            return False
        
        # ダイアグラムタイプの確認
        valid_starts = [
            'graph', 'flowchart', 'sequenceDiagram', 'classDiagram',
            'stateDiagram', 'erDiagram', 'gantt', 'pie', 'gitGraph'
        ]
        
        first_line = content.strip().split('\n')[0]
        # コメントをスキップ
        while first_line.startswith('%%'):
            lines = content.strip().split('\n')
            for line in lines:
                if not line.startswith('%%'):
                    first_line = line
                    break
        
        diagram_type = first_line.split()[0] if first_line else ""
        
        if not any(first_line.startswith(start) for start in valid_starts):
            result['errors'].append(f"不正なダイアグラムタイプ: {diagram_type}")
            return False
        
        return True
    
    def _generate_html_viewer(self, mermaid_file: Path, content: str) -> Optional[Path]:
        """HTMLビューワーを生成"""
        try:
            html_template = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Mermaid Diagram Viewer - {filename}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        .info {{
            background-color: #e9ecef;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .mermaid {{
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .error {{
            color: red;
            font-weight: bold;
            padding: 10px;
            background-color: #ffe0e0;
            border-radius: 5px;
        }}
        .source {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
            font-family: monospace;
            white-space: pre-wrap;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <h1>Mermaid Diagram Viewer</h1>
    <div class="info">
        <strong>File:</strong> {filename}<br>
        <strong>Generated:</strong> {timestamp}<br>
        <strong>Type:</strong> <span id="diagram-type">Detecting...</span>
    </div>
    
    <h2>Rendered Diagram</h2>
    <div id="diagram-container">
        <div class="mermaid">
{content}
        </div>
    </div>
    
    <h2>Source Code</h2>
    <div class="source">{content}</div>
    
    <div id="error-container"></div>
    
    <script>
        mermaid.initialize({{ 
            startOnLoad: true,
            theme: 'default',
            themeVariables: {{
                primaryColor: '#007bff',
                primaryTextColor: '#fff',
                primaryBorderColor: '#0056b3',
                lineColor: '#333',
                secondaryColor: '#6c757d',
                tertiaryColor: '#f8f9fa'
            }},
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'basis'
            }},
            securityLevel: 'loose'
        }});
        
        // エラーハンドリング
        mermaid.parseError = function(err, hash) {{
            console.error('Mermaid parsing error:', err);
            document.getElementById('error-container').innerHTML = 
                '<div class="error">Rendering Error: ' + err + '</div>';
        }};
        
        // ダイアグラムタイプの検出
        const content = `{content}`;
        const lines = content.trim().split('\\n');
        let diagramType = 'Unknown';
        
        for (const line of lines) {{
            if (!line.startsWith('%%')) {{
                diagramType = line.split(' ')[0];
                break;
            }}
        }}
        
        document.getElementById('diagram-type').textContent = diagramType;
        
        // レンダリング成功の確認
        setTimeout(() => {{
            const svg = document.querySelector('.mermaid svg');
            if (svg) {{
                console.log('Diagram rendered successfully');
            }} else {{
                console.error('Failed to render diagram');
                document.getElementById('error-container').innerHTML = 
                    '<div class="error">Failed to render diagram. Check the syntax.</div>';
            }}
        }}, 1000);
    </script>
</body>
</html>'''
            
            # HTMLファイルを生成
            html_file = mermaid_file.with_suffix('.html')
            
            from datetime import datetime
            import html
            
            # XSS対策：HTMLエスケープを適用
            safe_filename = html.escape(mermaid_file.name)
            safe_timestamp = html.escape(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            # JavaScriptコンテキスト用のエスケープ
            safe_content = content.replace('\\', '\\\\').replace('`', '\\`').replace('</', '<\\/')
            
            html_content = html_template.format(
                filename=safe_filename,
                timestamp=safe_timestamp,
                content=safe_content
            )
            
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Generated HTML viewer: {html_file}")
            return html_file
            
        except Exception as e:
            logger.error(f"Failed to generate HTML viewer: {e}")
            return None
    
    def _test_mermaid_cli(self, mermaid_file: Path, result: Dict[str, Any]) -> bool:
        """Mermaid CLIでのテスト（mmdc）"""
        try:
            import shlex
            from adg.utils.security import validate_path
            
            # パスを検証
            try:
                safe_path = validate_path(mermaid_file)
            except Exception as e:
                result['errors'].append(f"Invalid file path: {e}")
                return False
            
            # mmdcコマンドの存在確認（シェル経由ではなく直接実行）
            mmdc_check = subprocess.run(
                ['npx', 'mmdc', '--version'],
                capture_output=True,
                text=True,
                timeout=5,
                shell=False  # シェル経由を明示的に無効化
            )
            
            if mmdc_check.returncode != 0:
                result['errors'].append("Mermaid CLI (mmdc) not found")
                return False
            
            # SVG生成テスト（安全なパス使用）
            svg_file = safe_path.with_suffix('.svg')
            generate_result = subprocess.run(
                ['npx', 'mmdc', '-i', str(safe_path), '-o', str(svg_file)],
                capture_output=True,
                text=True,
                timeout=30,
                shell=False  # シェル経由を明示的に無効化
            )
            
            if generate_result.returncode == 0 and svg_file.exists():
                result['svg_file'] = str(svg_file)
                return True
            else:
                result['errors'].append(f"CLI generation failed: {generate_result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            result['errors'].append("CLI test timeout")
            return False
        except FileNotFoundError:
            result['errors'].append("npx command not found")
            return False
        except Exception as e:
            result['errors'].append(f"CLI test error: {e}")
            return False
    
    def open_in_browser(self, html_file: Path) -> bool:
        """ブラウザでHTMLファイルを開く"""
        try:
            webbrowser.open(f'file://{html_file.absolute()}')
            return True
        except Exception as e:
            logger.error(f"Failed to open browser: {e}")
            return False
    
    def batch_test(self, directory: Path, pattern: str = "*.mmd") -> Dict[str, Any]:
        """
        ディレクトリ内のすべてのMermaidファイルをテスト
        
        Args:
            directory: テスト対象ディレクトリ
            pattern: ファイルパターン
        
        Returns:
            バッチテスト結果
        """
        results = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'files': []
        }
        
        mermaid_files = list(directory.glob(pattern))
        results['total'] = len(mermaid_files)
        
        for mermaid_file in mermaid_files:
            test_result = self.test_mermaid_file(mermaid_file)
            
            if test_result['valid_syntax'] and test_result['html_generated']:
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            results['files'].append(test_result)
        
        return results
    
    def generate_test_report(self, output_file: Path) -> None:
        """テストレポートを生成"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.test_results),
            'results': self.test_results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Test report generated: {output_file}")


class MermaidLiveServer:
    """Mermaidダイアグラムのライブプレビューサーバー"""
    
    @staticmethod
    def create_live_preview(mermaid_file: Path, port: int = 8080) -> str:
        """
        ライブプレビュー用のHTMLを生成
        
        Returns:
            プレビューURL
        """
        try:
            import http.server
            import socketserver
            import threading
            
            # HTMLコンテンツを生成
            with open(mermaid_file, 'r', encoding='utf-8') as f:
                mermaid_content = f.read()
            
            html_content = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Mermaid Live Preview</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{ margin: 20px; font-family: Arial; }}
        .mermaid {{ background: white; padding: 20px; }}
    </style>
</head>
<body>
    <h1>Mermaid Live Preview - {mermaid_file.name}</h1>
    <div class="mermaid">
{mermaid_content}
    </div>
    <script>
        mermaid.initialize({{ startOnLoad: true }});
        // Auto-reload every 2 seconds
        setInterval(() => location.reload(), 2000);
    </script>
</body>
</html>'''
            
            # 一時ファイルに保存
            temp_dir = Path(tempfile.gettempdir()) / 'mermaid_preview'
            temp_dir.mkdir(exist_ok=True)
            
            html_file = temp_dir / 'index.html'
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # サーバーを起動
            os.chdir(temp_dir)
            
            Handler = http.server.SimpleHTTPRequestHandler
            with socketserver.TCPServer(("", port), Handler) as httpd:
                url = f"http://localhost:{port}"
                logger.info(f"Serving at {url}")
                
                # ブラウザを開く
                webbrowser.open(url)
                
                # サーバーを別スレッドで実行
                server_thread = threading.Thread(target=httpd.serve_forever)
                server_thread.daemon = True
                server_thread.start()
                
                return url
                
        except Exception as e:
            logger.error(f"Failed to start live server: {e}")
            return ""


# 使用例とテスト関数
def test_mermaid_generation():
    """Mermaid生成とビューワーのテスト"""
    from adg.core.analyzer import ProjectAnalyzer
    from adg.generators.mermaid_refactored import MermaidGeneratorRefactored
    
    # プロジェクトを解析
    analyzer = ProjectAnalyzer("src")
    analysis_result = analyzer.analyze()
    
    # Mermaidファイルを生成
    output_dir = Path("output/test")
    generator = MermaidGeneratorRefactored(analysis_result)
    results = generator.generate_all(output_dir)
    
    # ビューワーテストを実行
    viewer_test = MermaidViewerTest()
    test_results = viewer_test.batch_test(output_dir)
    
    # レポート生成
    viewer_test.generate_test_report(output_dir / "test_report.json")
    
    # 成功したファイルをブラウザで開く
    for result in viewer_test.test_results:
        if result.get('html_generated'):
            html_file = Path(result['html_file'])
            viewer_test.open_in_browser(html_file)
            break
    
    return test_results


if __name__ == "__main__":
    # テスト実行
    test_results = test_mermaid_generation()
    print(f"Test Results: {test_results}")