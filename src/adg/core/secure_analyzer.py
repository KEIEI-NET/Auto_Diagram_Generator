"""
セキュアな多言語コード解析モジュール
セキュリティ修正版の実装
"""

import os
import re
import hashlib
import pickle
import signal
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Type, Protocol
from loguru import logger
import json

from adg.core.analyzer import CodeElement, ClassInfo, FunctionInfo, ImportInfo


# セキュリティ設定
class SecurityConfig:
    """セキュリティ設定"""
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_MEMORY_USAGE = 100 * 1024 * 1024  # 100MB
    REGEX_TIMEOUT_SECONDS = 5
    MAX_FILES_TO_PROCESS = 10000
    DANGEROUS_PATHS = [
        '..', '../', '..\\',
        '/etc/', '/proc/', '/sys/', 
        'C:\\Windows\\', 'C:\\System32\\',
        '/dev/', '/var/log/', '~/'
    ]
    ALLOWED_EXTENSIONS = {
        '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go',
        '.cpp', '.cc', '.cxx', '.c', '.h', '.hpp',
        '.rs', '.swift', '.php', '.rb', '.cs', '.kt'
    }


class SecurityError(Exception):
    """セキュリティエラー"""
    pass


class PathValidator:
    """パス検証ユーティリティ"""
    
    @staticmethod
    def validate_path(base_path: Path, target_path: Path) -> Path:
        """
        パストラバーサル攻撃を防ぐパス検証
        
        Args:
            base_path: ベースディレクトリ
            target_path: 検証するパス
            
        Returns:
            検証済みの安全なパス
            
        Raises:
            SecurityError: 不正なパスの場合
        """
        try:
            # パスを正規化
            base_resolved = base_path.resolve()
            target_resolved = target_path.resolve()
            
            # 危険なパターンをチェック
            target_str = str(target_resolved)
            for dangerous in SecurityConfig.DANGEROUS_PATHS:
                if dangerous in target_str:
                    raise SecurityError(f"Dangerous path pattern detected: {dangerous}")
            
            # ベースディレクトリ内にあることを確認
            if not str(target_resolved).startswith(str(base_resolved)):
                raise SecurityError(f"Path traversal attempt detected: {target_path}")
            
            return target_resolved
            
        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            raise SecurityError(f"Path validation failed: {e}")


