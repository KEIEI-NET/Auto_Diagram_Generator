"""
コード解析エンジン
様々な言語のコードを解析して構造を抽出
"""

import ast
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class CodeElement:
    """コード要素の基本クラス"""
    name: str
    type: str
    file_path: str
    line_number: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClassInfo(CodeElement):
    """クラス情報"""
    methods: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)


@dataclass
class FunctionInfo(CodeElement):
    """関数/メソッド情報"""
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False


@dataclass
class ImportInfo(CodeElement):
    """インポート情報"""
    module: str = ""
    imported_names: List[str] = field(default_factory=list)
    is_from_import: bool = False


class CodeAnalyzer:
    """コード解析の基底クラス"""
    
    def __init__(self, file_path: str):
        # セキュリティ: パスの検証を追加
        from adg.utils.security import validate_path
        self.file_path = validate_path(file_path)
        self.content = self._read_file()
        self.elements: List[CodeElement] = []
        
    def _read_file(self) -> str:
        """ファイル内容を読み込む"""
        try:
            if not self.file_path.exists():
                logger.error(f"File not found: {self.file_path}")
                raise FileNotFoundError(f"File not found: {self.file_path}")
            
            if not self.file_path.is_file():
                logger.error(f"Path is not a file: {self.file_path}")
                raise ValueError(f"Path is not a file: {self.file_path}")
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    logger.warning(f"File is empty: {self.file_path}")
                return content
        except (UnicodeDecodeError, PermissionError) as e:
            logger.error(f"Failed to read file {self.file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error reading file {self.file_path}: {e}")
            raise
    
    def analyze(self) -> Dict[str, Any]:
        """コードを解析して構造を抽出"""
        raise NotImplementedError("Subclasses must implement analyze method")


class PythonAnalyzer(CodeAnalyzer):
    """Python コード解析器"""
    
    def analyze(self) -> Dict[str, Any]:
        """Pythonコードを解析"""
        try:
            if not self.content.strip():
                logger.warning(f"Empty file: {self.file_path}")
                return {"classes": [], "functions": [], "imports": [], "variables": []}
            
            tree = ast.parse(self.content, filename=str(self.file_path))
            return self._extract_structure(tree)
        except SyntaxError as e:
            logger.error(f"Syntax error in {self.file_path}: {e}")
            return {"error": str(e), "classes": [], "functions": [], "imports": [], "variables": []}
        except Exception as e:
            logger.error(f"Unexpected error analyzing {self.file_path}: {e}")
            return {"error": str(e), "classes": [], "functions": [], "imports": [], "variables": []}
    
    def _extract_structure(self, tree: ast.AST) -> Dict[str, Any]:
        """AST から構造を抽出"""
        structure = {
            "classes": [],
            "functions": [],
            "imports": [],
            "variables": [],
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                structure["classes"].append(self._extract_class_info(node))
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                structure["functions"].append(self._extract_function_info(node))
            elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                structure["imports"].append(self._extract_import_info(node))
        
        return structure
    
    def _extract_class_info(self, node: ast.ClassDef) -> ClassInfo:
        """クラス情報を抽出"""
        methods = []
        attributes = []
        
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(item.name)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)
        
        base_classes = [
            base.id if isinstance(base, ast.Name) else ast.unparse(base)
            for base in node.bases
        ]
        
        decorators = [
            dec.id if isinstance(dec, ast.Name) else ast.unparse(dec)
            for dec in node.decorator_list
        ]
        
        return ClassInfo(
            name=node.name,
            type="class",
            file_path=str(self.file_path),
            line_number=node.lineno,
            methods=methods,
            attributes=attributes,
            base_classes=base_classes,
            decorators=decorators
        )
    
    def _extract_function_info(self, node) -> FunctionInfo:
        """関数/メソッド情報を抽出"""
        parameters = [arg.arg for arg in node.args.args]
        
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns)
        
        decorators = [
            dec.id if isinstance(dec, ast.Name) else ast.unparse(dec)
            for dec in node.decorator_list
        ]
        
        return FunctionInfo(
            name=node.name,
            type="function",
            file_path=str(self.file_path),
            line_number=node.lineno,
            parameters=parameters,
            return_type=return_type,
            decorators=decorators,
            is_async=isinstance(node, ast.AsyncFunctionDef)
        )
    
    def _extract_import_info(self, node) -> ImportInfo:
        """インポート情報を抽出"""
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
            return ImportInfo(
                name="import",
                type="import",
                file_path=str(self.file_path),
                line_number=node.lineno,
                module=names[0] if names else "",
                imported_names=names,
                is_from_import=False
            )
        else:  # ast.ImportFrom
            module = node.module or ""
            names = [alias.name for alias in node.names]
            return ImportInfo(
                name="import",
                type="import",
                file_path=str(self.file_path),
                line_number=node.lineno,
                module=module,
                imported_names=names,
                is_from_import=True
            )


