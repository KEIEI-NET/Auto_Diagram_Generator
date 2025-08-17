"""
統合型セキュア多言語アナライザー
secure_analyzerとmulti_language_analyzerを統合
"""

import ast
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from loguru import logger

from adg.core.analyzer import CodeElement, ClassInfo, FunctionInfo, ImportInfo
from adg.core.secure_analyzer import (
    SecurityConfig,
    SecurityError,
    PathValidator,
    SecureFileHandler,
    SafeRegexPatterns,
    AnalysisResult,
    SerializationMixin,
    SecureLanguageAnalyzer,
    AnalysisCache,
    SecurePythonAnalyzer
)


class IntegratedLanguageAnalyzer(SecureLanguageAnalyzer):
    """統合型言語アナライザー基底クラス"""
    
    def __init__(self, file_path: str, base_path: Optional[Path] = None):
        """
        初期化
        
        Args:
            file_path: 解析するファイルパス
            base_path: ベースディレクトリ（セキュリティチェック用）
        """
        super().__init__(file_path, base_path)
        self.use_ast = self.supports_ast_parsing()
    
    def supports_ast_parsing(self) -> bool:
        """AST解析をサポートするか"""
        return False
    
    def analyze_with_ast(self) -> Dict[str, Any]:
        """AST解析（サブクラスでオーバーライド）"""
        raise NotImplementedError("AST parsing not implemented for this language")
    
    def analyze_with_regex(self) -> Dict[str, Any]:
        """正規表現ベースの解析（フォールバック）"""
        return self.analyze()
    
    def analyze(self) -> Dict[str, Any]:
        """解析実行"""
        if self.use_ast:
            try:
                return self.analyze_with_ast()
            except Exception as e:
                logger.warning(f"AST parsing failed, falling back to regex: {e}")
                return self.analyze_with_regex()
        else:
            return self.analyze_with_regex()


class IntegratedPythonAnalyzer(IntegratedLanguageAnalyzer):
    """Python用統合アナライザー（AST対応）"""
    
    def get_language_name(self) -> str:
        return 'python'
    
    def supports_ast_parsing(self) -> bool:
        return True
    
    def analyze_with_ast(self) -> Dict[str, Any]:
        """Python ASTを使用した解析"""
        try:
            tree = ast.parse(self.content)
            
            classes = []
            functions = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(self._extract_class_info(node))
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    # トップレベル関数のみ
                    if not self._is_nested_function(node, tree):
                        functions.append(self._extract_function_info(node))
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    imports.append(self._extract_import_info(node))
            
            return {
                'file_path': str(self.file_path),
                'language': 'python',
                'classes': [self._class_to_dict(c) for c in classes],
                'functions': [self._function_to_dict(f) for f in functions],
                'imports': [self._import_to_dict(i) for i in imports],
                'ast_used': True
            }
            
        except SyntaxError as e:
            logger.warning(f"Syntax error in Python file: {e}")
            return self.analyze_with_regex()
    
    def _is_nested_function(self, node: ast.FunctionDef, tree: ast.Module) -> bool:
        """関数がネストされているか確認"""
        for cls in ast.walk(tree):
            if isinstance(cls, ast.ClassDef):
                for item in cls.body:
                    if item == node:
                        return True
        return False
    
    def _extract_class_info(self, node: ast.ClassDef) -> ClassInfo:
        """ASTノードからクラス情報を抽出"""
        methods = []
        attributes = []
        
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(item.name)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)
            elif isinstance(item, ast.AnnAssign):
                if isinstance(item.target, ast.Name):
                    attributes.append(item.target.id)
        
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_classes.append(f"{base.value.id}.{base.attr}" if isinstance(base.value, ast.Name) else base.attr)
        
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(dec.attr)
        
        return ClassInfo(
            name=node.name,
            type='class',
            file_path=str(self.file_path),
            line_number=node.lineno,
            methods=methods,
            attributes=attributes,
            base_classes=base_classes,
            decorators=decorators
        )
    
    def _extract_function_info(self, node) -> FunctionInfo:
        """ASTノードから関数情報を抽出"""
        params = []
        for arg in node.args.args:
            params.append(arg.arg)
        
        # 戻り値の型ヒントを取得
        return_type = None
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return_type = node.returns.id
            elif isinstance(node.returns, ast.Constant):
                return_type = str(node.returns.value)
        
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(dec.attr)
        
        return FunctionInfo(
            name=node.name,
            type='function',
            file_path=str(self.file_path),
            line_number=node.lineno,
            parameters=params,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            return_type=return_type,
            decorators=decorators
        )
    
    def _extract_import_info(self, node) -> ImportInfo:
        """ASTノードからインポート情報を抽出"""
        if isinstance(node, ast.Import):
            module = node.names[0].name if node.names else ''
            imported_names = [alias.name for alias in node.names]
        else:  # ImportFrom
            module = node.module or ''
            imported_names = [alias.name for alias in node.names] if node.names else ['*']
        
        return ImportInfo(
            name=module,
            type='import',
            file_path=str(self.file_path),
            line_number=node.lineno,
            module=module,
            imported_names=imported_names,
            is_from_import=isinstance(node, ast.ImportFrom)
        )
    
    def analyze_with_regex(self) -> Dict[str, Any]:
        """正規表現によるフォールバック解析"""
        classes = []
        functions = []
        imports = []
        
        # 安全な正規表現パターンを使用
        for match in SafeRegexPatterns.safe_search('python_class', self.content):
            classes.append({
                'name': match.group(1),
                'line_number': self.content[:match.start()].count('\n') + 1,
                'methods': [],
                'attributes': [],
                'base_classes': [],
                'decorators': []
            })
        
        for match in SafeRegexPatterns.safe_search('python_function', self.content):
            functions.append({
                'name': match.group(1),
                'line_number': self.content[:match.start()].count('\n') + 1,
                'parameters': [],
                'is_async': 'async' in self.content[max(0, match.start()-10):match.start()],
                'return_type': None,
                'decorators': []
            })
        
        for match in SafeRegexPatterns.safe_search('python_import', self.content):
            imports.append({
                'module': match.group(1),
                'line_number': self.content[:match.start()].count('\n') + 1,
                'imported_names': [],
                'is_from_import': 'from' in self.content[max(0, match.start()-20):match.start()]
            })
        
        return {
            'file_path': str(self.file_path),
            'language': 'python',
            'classes': classes,
            'functions': functions,
            'imports': imports,
            'ast_used': False
        }


