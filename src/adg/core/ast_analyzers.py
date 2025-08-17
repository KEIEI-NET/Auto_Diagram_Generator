"""
各言語専用のASTパーサーを使用した解析モジュール
tree-sitter, javalang, esprima等を統合
"""

import ast
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger

# Tree-sitter imports
import tree_sitter_languages as tsl

# Language-specific parsers
import esprima
import javalang

from adg.core.analyzer import CodeElement, ClassInfo, FunctionInfo, ImportInfo
from adg.core.secure_analyzer import (
    SecureLanguageAnalyzer,
    SerializationMixin,
    SecureFileHandler
)


class ASTAnalyzer(SecureLanguageAnalyzer, ABC):
    """AST解析基底クラス"""
    
    def supports_ast(self) -> bool:
        """AST解析をサポートするか"""
        return True
    
    @abstractmethod
    def parse_ast(self) -> Any:
        """ASTを解析して返す"""
        pass
    
    @abstractmethod
    def extract_from_ast(self, tree: Any) -> Dict[str, Any]:
        """ASTから構造を抽出"""
        pass
    
    def analyze(self) -> Dict[str, Any]:
        """AST解析を実行"""
        try:
            tree = self.parse_ast()
            if tree:
                return self.extract_from_ast(tree)
        except Exception as e:
            logger.warning(f"AST parsing failed for {self.file_path}: {e}")
        
        # フォールバック
        return self._fallback_analysis()
    
    def _fallback_analysis(self) -> Dict[str, Any]:
        """フォールバック解析（基本的な情報のみ）"""
        return {
            'file_path': str(self.file_path),
            'language': self.get_language_name(),
            'classes': [],
            'functions': [],
            'imports': [],
            'ast_used': False,
            'error': 'AST parsing failed, fallback used'
        }