class ProjectAnalyzer:
    """プロジェクト全体の解析"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.analyzers = {
            '.py': PythonAnalyzer,
            # 今後追加: '.js': JavaScriptAnalyzer,
            # 今後追加: '.java': JavaAnalyzer,
        }
    
    def analyze(self) -> Dict[str, Any]:
        """プロジェクト全体を解析"""
        results = {
            "project_path": str(self.project_path),
            "files": {},
            "summary": {
                "total_files": 0,
                "total_classes": 0,
                "total_functions": 0,
                "errors": []  # エラー収集用
            }
        }
        
        for file_path in self._get_source_files():
            try:
                analyzer = self._get_analyzer(file_path)
                if analyzer:
                    analysis = analyzer.analyze()
                    if analysis:  # 解析結果が空でない場合のみ処理
                        results["files"][str(file_path)] = analysis
                        
                        # サマリー更新（型安全性を考慮）
                        results["summary"]["total_files"] += 1
                        
                        classes = analysis.get("classes", [])
                        if isinstance(classes, list):
                            results["summary"]["total_classes"] += len(classes)
                        
                        functions = analysis.get("functions", [])
                        if isinstance(functions, list):
                            results["summary"]["total_functions"] += len(functions)
                    else:
                        logger.warning(f"Empty analysis result for {file_path}")
            except FileNotFoundError as e:
                logger.warning(f"File not found: {file_path}: {e}")
                results["summary"]["errors"].append(f"File not found: {file_path}")
                continue
            except PermissionError as e:
                logger.warning(f"Permission denied: {file_path}: {e}")
                results["summary"]["errors"].append(f"Permission denied: {file_path}")
                continue
            except UnicodeDecodeError as e:
                logger.warning(f"Encoding error in file {file_path}: {e}")
                results["summary"]["errors"].append(f"Encoding error: {file_path}")
                continue
            except SyntaxError as e:
                logger.warning(f"Syntax error in file {file_path}: {e}")
                results["summary"]["errors"].append(f"Syntax error: {file_path}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error analyzing {file_path}: {type(e).__name__}: {e}")
                results["summary"]["errors"].append(f"Analysis failed: {file_path}: {type(e).__name__}")
                continue
        
        return results
    
    def _get_source_files(self) -> List[Path]:
        """ソースファイルを取得"""
        source_files = []
        # 除外パターンを定義
        exclude_patterns = {
            '__pycache__', '.git', '.venv', 'venv', 'node_modules',
            '.pytest_cache', '.mypy_cache', 'dist', 'build'
        }
        
        for ext, analyzer_class in self.analyzers.items():
            for file_path in self.project_path.rglob(f"*{ext}"):
                # 除外パターンに該当するかチェック
                if any(pattern in str(file_path) for pattern in exclude_patterns):
                    continue
                # ファイルサイズチェック（1MB以上は除外）
                try:
                    if file_path.stat().st_size > 1024 * 1024:
                        logger.warning(f"Skipping large file: {file_path}")
                        continue
                except OSError:
                    continue
                source_files.append(file_path)
        
        return source_files
    
    def _get_analyzer(self, file_path: Path) -> Optional[CodeAnalyzer]:
        """ファイル拡張子に応じたアナライザーを取得"""
        try:
            ext = file_path.suffix
            analyzer_class = self.analyzers.get(ext)
            if analyzer_class:
                return analyzer_class(str(file_path))
            return None
        except Exception as e:
            logger.error(f"Failed to create analyzer for {file_path}: {e}")
            return None