class IntegratedJavaScriptAnalyzer(IntegratedLanguageAnalyzer):
    """JavaScript/TypeScript用統合アナライザー"""
    
    def get_language_name(self) -> str:
        return 'javascript'
    
    def supports_ast_parsing(self) -> bool:
        # esprimaやbabel-parserが利用可能な場合はTrue
        try:
            import esprima
            return True
        except ImportError:
            return False
    
    def analyze_with_ast(self) -> Dict[str, Any]:
        """JavaScript ASTを使用した解析"""
        try:
            import esprima
            
            # ES6モジュール構文をサポート
            tree = esprima.parseModule(self.content, {'loc': True, 'range': True})
            
            classes = []
            functions = []
            imports = []
            
            # treeオブジェクトを辞書に変換
            tree_dict = tree.toDict() if hasattr(tree, 'toDict') else tree
            
            # ASTを再帰的に探索
            def visit_node(node, parent=None):
                if not isinstance(node, dict):
                    return
                
                node_type = node.get('type')
                
                if node_type == 'ClassDeclaration':
                    classes.append(self._extract_js_class_info(node))
                elif node_type == 'FunctionDeclaration':
                    functions.append(self._extract_js_function_info(node))
                elif node_type == 'ImportDeclaration':
                    imports.append(self._extract_js_import_info(node))
                elif node_type == 'VariableDeclaration':
                    # Arrow functionsをチェック
                    for decl in node.get('declarations', []):
                        init = decl.get('init', {})
                        if isinstance(init, dict) and init.get('type') == 'ArrowFunctionExpression':
                            functions.append(self._extract_js_arrow_function(decl))
                
                # 子ノードを探索
                for key, value in node.items():
                    if isinstance(value, dict):
                        visit_node(value, node)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                visit_node(item, node)
            
            visit_node(tree_dict)
            
            return {
                'file_path': str(self.file_path),
                'language': 'javascript',
                'classes': [self._class_to_dict(c) for c in classes],
                'functions': [self._function_to_dict(f) for f in functions],
                'imports': [self._import_to_dict(i) for i in imports],
                'ast_used': True
            }
            
        except Exception as e:
            logger.warning(f"JavaScript AST parsing failed: {e}")
            return self.analyze_with_regex()
    
    def _extract_js_class_info(self, node: dict) -> ClassInfo:
        """JavaScriptクラス情報を抽出"""
        class_name = node.get('id', {}).get('name', 'Anonymous')
        super_class = node.get('superClass', {}).get('name') if node.get('superClass') else None
        
        methods = []
        attributes = []
        
        for item in node.get('body', {}).get('body', []):
            if item.get('type') == 'MethodDefinition':
                methods.append(item.get('key', {}).get('name', ''))
            elif item.get('type') == 'PropertyDefinition':
                attributes.append(item.get('key', {}).get('name', ''))
        
        return ClassInfo(
            name=class_name,
            type='class',
            file_path=str(self.file_path),
            line_number=node.get('loc', {}).get('start', {}).get('line', 0),
            methods=methods,
            attributes=attributes,
            base_classes=[super_class] if super_class else [],
            decorators=[]
        )
    
    def _extract_js_function_info(self, node: dict) -> FunctionInfo:
        """JavaScript関数情報を抽出"""
        func_name = node.get('id', {}).get('name', 'Anonymous')
        params = [p.get('name', '') for p in node.get('params', [])]
        is_async = node.get('async', False)
        
        return FunctionInfo(
            name=func_name,
            type='function',
            file_path=str(self.file_path),
            line_number=node.get('loc', {}).get('start', {}).get('line', 0),
            parameters=params,
            is_async=is_async,
            return_type=None,
            decorators=[]
        )
    
    def _extract_js_arrow_function(self, node: dict) -> FunctionInfo:
        """JavaScript Arrow関数情報を抽出"""
        func_name = node.get('id', {}).get('name', 'Anonymous')
        init_node = node.get('init', {})
        params = [p.get('name', '') for p in init_node.get('params', [])]
        is_async = init_node.get('async', False)
        
        return FunctionInfo(
            name=func_name,
            type='arrow_function',
            file_path=str(self.file_path),
            line_number=node.get('loc', {}).get('start', {}).get('line', 0),
            parameters=params,
            is_async=is_async,
            return_type=None,
            decorators=[]
        )
    
    def _extract_js_import_info(self, node: dict) -> ImportInfo:
        """JavaScriptインポート情報を抽出"""
        source = node.get('source', {}).get('value', '')
        specifiers = node.get('specifiers', [])
        
        imported_names = []
        for spec in specifiers:
            if spec.get('type') == 'ImportDefaultSpecifier':
                imported_names.append(spec.get('local', {}).get('name', 'default'))
            elif spec.get('type') == 'ImportSpecifier':
                imported_names.append(spec.get('imported', {}).get('name', ''))
            elif spec.get('type') == 'ImportNamespaceSpecifier':
                imported_names.append(f"* as {spec.get('local', {}).get('name', '')}")
        
        return ImportInfo(
            name=source,
            type='import',
            file_path=str(self.file_path),
            line_number=node.get('loc', {}).get('start', {}).get('line', 0),
            module=source,
            imported_names=imported_names,
            is_from_import=True
        )
    
    def analyze_with_regex(self) -> Dict[str, Any]:
        """正規表現ベースの解析"""
        from adg.core.multi_language_analyzer import JavaScriptAnalyzer
        
        # 既存のJavaScriptAnalyzerを使用
        analyzer = JavaScriptAnalyzer(str(self.file_path))
        result = analyzer.analyze()
        result['ast_used'] = False
        return result