class TreeSitterAnalyzer(ASTAnalyzer):
    """Tree-sitterベースの汎用アナライザー"""
    
    LANGUAGE_MAP = {
        '.java': 'java',
        '.js': 'javascript',
        '.jsx': 'jsx',
        '.ts': 'typescript',
        '.tsx': 'tsx',
        '.py': 'python',
        '.go': 'go',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.c': 'c',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cs': 'c_sharp',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.r': 'r',
        '.lua': 'lua',
        '.perl': 'perl',
        '.pl': 'perl',
        '.sh': 'bash',
        '.bash': 'bash',
    }
    
    def __init__(self, file_path: str, base_path: Optional[Path] = None):
        super().__init__(file_path, base_path)
        self.language = self._detect_language()
        self.parser = None
        if self.language:
            try:
                self.parser = tsl.get_parser(self.language)
            except Exception as e:
                logger.warning(f"Could not get parser for {self.language}: {e}")
    
    def _detect_language(self) -> Optional[str]:
        """ファイル拡張子から言語を検出"""
        ext = self.file_path.suffix.lower()
        return self.LANGUAGE_MAP.get(ext)
    
    def get_language_name(self) -> str:
        return self.language or 'unknown'
    
    def parse_ast(self) -> Optional[Any]:
        """Tree-sitterでASTを解析"""
        if not self.parser or not self.content:
            return None
        
        try:
            tree = self.parser.parse(bytes(self.content, 'utf8'))
            return tree
        except Exception as e:
            logger.error(f"Tree-sitter parsing failed: {e}")
            return None
    
    def extract_from_ast(self, tree: Any) -> Dict[str, Any]:
        """Tree-sitter ASTから構造を抽出"""
        classes = []
        functions = []
        imports = []
        
        # Tree-sitterのASTを探索
        def traverse(node, depth=0):
            node_type = node.type
            
            # 言語別の処理
            if self.language == 'java':
                if node_type == 'class_declaration':
                    classes.append(self._extract_java_class(node))
                elif node_type == 'method_declaration':
                    if depth <= 1:  # トップレベルのメソッドのみ
                        functions.append(self._extract_java_method(node))
                elif node_type == 'import_declaration':
                    imports.append(self._extract_java_import(node))
                    
            elif self.language in ['javascript', 'typescript', 'jsx', 'tsx']:
                if node_type == 'class_declaration':
                    classes.append(self._extract_js_class(node))
                elif node_type in ['function_declaration', 'arrow_function']:
                    functions.append(self._extract_js_function(node))
                elif node_type == 'import_statement':
                    imports.append(self._extract_js_import(node))
                    
            elif self.language == 'python':
                if node_type == 'class_definition':
                    classes.append(self._extract_python_class(node))
                elif node_type == 'function_definition':
                    if depth <= 1:
                        functions.append(self._extract_python_function(node))
                elif node_type in ['import_statement', 'import_from_statement']:
                    imports.append(self._extract_python_import(node))
                    
            elif self.language == 'go':
                if node_type == 'type_declaration':
                    classes.append(self._extract_go_struct(node))
                elif node_type == 'function_declaration':
                    functions.append(self._extract_go_function(node))
                elif node_type == 'import_declaration':
                    imports.append(self._extract_go_import(node))
                    
            elif self.language == 'cpp':
                if node_type == 'class_specifier':
                    classes.append(self._extract_cpp_class(node))
                elif node_type == 'function_definition':
                    functions.append(self._extract_cpp_function(node))
                elif node_type == 'preproc_include':
                    imports.append(self._extract_cpp_include(node))
                    
            elif self.language == 'rust':
                if node_type in ['struct_item', 'enum_item']:
                    classes.append(self._extract_rust_struct(node))
                elif node_type == 'function_item':
                    functions.append(self._extract_rust_function(node))
                elif node_type == 'use_declaration':
                    imports.append(self._extract_rust_use(node))
            
            # 子ノードを探索
            for child in node.children:
                traverse(child, depth + 1)
        
        if tree.root_node:
            traverse(tree.root_node)
        
        return {
            'file_path': str(self.file_path),
            'language': self.language,
            'classes': [self._class_to_dict(c) for c in classes if c],
            'functions': [self._function_to_dict(f) for f in functions if f],
            'imports': [self._import_to_dict(i) for i in imports if i],
            'ast_used': True
        }
    
    def _get_node_text(self, node) -> str:
        """ノードのテキストを取得"""
        if hasattr(node, 'text'):
            return node.text.decode('utf8') if isinstance(node.text, bytes) else str(node.text)
        return ''
    
    def _extract_java_class(self, node) -> Optional[ClassInfo]:
        """Javaクラス情報を抽出"""
        class_name = None
        methods = []
        fields = []
        
        for child in node.children:
            if child.type == 'identifier':
                class_name = self._get_node_text(child)
            elif child.type == 'class_body':
                for body_item in child.children:
                    if body_item.type == 'method_declaration':
                        method_name = None
                        for method_child in body_item.children:
                            if method_child.type == 'identifier':
                                method_name = self._get_node_text(method_child)
                                break
                        if method_name:
                            methods.append(method_name)
                    elif body_item.type == 'field_declaration':
                        fields.append(self._get_node_text(body_item))
        
        if class_name:
            return ClassInfo(
                name=class_name,
                type='class',
                file_path=str(self.file_path),
                line_number=node.start_point[0] + 1,
                methods=methods,
                attributes=fields,
                base_classes=[],
                decorators=[]
            )
        return None
    
    def _extract_java_method(self, node) -> Optional[FunctionInfo]:
        """Javaメソッド情報を抽出"""
        method_name = None
        params = []
        
        for child in node.children:
            if child.type == 'identifier':
                method_name = self._get_node_text(child)
            elif child.type == 'formal_parameters':
                for param in child.children:
                    if param.type == 'formal_parameter':
                        params.append(self._get_node_text(param))
        
        if method_name:
            return FunctionInfo(
                name=method_name,
                type='method',
                file_path=str(self.file_path),
                line_number=node.start_point[0] + 1,
                parameters=params,
                is_async=False,
                return_type=None,
                decorators=[]
            )
        return None
    
    def _extract_java_import(self, node) -> Optional[ImportInfo]:
        """Javaインポート情報を抽出"""
        import_text = self._get_node_text(node)
        # "import " を除去
        if import_text.startswith('import '):
            import_text = import_text[7:].strip().rstrip(';')
            
            return ImportInfo(
                name=import_text,
                type='import',
                file_path=str(self.file_path),
                line_number=node.start_point[0] + 1,
                module=import_text,
                imported_names=[],
                is_from_import=False
            )
        return None
    
    def _extract_js_class(self, node) -> Optional[ClassInfo]:
        """JavaScript/TypeScriptクラス情報を抽出"""
        class_name = None
        methods = []
        
        for child in node.children:
            if child.type == 'identifier':
                class_name = self._get_node_text(child)
            elif child.type == 'class_body':
                for body_item in child.children:
                    if body_item.type in ['method_definition', 'public_field_definition']:
                        for item_child in body_item.children:
                            if item_child.type == 'property_identifier':
                                methods.append(self._get_node_text(item_child))
                                break
        
        if class_name:
            return ClassInfo(
                name=class_name,
                type='class',
                file_path=str(self.file_path),
                line_number=node.start_point[0] + 1,
                methods=methods,
                attributes=[],
                base_classes=[],
                decorators=[]
            )
        return None
    
    def _extract_js_function(self, node) -> Optional[FunctionInfo]:
        """JavaScript/TypeScript関数情報を抽出"""
        func_name = None
        params = []
        is_async = False
        
        for child in node.children:
            if child.type == 'identifier':
                func_name = self._get_node_text(child)
            elif child.type == 'formal_parameters':
                for param in child.children:
                    if param.type in ['identifier', 'required_parameter']:
                        params.append(self._get_node_text(param))
        
        # async チェック
        if node.parent and 'async' in self._get_node_text(node.parent):
            is_async = True
        
        if func_name:
            return FunctionInfo(
                name=func_name,
                type='function',
                file_path=str(self.file_path),
                line_number=node.start_point[0] + 1,
                parameters=params,
                is_async=is_async,
                return_type=None,
                decorators=[]
            )
        return None
    
    def _extract_js_import(self, node) -> Optional[ImportInfo]:
        """JavaScript/TypeScriptインポート情報を抽出"""
        import_text = self._get_node_text(node)
        
        # 簡易的な解析
        if 'from' in import_text:
            parts = import_text.split('from')
            if len(parts) == 2:
                module = parts[1].strip().strip('"\'')
                return ImportInfo(
                    name=module,
                    type='import',
                    file_path=str(self.file_path),
                    line_number=node.start_point[0] + 1,
                    module=module,
                    imported_names=[],
                    is_from_import=True
                )
        return None
    
    def _extract_python_class(self, node) -> Optional[ClassInfo]:
        """Pythonクラス情報を抽出"""
        class_name = None
        methods = []
        
        for child in node.children:
            if child.type == 'identifier':
                class_name = self._get_node_text(child)
            elif child.type == 'block':
                for stmt in child.children:
                    if stmt.type == 'function_definition':
                        for func_child in stmt.children:
                            if func_child.type == 'identifier':
                                methods.append(self._get_node_text(func_child))
                                break
        
        if class_name:
            return ClassInfo(
                name=class_name,
                type='class',
                file_path=str(self.file_path),
                line_number=node.start_point[0] + 1,
                methods=methods,
                attributes=[],
                base_classes=[],
                decorators=[]
            )
        return None
    
    def _extract_python_function(self, node) -> Optional[FunctionInfo]:
        """Python関数情報を抽出"""
        func_name = None
        params = []
        is_async = False
        
        for child in node.children:
            if child.type == 'identifier':
                func_name = self._get_node_text(child)
            elif child.type == 'parameters':
                for param in child.children:
                    if param.type == 'identifier':
                        params.append(self._get_node_text(param))
        
        # async チェック
        text = self._get_node_text(node)
        if text.startswith('async '):
            is_async = True
        
        if func_name:
            return FunctionInfo(
                name=func_name,
                type='function',
                file_path=str(self.file_path),
                line_number=node.start_point[0] + 1,
                parameters=params,
                is_async=is_async,
                return_type=None,
                decorators=[]
            )
        return None
    
    def _extract_python_import(self, node) -> Optional[ImportInfo]:
        """Pythonインポート情報を抽出"""
        import_text = self._get_node_text(node)
        
        if import_text.startswith('import '):
            module = import_text[7:].strip()
        elif import_text.startswith('from '):
            parts = import_text.split(' import ')
            if len(parts) == 2:
                module = parts[0][5:].strip()
            else:
                module = import_text
        else:
            module = import_text
        
        return ImportInfo(
            name=module,
            type='import',
            file_path=str(self.file_path),
            line_number=node.start_point[0] + 1,
            module=module,
            imported_names=[],
            is_from_import='from' in import_text
        )
    
    def _extract_go_struct(self, node) -> Optional[ClassInfo]:
        """Go構造体情報を抽出"""
        struct_name = None
        fields = []
        
        for child in node.children:
            if child.type == 'type_spec':
                for spec_child in child.children:
                    if spec_child.type == 'type_identifier':
                        struct_name = self._get_node_text(spec_child)
                    elif spec_child.type == 'struct_type':
                        for field in spec_child.children:
                            if field.type == 'field_declaration':
                                fields.append(self._get_node_text(field))
        
        if struct_name:
            return ClassInfo(
                name=struct_name,
                type='struct',
                file_path=str(self.file_path),
                line_number=node.start_point[0] + 1,
                methods=[],
                attributes=fields,
                base_classes=[],
                decorators=[]
            )
        return None
    
    def _extract_go_function(self, node) -> Optional[FunctionInfo]:
        """Go関数情報を抽出"""
        func_name = None
        params = []
        
        for child in node.children:
            if child.type == 'identifier':
                func_name = self._get_node_text(child)
            elif child.type == 'parameter_list':
                for param in child.children:
                    if param.type == 'parameter_declaration':
                        params.append(self._get_node_text(param))
        
        if func_name:
            return FunctionInfo(
                name=func_name,
                type='function',
                file_path=str(self.file_path),
                line_number=node.start_point[0] + 1,
                parameters=params,
                is_async=False,
                return_type=None,
                decorators=[]
            )
        return None
    
    def _extract_go_import(self, node) -> Optional[ImportInfo]:
        """Goインポート情報を抽出"""
        import_text = self._get_node_text(node)
        
        # import文から引用符を除去
        import_text = import_text.replace('import', '').strip()
        import_text = import_text.strip('"\'')
        
        return ImportInfo(
            name=import_text,
            type='import',
            file_path=str(self.file_path),
            line_number=node.start_point[0] + 1,
            module=import_text,
            imported_names=[],
            is_from_import=False
        )
    
    def _extract_cpp_class(self, node) -> Optional[ClassInfo]:
        """C++クラス情報を抽出"""
        class_name = None
        methods = []
        
        for child in node.children:
            if child.type == 'type_identifier':
                class_name = self._get_node_text(child)
            elif child.type == 'field_declaration_list':
                for field in child.children:
                    if field.type == 'function_definition':
                        for func_child in field.children:
                            if func_child.type == 'function_declarator':
                                for decl_child in func_child.children:
                                    if decl_child.type == 'identifier':
                                        methods.append(self._get_node_text(decl_child))
                                        break
        
        if class_name:
            return ClassInfo(
                name=class_name,
                type='class',
                file_path=str(self.file_path),
                line_number=node.start_point[0] + 1,
                methods=methods,
                attributes=[],
                base_classes=[],
                decorators=[]
            )
        return None
    
    def _extract_cpp_function(self, node) -> Optional[FunctionInfo]:
        """C++関数情報を抽出"""
        func_name = None
        params = []
        
        for child in node.children:
            if child.type == 'function_declarator':
                for decl_child in child.children:
                    if decl_child.type == 'identifier':
                        func_name = self._get_node_text(decl_child)
                    elif decl_child.type == 'parameter_list':
                        for param in decl_child.children:
                            if param.type == 'parameter_declaration':
                                params.append(self._get_node_text(param))
        
        if func_name:
            return FunctionInfo(
                name=func_name,
                type='function',
                file_path=str(self.file_path),
                line_number=node.start_point[0] + 1,
                parameters=params,
                is_async=False,
                return_type=None,
                decorators=[]
            )
        return None
    
    def _extract_cpp_include(self, node) -> Optional[ImportInfo]:
        """C++インクルード情報を抽出"""
        include_text = self._get_node_text(node)
        
        # #include から始まる部分を除去
        if include_text.startswith('#include'):
            include_text = include_text[8:].strip()
            include_text = include_text.strip('<>"')
            
            return ImportInfo(
                name=include_text,
                type='include',
                file_path=str(self.file_path),
                line_number=node.start_point[0] + 1,
                module=include_text,
                imported_names=[],
                is_from_import=False
            )
        return None
    
    def _extract_rust_struct(self, node) -> Optional[ClassInfo]:
        """Rust構造体情報を抽出"""
        struct_name = None
        fields = []
        
        for child in node.children:
            if child.type == 'identifier':
                struct_name = self._get_node_text(child)
            elif child.type == 'field_declaration_list':
                for field in child.children:
                    if field.type == 'field_declaration':
                        fields.append(self._get_node_text(field))
        
        if struct_name:
            return ClassInfo(
                name=struct_name,
                type='struct',
                file_path=str(self.file_path),
                line_number=node.start_point[0] + 1,
                methods=[],
                attributes=fields,
                base_classes=[],
                decorators=[]
            )
        return None
    
    def _extract_rust_function(self, node) -> Optional[FunctionInfo]:
        """Rust関数情報を抽出"""
        func_name = None
        params = []
        is_async = False
        
        for child in node.children:
            if child.type == 'identifier':
                func_name = self._get_node_text(child)
            elif child.type == 'parameters':
                for param in child.children:
                    if param.type == 'parameter':
                        params.append(self._get_node_text(param))
        
        # async チェック
        text = self._get_node_text(node)
        if 'async' in text:
            is_async = True
        
        if func_name:
            return FunctionInfo(
                name=func_name,
                type='function',
                file_path=str(self.file_path),
                line_number=node.start_point[0] + 1,
                parameters=params,
                is_async=is_async,
                return_type=None,
                decorators=[]
            )
        return None
    
    def _extract_rust_use(self, node) -> Optional[ImportInfo]:
        """Rust use文情報を抽出"""
        use_text = self._get_node_text(node)
        
        if use_text.startswith('use '):
            use_text = use_text[4:].strip().rstrip(';')
            
            return ImportInfo(
                name=use_text,
                type='use',
                file_path=str(self.file_path),
                line_number=node.start_point[0] + 1,
                module=use_text,
                imported_names=[],
                is_from_import=False
            )
        return None


