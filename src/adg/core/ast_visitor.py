"""
ASTビジターパターンによる効率的なコード解析
"""

import ast
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
from loguru import logger


@dataclass
class SymbolInfo:
    """シンボル情報の基底クラス"""
    name: str
    line_number: int
    end_line_number: Optional[int] = None
    docstring: Optional[str] = None


@dataclass
class ClassInfo(SymbolInfo):
    """クラス情報"""
    methods: List['MethodInfo'] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    is_abstract: bool = False


@dataclass
class MethodInfo(SymbolInfo):
    """メソッド/関数情報"""
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    is_static: bool = False
    is_classmethod: bool = False
    is_property: bool = False
    complexity: int = 1  # Cyclomatic complexity


@dataclass
class ImportInfo:
    """インポート情報"""
    module: str
    names: List[str]
    alias: Optional[str] = None
    line_number: int = 0
    is_from_import: bool = False


class PythonASTVisitor(ast.NodeVisitor):
    """
    Python ASTビジター
    効率的な木構造走査で情報を収集
    """
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.classes: List[ClassInfo] = []
        self.functions: List[MethodInfo] = []
        self.imports: List[ImportInfo] = []
        self.current_class: Optional[ClassInfo] = None
        self.complexity_stack: List[int] = [1]
        
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """クラス定義を訪問"""
        # クラス情報を抽出
        class_info = ClassInfo(
            name=node.name,
            line_number=node.lineno,
            end_line_number=getattr(node, 'end_lineno', None),
            docstring=ast.get_docstring(node),
            base_classes=self._extract_base_classes(node),
            decorators=self._extract_decorators(node),
            is_abstract=self._is_abstract_class(node)
        )
        
        # 現在のクラスコンテキストを設定
        parent_class = self.current_class
        self.current_class = class_info
        
        # クラス属性を抽出
        class_info.attributes = self._extract_class_attributes(node)
        
        # 子ノードを訪問（メソッドなど）
        self.generic_visit(node)
        
        # クラスコンテキストを復元
        self.current_class = parent_class
        
        # 結果に追加
        if parent_class:
            # ネストされたクラス
            parent_class.attributes.append(f"class:{node.name}")
        else:
            self.classes.append(class_info)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """関数定義を訪問"""
        self._visit_function(node, is_async=False)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """非同期関数定義を訪問"""
        self._visit_function(node, is_async=True)
    
    def _visit_function(self, node, is_async: bool) -> None:
        """関数/メソッドの共通処理"""
        method_info = MethodInfo(
            name=node.name,
            line_number=node.lineno,
            end_line_number=getattr(node, 'end_lineno', None),
            docstring=ast.get_docstring(node),
            parameters=self._extract_parameters(node),
            return_type=self._extract_return_type(node),
            decorators=self._extract_decorators(node),
            is_async=is_async,
            complexity=self._calculate_complexity(node)
        )
        
        # デコレータから特殊メソッドを判定
        decorators_str = [d if isinstance(d, str) else '' for d in method_info.decorators]
        method_info.is_static = 'staticmethod' in decorators_str
        method_info.is_classmethod = 'classmethod' in decorators_str
        method_info.is_property = 'property' in decorators_str
        
        if self.current_class:
            # クラスメソッド
            self.current_class.methods.append(method_info)
        else:
            # トップレベル関数
            self.functions.append(method_info)
        
        # 子ノードを訪問
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import) -> None:
        """import文を訪問"""
        for alias in node.names:
            self.imports.append(ImportInfo(
                module=alias.name,
                names=[alias.name],
                alias=alias.asname,
                line_number=node.lineno,
                is_from_import=False
            ))
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """from-import文を訪問"""
        module = node.module or ''
        names = [alias.name for alias in node.names]
        
        self.imports.append(ImportInfo(
            module=module,
            names=names,
            line_number=node.lineno,
            is_from_import=True
        ))
    
    def visit_If(self, node: ast.If) -> None:
        """if文を訪問（複雑度計算用）"""
        self.complexity_stack[-1] += 1
        self.generic_visit(node)
    
    def visit_For(self, node: ast.For) -> None:
        """for文を訪問（複雑度計算用）"""
        self.complexity_stack[-1] += 1
        self.generic_visit(node)
    
    def visit_While(self, node: ast.While) -> None:
        """while文を訪問（複雑度計算用）"""
        self.complexity_stack[-1] += 1
        self.generic_visit(node)
    
    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        """except節を訪問（複雑度計算用）"""
        self.complexity_stack[-1] += 1
        self.generic_visit(node)
    
    def _extract_base_classes(self, node: ast.ClassDef) -> List[str]:
        """基底クラスを抽出"""
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(ast.unparse(base))
            else:
                try:
                    bases.append(ast.unparse(base))
                except (AttributeError, TypeError, ValueError) as e:
                    logger.warning(f"Failed to extract base class: {e}")
                    bases.append("Unknown")
        return bases
    
    def _extract_decorators(self, node) -> List[str]:
        """デコレータを抽出"""
        decorators = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorators.append(f"{decorator.attr}")
            else:
                try:
                    decorators.append(ast.unparse(decorator))
                except (AttributeError, TypeError, ValueError) as e:
                    logger.warning(f"Failed to extract decorator: {e}")
                    decorators.append("Unknown")
        return decorators
    
    def _extract_class_attributes(self, node: ast.ClassDef) -> List[str]:
        """クラス属性を抽出"""
        attributes = []
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)
            elif isinstance(item, ast.AnnAssign):
                if isinstance(item.target, ast.Name):
                    attributes.append(item.target.id)
        return attributes
    
    def _extract_parameters(self, node) -> List[Dict[str, Any]]:
        """パラメータを抽出"""
        params = []
        for arg in node.args.args:
            param_info = {
                'name': arg.arg,
                'type': None,
                'default': None
            }
            
            # 型アノテーション
            if arg.annotation:
                try:
                    param_info['type'] = ast.unparse(arg.annotation)
                except (AttributeError, TypeError, ValueError) as e:
                    logger.warning(f"Failed to extract parameter type: {e}")
                    param_info['type'] = "Unknown"
            
            params.append(param_info)
        
        # デフォルト値を設定
        defaults = node.args.defaults
        if defaults:
            offset = len(params) - len(defaults)
            for i, default in enumerate(defaults):
                try:
                    params[offset + i]['default'] = ast.unparse(default)
                except (AttributeError, TypeError, ValueError) as e:
                    logger.warning(f"Failed to extract default value: {e}")
                    params[offset + i]['default'] = "..."
        
        return params
    
    def _extract_return_type(self, node) -> Optional[str]:
        """戻り値の型を抽出"""
        if node.returns:
            try:
                return ast.unparse(node.returns)
            except (AttributeError, TypeError, ValueError) as e:
                logger.warning(f"Failed to extract return type: {e}")
                return "Unknown"
        return None
    
    def _is_abstract_class(self, node: ast.ClassDef) -> bool:
        """抽象クラスかどうかを判定"""
        # ABC継承をチェック
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == 'ABC':
                return True
            elif isinstance(base, ast.Attribute) and base.attr == 'ABC':
                return True
        
        # abstractmethodデコレータをチェック
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in item.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == 'abstractmethod':
                        return True
        
        return False
    
    def _calculate_complexity(self, node) -> int:
        """循環的複雑度を計算"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def get_analysis_result(self) -> Dict[str, Any]:
        """解析結果を取得"""
        return {
            'file_path': str(self.file_path),
            'classes': self.classes,
            'functions': self.functions,
            'imports': self.imports,
            'metrics': {
                'total_classes': len(self.classes),
                'total_functions': len(self.functions),
                'total_methods': sum(len(c.methods) for c in self.classes),
                'total_imports': len(self.imports),
                'avg_complexity': self._calculate_average_complexity()
            }
        }
    
    def _calculate_average_complexity(self) -> float:
        """平均複雑度を計算"""
        all_methods = self.functions + [m for c in self.classes for m in c.methods]
        if not all_methods:
            return 0.0
        return sum(m.complexity for m in all_methods) / len(all_methods)