class IntegratedUniversalAnalyzer:
    """
    統合型汎用アナライザー
    セキュリティ機能とAST解析を統合
    """
    
    # 言語ごとの専用アナライザー
    LANGUAGE_ANALYZERS = {
        '.py': IntegratedPythonAnalyzer,
        '.js': IntegratedJavaScriptAnalyzer,
        '.jsx': IntegratedJavaScriptAnalyzer,
        '.ts': IntegratedJavaScriptAnalyzer,
        '.tsx': IntegratedJavaScriptAnalyzer,
    }
    
    def __init__(self, file_path: str, base_path: Optional[Path] = None):
        self.file_path = Path(file_path)
        self.base_path = base_path or Path.cwd()
        self.extension = self.file_path.suffix.lower()
        
        # セキュリティチェック
        try:
            self.file_path = PathValidator.validate_path(self.base_path, self.file_path)
        except SecurityError as e:
            raise ValueError(f"Security check failed: {e}")
        
        self.analyzer = self._get_analyzer()
    
    def _get_analyzer(self) -> Optional[IntegratedLanguageAnalyzer]:
        """適切な言語アナライザーを取得"""
        # まず既存の専用アナライザーをチェック
        analyzer_class = self.LANGUAGE_ANALYZERS.get(self.extension)
        if analyzer_class:
            return analyzer_class(str(self.file_path), self.base_path)
        
        # 新しいAST アナライザーを試す
        try:
            from adg.core.ast_analyzers import (
                TreeSitterAnalyzer,
                JavaLangAnalyzer,
                DelphiAnalyzer,
                get_ast_analyzer_for_file
            )
            
            # AST アナライザーの自動選択
            ast_analyzer = get_ast_analyzer_for_file(str(self.file_path))
            if ast_analyzer:
                return self._wrap_ast_analyzer(ast_analyzer)
                
        except ImportError as e:
            logger.warning(f"AST analyzers not available: {e}")
        
        # 既存のアナライザーにフォールバック
        from adg.core.multi_language_analyzer import (
            JavaAnalyzer, GoAnalyzer, GenericAnalyzer
        )
        from adg.core.language_parsers import ADDITIONAL_ANALYZERS
        
        # Java, Go
        if self.extension == '.java':
            return self._create_fallback_analyzer(JavaAnalyzer)
        elif self.extension == '.go':
            return self._create_fallback_analyzer(GoAnalyzer)
        
        # 追加言語（C++, Rust, PHP, Ruby）
        fallback_class = ADDITIONAL_ANALYZERS.get(self.extension)
        if fallback_class:
            return self._create_fallback_analyzer(fallback_class)
        
        # 汎用アナライザー
        return self._create_fallback_analyzer(GenericAnalyzer)
    
    def _wrap_ast_analyzer(self, ast_analyzer):
        """AST アナライザーをIntegratedLanguageAnalyzerにラップ"""
        class ASTAnalyzerWrapper(IntegratedLanguageAnalyzer):
            def __init__(self, file_path: str, base_path: Optional[Path] = None):
                super().__init__(file_path, base_path)
                self.ast_analyzer = ast_analyzer
            
            def get_language_name(self) -> str:
                return self.ast_analyzer.get_language_name()
            
            def supports_ast_parsing(self) -> bool:
                return True
            
            def analyze_with_ast(self) -> Dict[str, Any]:
                result = self.ast_analyzer.analyze()
                # AST解析が成功したことをマーク
                result['ast_used'] = True
                return result
            
            def analyze_with_regex(self) -> Dict[str, Any]:
                # AST解析が失敗した場合のフォールバック
                result = super().analyze()
                result['ast_used'] = False
                return result
        
        return ASTAnalyzerWrapper(str(self.file_path), self.base_path)
    
    def _create_fallback_analyzer(self, analyzer_class):
        """既存アナライザーをラップ"""
        class FallbackAnalyzer(IntegratedLanguageAnalyzer):
            def __init__(self, file_path: str, base_path: Optional[Path] = None):
                super().__init__(file_path, base_path)
                self.wrapped_analyzer = analyzer_class(file_path)
            
            def get_language_name(self) -> str:
                return self.wrapped_analyzer.analyze().get('language', 'unknown')
            
            def analyze(self) -> Dict[str, Any]:
                return self.wrapped_analyzer.analyze()
        
        return FallbackAnalyzer(str(self.file_path), self.base_path)
    
    def analyze(self) -> AnalysisResult:
        """ファイルを解析"""
        if self.analyzer:
            return self.analyzer.analyze_with_recovery()
        else:
            return AnalysisResult(
                success=False,
                file_path=str(self.file_path),
                language='unknown',
                errors=[f'Unsupported file type: {self.extension}']
            )