class JavaLangAnalyzer(ASTAnalyzer):
    """javalang を使用したJava専用アナライザー"""
    
    def get_language_name(self) -> str:
        return 'java'
    
    def parse_ast(self) -> Optional[Any]:
        """javalangでASTを解析"""
        try:
            tree = javalang.parse.parse(self.content)
            return tree
        except Exception as e:
            logger.error(f"javalang parsing failed: {e}")
            return None
    
    def extract_from_ast(self, tree: Any) -> Dict[str, Any]:
        """javalang ASTから構造を抽出"""
        classes = []
        functions = []
        imports = []
        
        # インポートを抽出
        for imp in tree.imports:
            imports.append(ImportInfo(
                name=imp.path,
                type='import',
                file_path=str(self.file_path),
                line_number=imp.position.line if imp.position else 0,
                module=imp.path,
                imported_names=[],
                is_from_import=False
            ))
        
        # クラスを抽出
        for _, node in tree.filter(javalang.tree.ClassDeclaration):
            methods = []
            fields = []
            
            # メソッドを抽出
            for method in node.methods:
                methods.append(method.name)
                
                # トップレベルメソッドとして追加
                functions.append(FunctionInfo(
                    name=method.name,
                    type='method',
                    file_path=str(self.file_path),
                    line_number=method.position.line if method.position else 0,
                    parameters=[param.name for param in method.parameters],
                    is_async=False,
                    return_type=method.return_type.name if method.return_type else None,
                    decorators=[anno.name for anno in method.annotations] if method.annotations else []
                ))
            
            # フィールドを抽出
            for field in node.fields:
                for declarator in field.declarators:
                    fields.append(f"{declarator.name}: {field.type.name if field.type else 'Object'}")
            
            # 基底クラスとインターフェース
            base_classes = []
            if node.extends:
                base_classes.append(node.extends.name)
            if node.implements:
                base_classes.extend([i.name for i in node.implements])
            
            classes.append(ClassInfo(
                name=node.name,
                type='class',
                file_path=str(self.file_path),
                line_number=node.position.line if node.position else 0,
                methods=methods,
                attributes=fields,
                base_classes=base_classes,
                decorators=[anno.name for anno in node.annotations] if node.annotations else []
            ))
        
        # インターフェースも抽出
        for _, node in tree.filter(javalang.tree.InterfaceDeclaration):
            methods = []
            for method in node.methods:
                methods.append(method.name)
            
            classes.append(ClassInfo(
                name=node.name,
                type='interface',
                file_path=str(self.file_path),
                line_number=node.position.line if node.position else 0,
                methods=methods,
                attributes=[],
                base_classes=[i.name for i in node.extends] if node.extends else [],
                decorators=[anno.name for anno in node.annotations] if node.annotations else []
            ))
        
        return {
            'file_path': str(self.file_path),
            'language': 'java',
            'classes': [self._class_to_dict(c) for c in classes],
            'functions': [self._function_to_dict(f) for f in functions],
            'imports': [self._import_to_dict(i) for i in imports],
            'ast_used': True
        }