class SecureFileHandler:
    """セキュアなファイル処理"""
    
    @staticmethod
    def safe_read_file(file_path: Path, encoding='utf-8') -> Optional[str]:
        """
        安全にファイルを読み込む
        
        Args:
            file_path: ファイルパス
            encoding: エンコーディング
            
        Returns:
            ファイル内容またはNone
        """
        try:
            # ファイル存在チェック
            if not file_path.exists() or not file_path.is_file():
                logger.warning(f"File not found or not a file: {file_path}")
                return None
            
            # ファイルサイズチェック
            file_size = file_path.stat().st_size
            if file_size > SecurityConfig.MAX_FILE_SIZE:
                logger.warning(f"File too large ({file_size} bytes): {file_path}")
                return None
            
            # 複数エンコーディングを試行
            encodings = [encoding, 'utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            
            for enc in encodings:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            
            logger.error(f"Unable to decode file: {file_path}")
            return None
            
        except PermissionError:
            logger.error(f"Permission denied: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return None


@contextmanager
def timeout_regex(timeout_seconds=SecurityConfig.REGEX_TIMEOUT_SECONDS):
    """
    正規表現のタイムアウト制御
    ReDoS攻撃を防ぐ
    """
    import threading
    
    class TimeoutException(Exception):
        pass
    
    def timeout_handler():
        raise TimeoutException("Regex operation timed out")
    
    timer = threading.Timer(timeout_seconds, timeout_handler)
    timer.start()
    
    try:
        yield
    finally:
        timer.cancel()


class SafeRegexPatterns:
    """安全な正規表現パターン"""
    
    # エスケープされた安全なパターン
    SAFE_PATTERNS = {
        'python_class': r'^class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\([^)]*\))?\s*:',
        'python_function': r'^(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
        'python_import': r'^(?:from\s+[\w.]+\s+)?import\s+([\w, ]+)',
        
        'js_class': r'(?:^|\s)class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)',
        'js_function': r'(?:^|\s)function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(',
        'js_arrow': r'(?:const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*(?:\([^)]*\)|[^=]+)\s*=>',
        
        'java_class': r'(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'java_method': r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
    }
    
    @classmethod
    def get_pattern(cls, pattern_name: str) -> Optional[re.Pattern]:
        """コンパイル済みパターンを取得"""
        pattern_str = cls.SAFE_PATTERNS.get(pattern_name)
        if pattern_str:
            return re.compile(pattern_str, re.MULTILINE)
        return None
    
    @classmethod
    def safe_search(cls, pattern_name: str, text: str, max_text_length: int = 100000) -> List[re.Match]:
        """安全な正規表現検索"""
        # テキストサイズ制限
        if len(text) > max_text_length:
            text = text[:max_text_length]
        
        pattern = cls.get_pattern(pattern_name)
        if not pattern:
            return []
        
        try:
            with timeout_regex():
                return list(pattern.finditer(text))
        except Exception as e:
            logger.warning(f"Regex search failed for {pattern_name}: {e}")
            return []


@dataclass
class AnalysisResult:
    """解析結果"""
    success: bool
    file_path: str
    language: str
    data: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    partial_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'success': self.success,
            'file_path': self.file_path,
            'language': self.language,
            'data': self.data,
            'errors': self.errors,
            'warnings': self.warnings,
            'partial_data': self.partial_data
        }


class SerializationMixin:
    """シリアライゼーション共通処理"""
    
    def _class_to_dict(self, cls: ClassInfo) -> Dict[str, Any]:
        """クラス情報を辞書に変換"""
        return {
            'name': cls.name,
            'type': getattr(cls, 'type', 'class'),
            'methods': cls.methods,
            'attributes': cls.attributes,
            'base_classes': cls.base_classes,
            'decorators': getattr(cls, 'decorators', []),
            'line_number': cls.line_number
        }
    
    def _function_to_dict(self, func: FunctionInfo) -> Dict[str, Any]:
        """関数情報を辞書に変換"""
        return {
            'name': func.name,
            'parameters': func.parameters,
            'return_type': getattr(func, 'return_type', None),
            'is_async': getattr(func, 'is_async', False),
            'decorators': getattr(func, 'decorators', []),
            'line_number': func.line_number
        }
    
    def _import_to_dict(self, imp: ImportInfo) -> Dict[str, Any]:
        """インポート情報を辞書に変換"""
        return {
            'module': imp.module,
            'imported_names': imp.imported_names,
            'is_from_import': imp.is_from_import,
            'line_number': imp.line_number
        }


class SecureLanguageAnalyzer(ABC, SerializationMixin):
    """セキュアな言語アナライザー基底クラス"""
    
    def __init__(self, file_path: str, base_path: Optional[Path] = None):
        """
        初期化
        
        Args:
            file_path: 解析するファイルパス
            base_path: ベースディレクトリ（セキュリティチェック用）
        """
        # パス検証
        self.file_path = Path(file_path)
        if base_path:
            self.file_path = PathValidator.validate_path(base_path, self.file_path)
        
        # ファイル内容を安全に読み込み
        self.content = SecureFileHandler.safe_read_file(self.file_path)
        if not self.content:
            self.content = ""
        
        self.elements: List[CodeElement] = []
    
    def analyze_with_recovery(self) -> AnalysisResult:
        """
        エラー回復機能付き解析
        
        Returns:
            AnalysisResult: 解析結果（部分的な結果を含む）
        """
        result = AnalysisResult(
            success=True,
            file_path=str(self.file_path),
            language=self.get_language_name()
        )
        
        try:
            # 通常の解析
            result.data = self.analyze()
            
        except SyntaxError as e:
            result.success = False
            result.errors.append(f"Syntax error: {e}")
            # 部分的な解析を試行
            result.partial_data = self.extract_basic_structure()
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Analysis failed: {type(e).__name__}: {str(e)[:100]}")
            # 最小限のメタデータを提供
            result.partial_data = {
                'file_path': str(self.file_path),
                'language': self.get_language_name(),
                'metadata': self.extract_metadata()
            }
        
        return result
    
    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """ファイルを解析"""
        pass
    
    @abstractmethod
    def get_language_name(self) -> str:
        """言語名を取得"""
        pass
    
    def extract_basic_structure(self) -> Dict[str, Any]:
        """基本的な構造を抽出（フォールバック用）"""
        lines = self.content.splitlines()
        return {
            'line_count': len(lines),
            'file_size': len(self.content),
            'has_classes': bool(re.search(r'\bclass\b', self.content)),
            'has_functions': bool(re.search(r'\b(function|def|func)\b', self.content)),
            'has_imports': bool(re.search(r'\b(import|require|include|use)\b', self.content))
        }
    
    def extract_metadata(self) -> Dict[str, Any]:
        """メタデータを抽出"""
        return {
            'file_name': self.file_path.name,
            'extension': self.file_path.suffix,
            'size': len(self.content),
            'lines': len(self.content.splitlines()),
            'encoding': 'utf-8'  # デフォルト
        }


class SecurePythonAnalyzer(SecureLanguageAnalyzer):
    """セキュアなPython解析"""
    
    def get_language_name(self) -> str:
        return 'python'
    
    def analyze(self) -> Dict[str, Any]:
        """Python ASTを使用した安全な解析"""
        import ast
        
        try:
            tree = ast.parse(self.content)
            
            classes = []
            functions = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(self._extract_class_info(node))
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    functions.append(self._extract_function_info(node))
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    imports.append(self._extract_import_info(node))
            
            return {
                'file_path': str(self.file_path),
                'language': 'python',
                'classes': [self._class_to_dict(c) for c in classes],
                'functions': [self._function_to_dict(f) for f in functions],
                'imports': [self._import_to_dict(i) for i in imports]
            }
            
        except SyntaxError as e:
            # 構文エラーの場合は正規表現でフォールバック
            return self._regex_fallback_analysis()
    
    def _extract_class_info(self, node: Any) -> ClassInfo:
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
        
        return ClassInfo(
            name=node.name,
            type='class',
            file_path=str(self.file_path),
            line_number=node.lineno,
            methods=methods,
            attributes=attributes,
            base_classes=[base.id for base in node.bases if isinstance(base, ast.Name)],
            decorators=[d.id for d in node.decorator_list if isinstance(d, ast.Name)]
        )
    
    def _extract_function_info(self, node: Any) -> FunctionInfo:
        """ASTノードから関数情報を抽出"""
        params = []
        for arg in node.args.args:
            params.append(arg.arg)
        
        return FunctionInfo(
            name=node.name,
            type='function',
            file_path=str(self.file_path),
            line_number=node.lineno,
            parameters=params,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            return_type=None,  # 型ヒントは省略
            decorators=[d.id for d in node.decorator_list if isinstance(d, ast.Name)]
        )
    
    def _extract_import_info(self, node: Any) -> ImportInfo:
        """ASTノードからインポート情報を抽出"""
        if isinstance(node, ast.Import):
            module = node.names[0].name if node.names else ''
            imported_names = [alias.name for alias in node.names]
        else:  # ImportFrom
            module = node.module or ''
            imported_names = [alias.name for alias in node.names] if node.names else []
        
        return ImportInfo(
            name=module,
            type='import',
            file_path=str(self.file_path),
            line_number=node.lineno,
            module=module,
            imported_names=imported_names,
            is_from_import=isinstance(node, ast.ImportFrom)
        )
    
    def _regex_fallback_analysis(self) -> Dict[str, Any]:
        """正規表現によるフォールバック解析"""
        classes = []
        functions = []
        imports = []
        
        # 安全な正規表現パターンを使用
        for match in SafeRegexPatterns.safe_search('python_class', self.content):
            classes.append({
                'name': match.group(1),
                'line_number': self.content[:match.start()].count('\n') + 1
            })
        
        for match in SafeRegexPatterns.safe_search('python_function', self.content):
            functions.append({
                'name': match.group(1),
                'line_number': self.content[:match.start()].count('\n') + 1
            })
        
        for match in SafeRegexPatterns.safe_search('python_import', self.content):
            imports.append({
                'module': match.group(1),
                'line_number': self.content[:match.start()].count('\n') + 1
            })
        
        return {
            'file_path': str(self.file_path),
            'language': 'python',
            'classes': classes,
            'functions': functions,
            'imports': imports,
            'metadata': {'fallback': True}
        }


class AnalysisCache:
    """解析結果のキャッシュ"""
    
    def __init__(self, cache_dir: Path):
        """
        初期化
        
        Args:
            cache_dir: キャッシュディレクトリ
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(hours=24)
    
    def get_cache_key(self, file_path: Path) -> str:
        """ファイルのキャッシュキーを生成"""
        try:
            stat = file_path.stat()
            content = f"{file_path}:{stat.st_mtime}:{stat.st_size}"
            return hashlib.sha256(content.encode()).hexdigest()
        except Exception:
            return hashlib.sha256(str(file_path).encode()).hexdigest()
    
    def get_cached_analysis(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """キャッシュから解析結果を取得"""
        cache_key = self.get_cache_key(file_path)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    cached = pickle.load(f)
                    if datetime.now() - cached['timestamp'] < self.cache_ttl:
                        return cached['data']
            except Exception as e:
                logger.debug(f"Cache read failed: {e}")
        
        return None
    
    def cache_analysis(self, file_path: Path, analysis: Dict[str, Any]):
        """解析結果をキャッシュ"""
        cache_key = self.get_cache_key(file_path)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump({
                    'timestamp': datetime.now(),
                    'data': analysis
                }, f)
        except Exception as e:
            logger.debug(f"Cache write failed: {e}")


class SecureProjectAnalyzer:
    """セキュアなプロジェクト解析"""
    
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
        results = {
            'project': str(self.project_path),
            'timestamp': datetime.now().isoformat(),
            'files': {},
            'summary': {
                'total_files': 0,
                'successful': 0,
                'failed': 0,
                'cached': 0
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
                        continue
                
                # 解析実行
                analyzer = self._get_analyzer(file_path)
                if analyzer:
                    result = analyzer.analyze_with_recovery()
                    
                    if result.success:
                        results['files'][str(file_path)] = result.to_dict()
                        results['summary']['successful'] += 1
                        
                        # キャッシュに保存
                        if self.cache:
                            self.cache.cache_analysis(file_path, result.to_dict())
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
        
        return results
    
    def _get_safe_source_files(self) -> List[Path]:
        """安全にソースファイルを取得"""
        source_files = []
        exclude_dirs = {
            '__pycache__', '.git', '.venv', 'venv', 'node_modules',
            '.pytest_cache', '.mypy_cache', 'dist', 'build'
        }
        
        for ext in SecurityConfig.ALLOWED_EXTENSIONS:
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
    
    def _get_analyzer(self, file_path: Path) -> Optional[SecureLanguageAnalyzer]:
        """適切なアナライザーを取得"""
        ext = file_path.suffix.lower()
        
        # 現在はPythonのみサポート（今後拡張）
        if ext == '.py':
            return SecurePythonAnalyzer(str(file_path), self.project_path)
        
        return None


# CLIコマンド
def main():
    """メインエントリーポイント"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Secure Auto Diagram Generator'
    )
    parser.add_argument('path', help='Path to analyze', default='.')
    parser.add_argument('--no-cache', action='store_true', help='Disable caching')
    parser.add_argument('--output', help='Output file', default='analysis.json')
    
    args = parser.parse_args()
    
    try:
        analyzer = SecureProjectAnalyzer(args.path, cache_enabled=not args.no_cache)
        results = analyzer.analyze_project()
        
        # 結果を保存
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Analysis complete: {output_path}")
        print(f"  Files: {results['summary']['total_files']}")
        print(f"  Successful: {results['summary']['successful']}")
        print(f"  Failed: {results['summary']['failed']}")
        print(f"  Cached: {results['summary']['cached']}")
        
        if results['errors']:
            print(f"  Errors: {len(results['errors'])}")
        
        return 0
        
    except Exception as e:
        print(f"✗ Analysis failed: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())