class IntegratedProjectAnalyzer:
    """統合型プロジェクト解析"""
    
    def __init__(self, project_path: str, cache_enabled: bool = True):
        """
        初期化
        
        Args:
            project_path: プロジェクトパス
            cache_enabled: キャッシュを有効にするか
        """
        self.project_path = Path(project_path).resolve()
        self.cache_enabled = cache_enabled
        
        if cache_enabled:
            cache_dir = self.project_path / '.adg_cache'
            self.cache = AnalysisCache(cache_dir)
        else:
            self.cache = None
        
        self.files_processed = 0
        self.errors = []
    
    def analyze_project(self) -> Dict[str, Any]:
        """
        プロジェクト全体を安全に解析
        
        Returns:
            解析結果
        """
        from datetime import datetime
        
        results = {
            'project': str(self.project_path),
            'timestamp': datetime.now().isoformat(),
            'files': {},
            'languages': {},
            'summary': {
                'total_files': 0,
                'successful': 0,
                'failed': 0,
                'cached': 0,
                'ast_used': 0,
                'regex_used': 0,
                'languages_detected': set()
            },
            'errors': []
        }
        
        # ソースファイルを取得
        source_files = self._get_safe_source_files()
        
        for file_path in source_files:
            if self.files_processed >= SecurityConfig.MAX_FILES_TO_PROCESS:
                results['errors'].append("File limit reached")
                break
            
            try:
                # キャッシュチェック
                if self.cache:
                    cached = self.cache.get_cached_analysis(file_path)
                    if cached:
                        results['files'][str(file_path)] = cached
                        results['summary']['cached'] += 1
                        self._update_language_stats(results, cached)
                        continue
                
                # 解析実行
                analyzer = IntegratedUniversalAnalyzer(str(file_path), self.project_path)
                result = analyzer.analyze()
                
                if result.success:
                    analysis_data = result.to_dict()
                    results['files'][str(file_path)] = analysis_data
                    results['summary']['successful'] += 1
                    
                    # AST使用状況を記録
                    if analysis_data.get('data', {}).get('ast_used'):
                        results['summary']['ast_used'] += 1
                    else:
                        results['summary']['regex_used'] += 1
                    
                    # 言語統計を更新
                    self._update_language_stats(results, analysis_data)
                    
                    # キャッシュに保存
                    if self.cache:
                        self.cache.cache_analysis(file_path, analysis_data)
                else:
                    results['files'][str(file_path)] = result.to_dict()
                    results['summary']['failed'] += 1
                    results['errors'].extend(result.errors)
                
                self.files_processed += 1
                results['summary']['total_files'] += 1
                
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
                results['errors'].append(f"{file_path}: {str(e)[:100]}")
                results['summary']['failed'] += 1
        
        # Set to list for JSON serialization
        results['summary']['languages_detected'] = list(results['summary']['languages_detected'])
        
        return results
    
    def _update_language_stats(self, results: Dict, analysis: Dict):
        """言語統計を更新"""
        language = analysis.get('language', 'unknown')
        results['summary']['languages_detected'].add(language)
        
        if language not in results['languages']:
            results['languages'][language] = {
                'files': 0,
                'classes': 0,
                'functions': 0,
                'ast_used': 0,
                'regex_used': 0
            }
        
        results['languages'][language]['files'] += 1
        
        data = analysis.get('data', {})
        if data:
            results['languages'][language]['classes'] += len(data.get('classes', []))
            results['languages'][language]['functions'] += len(data.get('functions', []))
            
            if data.get('ast_used'):
                results['languages'][language]['ast_used'] += 1
            else:
                results['languages'][language]['regex_used'] += 1
    
    def _get_safe_source_files(self) -> List[Path]:
        """安全にソースファイルを取得"""
        source_files = []
        exclude_dirs = {
            '__pycache__', '.git', '.venv', 'venv', 'node_modules',
            '.pytest_cache', '.mypy_cache', 'dist', 'build',
            'target', 'out', 'bin', 'obj', '.idea', '.vscode'
        }
        
        # すべての対応拡張子
        all_extensions = set(SecurityConfig.ALLOWED_EXTENSIONS)
        all_extensions.update({
            '.jsx', '.ts', '.tsx', '.pas', '.dpr',
            '.cs', '.vb', '.kt', '.scala', '.m', '.mm',
            '.r', '.lua', '.pl', '.sh', '.bat', '.ps1'
        })
        
        for ext in all_extensions:
            for file_path in self.project_path.rglob(f"*{ext}"):
                # 除外ディレクトリチェック
                if any(excluded in str(file_path) for excluded in exclude_dirs):
                    continue
                
                # パス検証
                try:
                    safe_path = PathValidator.validate_path(self.project_path, file_path)
                    source_files.append(safe_path)
                except SecurityError:
                    continue
        
        return source_files
    
    def generate_diagrams(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析結果から図を生成
        """
        from adg.generators.mermaid_refactored import MermaidGeneratorRefactored
        from adg.generators.drawio_from_mermaid import MermaidBasedDrawIOGenerator
        
        output_dir = self.project_path / 'adg_output'
        output_dir.mkdir(exist_ok=True)
        
        # 各言語ごとに図を生成
        results = {}
        
        for language, stats in analysis_result['languages'].items():
            if stats['classes'] > 0 or stats['functions'] > 0:
                logger.info(f"Generating diagrams for {language} files...")
                
                # 言語固有の解析結果を抽出
                language_analysis = {
                    'files': {
                        path: data for path, data in analysis_result['files'].items()
                        if data.get('language') == language
                    },
                    'summary': stats
                }
                
                try:
                    # Mermaid図生成
                    mermaid_gen = MermaidGeneratorRefactored(language_analysis)
                    mermaid_result = mermaid_gen.generate('class', output_dir)
                    
                    # DrawIO図生成
                    if mermaid_result.success:
                        drawio_gen = MermaidBasedDrawIOGenerator(language_analysis)
                        drawio_results = drawio_gen.generate_all(output_dir)
                        
                        results[language] = {
                            'mermaid': mermaid_result.file_path,
                            'drawio': [r.file_path for r in drawio_results if r.success]
                        }
                except Exception as e:
                    logger.error(f"Failed to generate diagrams for {language}: {e}")
        
        return results


# CLIコマンド実装
def main():
    """統合アナライザーのメインエントリーポイント"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Integrated Secure Multi-language Code Analyzer'
    )
    parser.add_argument(
        'path',
        help='Path to analyze',
        default='.',
        nargs='?'
    )
    parser.add_argument(
        '--output',
        help='Output directory',
        default='adg_output'
    )
    parser.add_argument(
        '--format',
        choices=['mermaid', 'drawio', 'all'],
        default='all',
        help='Output format'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Disable caching'
    )
    parser.add_argument(
        '--no-diagrams',
        action='store_true',
        help='Skip diagram generation'
    )
    
    args = parser.parse_args()
    
    # 統合アナライザーを実行
    analyzer = IntegratedProjectAnalyzer(args.path, cache_enabled=not args.no_cache)
    
    print("[INFO] Analyzing project with integrated analyzer...")
    analysis = analyzer.analyze_project()
    
    print(f"[STATS] Found {analysis['summary']['total_files']} files")
    print(f"[LANG] Languages: {', '.join(analysis['summary']['languages_detected'])}")
    print(f"[OK] Successful: {analysis['summary']['successful']}")
    print(f"[FAIL] Failed: {analysis['summary']['failed']}")
    print(f"[CACHE] Cached: {analysis['summary']['cached']}")
    print(f"[AST] AST used: {analysis['summary']['ast_used']}")
    print(f"[REGEX] Regex used: {analysis['summary']['regex_used']}")
    
    # 言語別の統計
    print("\n[STATS] Language Statistics:")
    for lang, stats in analysis['languages'].items():
        print(f"  {lang}:")
        print(f"    Files: {stats['files']}")
        print(f"    Classes: {stats['classes']}")
        print(f"    Functions: {stats['functions']}")
        print(f"    AST: {stats['ast_used']}, Regex: {stats['regex_used']}")
    
    # 図の生成
    if not args.no_diagrams and args.format in ['mermaid', 'drawio', 'all']:
        print("\n[DIAGRAM] Generating diagrams...")
        diagrams = analyzer.generate_diagrams(analysis)
        
        for language, paths in diagrams.items():
            print(f"  [OK] {language}: {len(paths.get('drawio', []))} diagrams")
    
    # 結果をJSON出力
    output_file = Path(args.output) / 'integrated_analysis.json'
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SAVE] Results saved to: {output_file}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())