class EsprimaJSAnalyzer(ASTAnalyzer):
    """esprima を使用したJavaScript専用アナライザー（既存実装の改良版）"""
    
    def get_language_name(self) -> str:
        ext = self.file_path.suffix.lower()
        if ext in ['.ts', '.tsx']:
            return 'typescript'
        return 'javascript'
    
    def parse_ast(self) -> Optional[Any]:
        """esprimaでASTを解析"""
        try:
            tree = esprima.parseModule(self.content, {'loc': True, 'range': True})
            return tree
        except Exception as e:
            logger.error(f"esprima parsing failed: {e}")
            return None
    
    def extract_from_ast(self, tree: Any) -> Dict[str, Any]:
        """esprima ASTから構造を抽出（改良版）"""
        classes = []
        functions = []
        imports = []
        
        tree_dict = tree.toDict() if hasattr(tree, 'toDict') else tree
        
        def visit_node(node, parent=None, in_class=None):
            if not isinstance(node, dict):
                return
            
            node_type = node.get('type')
            
            if node_type == 'ClassDeclaration':
                class_info = self._extract_class_info(node)
                if class_info:
                    classes.append(class_info)
                    # クラス内部を探索（in_classフラグ付き）
                    for key, value in node.items():
                        if key == 'body':
                            visit_node(value, node, class_info.name)
                        elif isinstance(value, dict):
                            visit_node(value, node, class_info.name)
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict):
                                    visit_node(item, node, class_info.name)
                    return  # クラス内部は既に探索済み
                    
            elif node_type == 'FunctionDeclaration' and not in_class:
                func_info = self._extract_function_info(node)
                if func_info:
                    functions.append(func_info)
                    
            elif node_type == 'VariableDeclaration' and not in_class:
                for decl in node.get('declarations', []):
                    init = decl.get('init', {})
                    if isinstance(init, dict):
                        if init.get('type') == 'ArrowFunctionExpression':
                            func_info = self._extract_arrow_function(decl)
                            if func_info:
                                functions.append(func_info)
                        elif init.get('type') == 'FunctionExpression':
                            func_info = self._extract_function_expression(decl)
                            if func_info:
                                functions.append(func_info)
                                
            elif node_type == 'ImportDeclaration':
                import_info = self._extract_import_info(node)
                if import_info:
                    imports.append(import_info)
            
            # 子ノードを探索（クラスは既に処理済み）
            if node_type != 'ClassDeclaration':
                for key, value in node.items():
                    if isinstance(value, dict):
                        visit_node(value, node, in_class)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                visit_node(item, node, in_class)
        
        visit_node(tree_dict)
        
        return {
            'file_path': str(self.file_path),
            'language': self.get_language_name(),
            'classes': [self._class_to_dict(c) for c in classes],
            'functions': [self._function_to_dict(f) for f in functions],
            'imports': [self._import_to_dict(i) for i in imports],
            'ast_used': True
        }
    
    def _extract_class_info(self, node: dict) -> Optional[ClassInfo]:
        """クラス情報を抽出"""
        class_name = node.get('id', {}).get('name', 'Anonymous')
        super_class = node.get('superClass', {}).get('name') if node.get('superClass') else None
        
        methods = []
        attributes = []
        
        body = node.get('body', {})
        if isinstance(body, dict):
            for item in body.get('body', []):
                if item.get('type') == 'MethodDefinition':
                    key = item.get('key', {})
                    method_name = key.get('name') if isinstance(key, dict) else str(key)
                    if method_name:
                        methods.append(method_name)
                elif item.get('type') == 'PropertyDefinition':
                    key = item.get('key', {})
                    prop_name = key.get('name') if isinstance(key, dict) else str(key)
                    if prop_name:
                        attributes.append(prop_name)
        
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
    
    def _extract_function_info(self, node: dict) -> Optional[FunctionInfo]:
        """関数情報を抽出"""
        func_name = node.get('id', {}).get('name', 'Anonymous')
        params = []
        
        for param in node.get('params', []):
            if isinstance(param, dict):
                param_name = param.get('name', '')
                if not param_name and param.get('type') == 'Identifier':
                    param_name = param.get('name', '')
                if param_name:
                    params.append(param_name)
        
        return FunctionInfo(
            name=func_name,
            type='function',
            file_path=str(self.file_path),
            line_number=node.get('loc', {}).get('start', {}).get('line', 0),
            parameters=params,
            is_async=node.get('async', False),
            return_type=None,
            decorators=[]
        )
    
    def _extract_arrow_function(self, node: dict) -> Optional[FunctionInfo]:
        """アロー関数情報を抽出"""
        func_name = node.get('id', {}).get('name', 'Anonymous')
        init = node.get('init', {})
        
        params = []
        for param in init.get('params', []):
            if isinstance(param, dict):
                param_name = param.get('name', '')
                if param_name:
                    params.append(param_name)
        
        return FunctionInfo(
            name=func_name,
            type='arrow_function',
            file_path=str(self.file_path),
            line_number=node.get('loc', {}).get('start', {}).get('line', 0),
            parameters=params,
            is_async=init.get('async', False),
            return_type=None,
            decorators=[]
        )
    
    def _extract_function_expression(self, node: dict) -> Optional[FunctionInfo]:
        """関数式情報を抽出"""
        func_name = node.get('id', {}).get('name', 'Anonymous')
        init = node.get('init', {})
        
        params = []
        for param in init.get('params', []):
            if isinstance(param, dict):
                param_name = param.get('name', '')
                if param_name:
                    params.append(param_name)
        
        return FunctionInfo(
            name=func_name,
            type='function_expression',
            file_path=str(self.file_path),
            line_number=node.get('loc', {}).get('start', {}).get('line', 0),
            parameters=params,
            is_async=init.get('async', False),
            return_type=None,
            decorators=[]
        )
    
    def _extract_import_info(self, node: dict) -> Optional[ImportInfo]:
        """インポート情報を抽出"""
        source = node.get('source', {}).get('value', '')
        specifiers = node.get('specifiers', [])
        
        imported_names = []
        for spec in specifiers:
            spec_type = spec.get('type')
            if spec_type == 'ImportDefaultSpecifier':
                imported_names.append(spec.get('local', {}).get('name', 'default'))
            elif spec_type == 'ImportSpecifier':
                imported = spec.get('imported', {})
                name = imported.get('name') if isinstance(imported, dict) else str(imported)
                if name:
                    imported_names.append(name)
            elif spec_type == 'ImportNamespaceSpecifier':
                local = spec.get('local', {})
                name = local.get('name') if isinstance(local, dict) else str(local)
                if name:
                    imported_names.append(f"* as {name}")
        
        return ImportInfo(
            name=source,
            type='import',
            file_path=str(self.file_path),
            line_number=node.get('loc', {}).get('start', {}).get('line', 0),
            module=source,
            imported_names=imported_names,
            is_from_import=True
        )


class DelphiAnalyzer(ASTAnalyzer):
    """Delphi/Pascal 専用アナライザー（高精度正規表現ベース）"""
    
    def get_language_name(self) -> str:
        return 'delphi'
    
    def parse_ast(self) -> Optional[Any]:
        """Delphiコードを疑似AST形式で解析"""
        # Delphiは専用ASTパーサーがないため、構造化された正規表現解析を使用
        return self.content  # コンテンツ自体を返す
    
    def extract_from_ast(self, content: str) -> Dict[str, Any]:
        """Delphiコードから構造を抽出"""
        classes = []
        functions = []
        imports = []
        
        # ユニット名を取得
        unit_match = re.search(r'unit\s+(\w+);', content, re.IGNORECASE)
        unit_name = unit_match.group(1) if unit_match else 'Unknown'
        
        # uses句からインポートを抽出
        uses_pattern = r'uses\s+([\w\s,\.]+);'
        for match in re.finditer(uses_pattern, content, re.IGNORECASE):
            units = match.group(1).split(',')
            for unit in units:
                unit = unit.strip()
                if unit:
                    imports.append(ImportInfo(
                        name=unit,
                        type='uses',
                        file_path=str(self.file_path),
                        line_number=content[:match.start()].count('\n') + 1,
                        module=unit,
                        imported_names=[],
                        is_from_import=False
                    ))
        
        # クラス定義を抽出（コメントと文字列を除外）
        content_no_comments = self._remove_comments_and_strings(content)
        
        # クラス定義パターン（TMyClass = class(TParent) から end; まで）
        class_pattern = r'(\w+)\s*=\s*class(?:\s*\(([^)]+)\))?\s*(.*?)(?:end;)'
        
        for match in re.finditer(class_pattern, content_no_comments, re.IGNORECASE | re.DOTALL):
            class_name = match.group(1)
            parent_class = match.group(2).strip() if match.group(2) else None
            class_body = match.group(3)
            
            # プロパティとメソッドを抽出
            methods = self._extract_delphi_methods(class_body)
            properties = self._extract_delphi_properties(class_body)
            fields = self._extract_delphi_fields(class_body)
            
            # 行番号を計算
            line_number = content[:match.start()].count('\n') + 1
            
            classes.append(ClassInfo(
                name=class_name,
                type='class',
                file_path=str(self.file_path),
                line_number=line_number,
                methods=methods,
                attributes=properties + fields,
                base_classes=[parent_class] if parent_class else [],
                decorators=[]
            ))
        
        # レコード型も抽出
        record_pattern = r'(\w+)\s*=\s*record\s*(.*?)(?:end;)'
        
        for match in re.finditer(record_pattern, content_no_comments, re.IGNORECASE | re.DOTALL):
            record_name = match.group(1)
            record_body = match.group(2)
            
            fields = self._extract_delphi_fields(record_body)
            line_number = content[:match.start()].count('\n') + 1
            
            classes.append(ClassInfo(
                name=record_name,
                type='record',
                file_path=str(self.file_path),
                line_number=line_number,
                methods=[],
                attributes=fields,
                base_classes=[],
                decorators=[]
            ))
        
        # 関数とプロシージャを抽出（implementation部）
        impl_match = re.search(r'implementation\s*(.*?)(?:end\.|$)', content, re.IGNORECASE | re.DOTALL)
        if impl_match:
            impl_section = impl_match.group(1)
            
            # 関数パターン
            func_pattern = r'function\s+(?:(\w+)\.)?(\w+)\s*(?:\(([^)]*)\))?\s*:\s*(\w+);'
            for match in re.finditer(func_pattern, impl_section, re.IGNORECASE):
                class_prefix = match.group(1)  # クラスメソッドの場合
                func_name = match.group(2)
                params = match.group(3) if match.group(3) else ''
                return_type = match.group(4)
                
                if not class_prefix:  # スタンドアロン関数のみ
                    functions.append(FunctionInfo(
                        name=func_name,
                        type='function',
                        file_path=str(self.file_path),
                        line_number=content[:match.start()].count('\n') + 1,
                        parameters=self._parse_delphi_params(params),
                        is_async=False,
                        return_type=return_type,
                        decorators=[]
                    ))
            
            # プロシージャパターン
            proc_pattern = r'procedure\s+(?:(\w+)\.)?(\w+)\s*(?:\(([^)]*)\))?;'
            for match in re.finditer(proc_pattern, impl_section, re.IGNORECASE):
                class_prefix = match.group(1)
                proc_name = match.group(2)
                params = match.group(3) if match.group(3) else ''
                
                if not class_prefix:  # スタンドアロンプロシージャのみ
                    functions.append(FunctionInfo(
                        name=proc_name,
                        type='procedure',
                        file_path=str(self.file_path),
                        line_number=content[:match.start()].count('\n') + 1,
                        parameters=self._parse_delphi_params(params),
                        is_async=False,
                        return_type='void',
                        decorators=[]
                    ))
        
        return {
            'file_path': str(self.file_path),
            'language': 'delphi',
            'unit_name': unit_name,
            'classes': [self._class_to_dict(c) for c in classes],
            'functions': [self._function_to_dict(f) for f in functions],
            'imports': [self._import_to_dict(i) for i in imports],
            'ast_used': False,  # 正規表現ベース
            'parser_type': 'enhanced_regex'
        }
    
    def _remove_comments_and_strings(self, content: str) -> str:
        """コメントと文字列リテラルを除去"""
        # {コメント} と (* コメント *) を除去
        content = re.sub(r'\{[^}]*\}', '', content)
        content = re.sub(r'\(\*.*?\*\)', '', content, flags=re.DOTALL)
        # // コメントを除去
        content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
        # 文字列リテラルを仮の文字列に置換
        content = re.sub(r"'[^']*'", "''", content)
        return content
    
    def _extract_delphi_methods(self, class_body: str) -> List[str]:
        """クラス本体からメソッドを抽出"""
        methods = []
        
        # メソッド宣言パターン
        patterns = [
            r'procedure\s+(\w+)',
            r'function\s+(\w+)',
            r'constructor\s+(\w+)',
            r'destructor\s+(\w+)'
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, class_body, re.IGNORECASE):
                method_name = match.group(1)
                if method_name not in methods:
                    methods.append(method_name)
        
        return methods
    
    def _extract_delphi_properties(self, class_body: str) -> List[str]:
        """クラス本体からプロパティを抽出"""
        properties = []
        
        # プロパティ宣言パターン
        property_pattern = r'property\s+(\w+)\s*:'
        
        for match in re.finditer(property_pattern, class_body, re.IGNORECASE):
            prop_name = match.group(1)
            properties.append(f"property {prop_name}")
        
        return properties
    
    def _extract_delphi_fields(self, body: str) -> List[str]:
        """クラスまたはレコード本体からフィールドを抽出"""
        fields = []
        
        # フィールド宣言パターン（private, protected, public セクション内）
        sections = ['private', 'protected', 'public', 'published']
        
        for section in sections:
            # セクション内のフィールドを取得
            section_pattern = rf'{section}\s+(.*?)(?:private|protected|public|published|procedure|function|property|end)'
            section_match = re.search(section_pattern, body, re.IGNORECASE | re.DOTALL)
            
            if section_match:
                section_content = section_match.group(1)
                # フィールド宣言: 名前: 型;
                field_pattern = r'(\w+)\s*:\s*([^;]+);'
                
                for match in re.finditer(field_pattern, section_content):
                    field_name = match.group(1)
                    field_type = match.group(2).strip()
                    fields.append(f"{field_name}: {field_type}")
        
        # セクション指定なしのフィールドも取得（レコードの場合）
        if not fields:
            field_pattern = r'(\w+)\s*:\s*([^;]+);'
            for match in re.finditer(field_pattern, body):
                field_name = match.group(1)
                field_type = match.group(2).strip()
                # メソッドのパラメータを除外
                if 'procedure' not in field_type.lower() and 'function' not in field_type.lower():
                    fields.append(f"{field_name}: {field_type}")
        
        return fields
    
    def _parse_delphi_params(self, params_str: str) -> List[str]:
        """Delphiのパラメータ文字列を解析"""
        if not params_str:
            return []
        
        params = []
        # パラメータはセミコロンで区切られる
        param_groups = params_str.split(';')
        
        for group in param_groups:
            group = group.strip()
            if not group:
                continue
            
            # const, var, out プレフィックスを除去
            group = re.sub(r'^(const|var|out)\s+', '', group, flags=re.IGNORECASE)
            
            # 名前: 型 の形式
            if ':' in group:
                names_part, type_part = group.split(':', 1)
                names = [n.strip() for n in names_part.split(',')]
                params.extend(names)
            else:
                # 型指定なしの場合
                params.append(group)
        
        return params


class PythonASTAnalyzer(ASTAnalyzer):
    """Python標準ast モジュールを使用したアナライザー"""
    
    def get_language_name(self) -> str:
        return 'python'
    
    def parse_ast(self) -> Optional[Any]:
        """Python標準astでASTを解析"""
        try:
            tree = ast.parse(self.content)
            return tree
        except SyntaxError as e:
            logger.error(f"Python AST parsing failed: {e}")
            return None
    
    def extract_from_ast(self, tree: Any) -> Dict[str, Any]:
        """Python ASTから構造を抽出"""
        classes = []
        functions = []
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(self._extract_class_info(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # トップレベル関数のみ（クラス内メソッドは除外）
                is_method = False
                for parent in ast.walk(tree):
                    if isinstance(parent, ast.ClassDef) and node in ast.walk(parent):
                        is_method = True
                        break
                if not is_method:
                    functions.append(self._extract_function_info(node))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(self._extract_import_info(node))
        
        return {
            'file_path': str(self.file_path),
            'language': 'python',
            'classes': [self._class_to_dict(c) for c in classes],
            'functions': [self._function_to_dict(f) for f in functions],
            'imports': [self._import_to_dict(i) for i in imports],
            'ast_used': True
        }
    
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
            elif isinstance(item, ast.AnnAssign):
                if isinstance(item.target, ast.Name):
                    attributes.append(item.target.id)
        
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_classes.append(ast.unparse(base) if hasattr(ast, 'unparse') else str(base))
        
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(dec.attr)
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                decorators.append(dec.func.id)
        
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
        """関数情報を抽出"""
        params = []
        for arg in node.args.args:
            params.append(arg.arg)
        
        return_type = None
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return_type = node.returns.id
            elif isinstance(node.returns, ast.Constant):
                return_type = str(node.returns.value)
            elif hasattr(ast, 'unparse'):
                return_type = ast.unparse(node.returns)
        
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(dec.attr)
            elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                decorators.append(dec.func.id)
        
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
        """インポート情報を抽出"""
        if isinstance(node, ast.Import):
            module = node.names[0].name if node.names else ''
            imported_names = [alias.name for alias in node.names]
        else:  # ImportFrom
            module = node.module or ''
            imported_names = []
            if node.names:
                for alias in node.names:
                    if alias.name == '*':
                        imported_names.append('*')
                    else:
                        imported_names.append(alias.name)
        
        return ImportInfo(
            name=module,
            type='import',
            file_path=str(self.file_path),
            line_number=node.lineno,
            module=module,
            imported_names=imported_names,
            is_from_import=isinstance(node, ast.ImportFrom)
        )


def get_ast_analyzer_for_file(file_path: str) -> Optional[ASTAnalyzer]:
    """
    ファイルパスから適切なASTアナライザーを自動選択
    
    Args:
        file_path: 解析するファイルパス
        
    Returns:
        適切なASTアナライザーインスタンス、対応していない場合はNone
    """
    from pathlib import Path
    
    path = Path(file_path)
    ext = path.suffix.lower()
    
    # Python: 標準ライブラリのast
    if ext in ['.py', '.pyi']:
        return PythonASTAnalyzer(file_path)
    
    # JavaScript/TypeScript: esprima
    if ext in ['.js', '.jsx', '.mjs']:
        return EsprimaJSAnalyzer(file_path)
    
    # TypeScript は esprima で部分的に対応
    if ext in ['.ts', '.tsx']:
        # TypeScriptはesprimaで完全には対応できないが、基本的な解析は可能
        return EsprimaJSAnalyzer(file_path)
    
    # Java: javalang
    if ext in ['.java']:
        return JavaLangAnalyzer(file_path)
    
    # Delphi/Pascal: 専用アナライザー
    if ext in ['.pas', '.dpr', '.dpk', '.pp', '.inc']:
        return DelphiAnalyzer(file_path)
    
    # Tree-sitter でサポートされている言語
    tree_sitter_languages = {
        '.go': 'go',
        '.rs': 'rust',
        '.c': 'c',
        '.h': 'c',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.hpp': 'cpp',
        '.hxx': 'cpp',
        '.cs': 'c_sharp',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.kts': 'kotlin',
        '.scala': 'scala',
        '.r': 'r',
        '.lua': 'lua',
        '.dart': 'dart',
        '.elm': 'elm',
        '.ex': 'elixir',
        '.exs': 'elixir',
        '.erl': 'erlang',
        '.hrl': 'erlang',
        '.hs': 'haskell',
        '.lhs': 'haskell',
        '.jl': 'julia',
        '.m': 'objc',
        '.mm': 'objc',
        '.ml': 'ocaml',
        '.mli': 'ocaml',
        '.pl': 'perl',
        '.pm': 'perl',
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'bash',
        '.fish': 'bash',
        '.vim': 'vim',
        '.sql': 'sql',
        '.toml': 'toml',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.json': 'json',
        '.html': 'html',
        '.htm': 'html',
        '.xml': 'xml',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'scss',
    }
    
    if ext in tree_sitter_languages:
        return TreeSitterAnalyzer(file_path)
    
    # 対応していない言語の場合
    return None