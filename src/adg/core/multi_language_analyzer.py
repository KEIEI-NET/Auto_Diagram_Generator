"""
多言語対応のコード解析モジュール
Claude Code CLIと統合して、あらゆるプログラミング言語を解析
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


class LanguageAnalyzer(ABC):
    """言語アナライザーの基底クラス"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.content = self._read_file()
        self.elements: List[CodeElement] = []
    
    def _read_file(self) -> str:
        """ファイルを読み込む"""
        from adg.core.secure_analyzer import SecureFileHandler
        content = SecureFileHandler.safe_read_file(self.file_path)
        return content if content else ""
    
    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """ファイルを解析して構造を抽出"""
        pass
    
    @abstractmethod
    def extract_classes(self) -> List[ClassInfo]:
        """クラス情報を抽出"""
        pass
    
    @abstractmethod
    def extract_functions(self) -> List[FunctionInfo]:
        """関数情報を抽出"""
        pass
    
    @abstractmethod
    def extract_imports(self) -> List[ImportInfo]:
        """インポート情報を抽出"""
        pass


class PythonAnalyzer(LanguageAnalyzer):
    """Python用アナライザー（既存のコードを活用）"""
    
    def analyze(self) -> Dict[str, Any]:
        from adg.core.analyzer import PythonAnalyzer as OriginalPythonAnalyzer
        analyzer = OriginalPythonAnalyzer(str(self.file_path))
        return analyzer.analyze()
    
    def extract_classes(self) -> List[ClassInfo]:
        result = self.analyze()
        return result.get('classes', [])
    
    def extract_functions(self) -> List[FunctionInfo]:
        result = self.analyze()
        return result.get('functions', [])
    
    def extract_imports(self) -> List[ImportInfo]:
        result = self.analyze()
        return result.get('imports', [])


class JavaScriptAnalyzer(LanguageAnalyzer):
    """JavaScript/TypeScript用アナライザー"""
    
    def analyze(self) -> Dict[str, Any]:
        classes = self.extract_classes()
        functions = self.extract_functions()
        imports = self.extract_imports()
        
        return {
            'file_path': str(self.file_path),
            'language': 'javascript',
            'classes': [self._class_to_dict(c) for c in classes],
            'functions': [self._function_to_dict(f) for f in functions],
            'imports': [self._import_to_dict(i) for i in imports],
        }
    
    def extract_classes(self) -> List[ClassInfo]:
        classes = []
        # ES6 class syntax
        class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?'
        
        for match in re.finditer(class_pattern, self.content):
            class_name = match.group(1)
            base_class = match.group(2) if match.group(2) else None
            
            # メソッドを抽出
            methods = self._extract_class_methods(class_name)
            
            classes.append(ClassInfo(
                name=class_name,
                type='class',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                methods=methods,
                base_classes=[base_class] if base_class else [],
                attributes=[],
                decorators=[]
            ))
        
        return classes
    
    def extract_functions(self) -> List[FunctionInfo]:
        functions = []
        
        # Regular functions
        func_pattern = r'function\s+(\w+)\s*\(([^)]*)\)'
        # Arrow functions
        arrow_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*(?:\([^)]*\)|[^=]+)\s*=>'
        # Async functions
        async_pattern = r'async\s+function\s+(\w+)\s*\(([^)]*)\)'
        
        patterns = [
            (func_pattern, False),
            (arrow_pattern, False),
            (async_pattern, True)
        ]
        
        for pattern, is_async in patterns:
            for match in re.finditer(pattern, self.content):
                func_name = match.group(1)
                params = match.group(2) if len(match.groups()) > 1 else ''
                
                functions.append(FunctionInfo(
                    name=func_name,
                    type='function',
                    file_path=str(self.file_path),
                    line_number=self.content[:match.start()].count('\n') + 1,
                    parameters=self._parse_parameters(params),
                    is_async=is_async,
                    return_type=None,
                    decorators=[]
                ))
        
        return functions
    
    def extract_imports(self) -> List[ImportInfo]:
        imports = []
        
        # ES6 imports
        import_patterns = [
            r'import\s+(\w+)\s+from\s+[\'"]([^\'\"]+)[\'"]',
            r'import\s*\{([^}]+)\}\s*from\s+[\'"]([^\'\"]+)[\'"]',
            r'import\s*\*\s*as\s+(\w+)\s+from\s+[\'"]([^\'\"]+)[\'"]',
            r'const\s+(\w+)\s*=\s*require\([\'"]([^\'\"]+)[\'"]\)',
        ]
        
        for pattern in import_patterns:
            for match in re.finditer(pattern, self.content):
                imported = match.group(1)
                module = match.group(2)
                
                imports.append(ImportInfo(
                    name=module,
                    type='import',
                    file_path=str(self.file_path),
                    line_number=self.content[:match.start()].count('\n') + 1,
                    module=module,
                    imported_names=imported.split(',') if ',' in imported else [imported],
                    is_from_import=True
                ))
        
        return imports
    
    def _extract_class_methods(self, class_name: str) -> List[str]:
        """クラスのメソッドを抽出"""
        methods = []
        class_pattern = rf'class\s+{class_name}[^{{]*\{{([^}}]+)\}}'
        
        match = re.search(class_pattern, self.content, re.DOTALL)
        if match:
            class_body = match.group(1)
            method_pattern = r'(?:async\s+)?(\w+)\s*\([^)]*\)'
            
            for method_match in re.finditer(method_pattern, class_body):
                method_name = method_match.group(1)
                if method_name not in ['if', 'for', 'while', 'switch']:
                    methods.append(method_name)
        
        return methods
    
    def _parse_parameters(self, params_str: str) -> List[str]:
        """パラメータ文字列をパース"""
        if not params_str:
            return []
        return [p.strip() for p in params_str.split(',') if p.strip()]
    
    def _class_to_dict(self, cls: ClassInfo) -> Dict[str, Any]:
        return {
            'name': cls.name,
            'methods': cls.methods,
            'attributes': cls.attributes,
            'base_classes': cls.base_classes,
            'line_number': cls.line_number
        }
    
    def _function_to_dict(self, func: FunctionInfo) -> Dict[str, Any]:
        return {
            'name': func.name,
            'parameters': func.parameters,
            'is_async': func.is_async,
            'line_number': func.line_number
        }
    
    def _import_to_dict(self, imp: ImportInfo) -> Dict[str, Any]:
        return {
            'module': imp.module,
            'imported_names': imp.imported_names,
            'line_number': imp.line_number
        }


class JavaAnalyzer(LanguageAnalyzer):
    """Java用アナライザー"""
    
    def analyze(self) -> Dict[str, Any]:
        classes = self.extract_classes()
        functions = self.extract_functions()
        imports = self.extract_imports()
        
        return {
            'file_path': str(self.file_path),
            'language': 'java',
            'classes': [self._class_to_dict(c) for c in classes],
            'functions': [self._function_to_dict(f) for f in functions],
            'imports': [self._import_to_dict(i) for i in imports],
        }
    
    def extract_classes(self) -> List[ClassInfo]:
        classes = []
        
        # Java class pattern
        class_pattern = r'(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?'
        
        for match in re.finditer(class_pattern, self.content):
            class_name = match.group(1)
            base_class = match.group(2)
            interfaces = match.group(3)
            
            # Extract methods and fields
            methods = self._extract_class_methods(class_name)
            attributes = self._extract_class_fields(class_name)
            
            base_classes = []
            if base_class:
                base_classes.append(base_class)
            if interfaces:
                base_classes.extend([i.strip() for i in interfaces.split(',')])
            
            classes.append(ClassInfo(
                name=class_name,
                type='class',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                methods=methods,
                attributes=attributes,
                base_classes=base_classes,
                decorators=self._extract_annotations(match.start())
            ))
        
        return classes
    
    def extract_functions(self) -> List[FunctionInfo]:
        functions = []
        
        # Java method pattern
        method_pattern = r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*(\w+)\s+(\w+)\s*\(([^)]*)\)'
        
        for match in re.finditer(method_pattern, self.content):
            return_type = match.group(1)
            method_name = match.group(2)
            params = match.group(3)
            
            # Skip constructors and keywords
            if return_type in ['class', 'interface', 'enum', 'if', 'for', 'while']:
                continue
            
            functions.append(FunctionInfo(
                name=method_name,
                type='method',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                parameters=self._parse_parameters(params),
                return_type=return_type,
                is_async=False,
                decorators=self._extract_annotations(match.start())
            ))
        
        return functions
    
    def extract_imports(self) -> List[ImportInfo]:
        imports = []
        
        # Java import pattern
        import_pattern = r'import\s+(?:static\s+)?([^;]+);'
        
        for match in re.finditer(import_pattern, self.content):
            import_path = match.group(1)
            module_parts = import_path.split('.')
            
            imports.append(ImportInfo(
                name=import_path,
                type='import',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                module=import_path,
                imported_names=[module_parts[-1]] if module_parts else [],
                is_from_import=False
            ))
        
        return imports
    
    def _extract_class_methods(self, class_name: str) -> List[str]:
        methods = []
        # Simplified extraction - in production, use proper Java parser
        method_pattern = r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*\w+\s+(\w+)\s*\([^)]*\)'
        
        for match in re.finditer(method_pattern, self.content):
            method_name = match.group(1)
            if method_name != class_name:  # Skip constructors
                methods.append(method_name)
        
        return methods
    
    def _extract_class_fields(self, class_name: str) -> List[str]:
        fields = []
        field_pattern = r'(?:public|private|protected)?\s*(?:static)?\s*(?:final)?\s*(\w+)\s+(\w+)\s*[;=]'
        
        for match in re.finditer(field_pattern, self.content):
            field_type = match.group(1)
            field_name = match.group(2)
            if field_type not in ['class', 'interface', 'enum']:
                fields.append(f"{field_name}: {field_type}")
        
        return fields
    
    def _extract_annotations(self, position: int) -> List[str]:
        annotations = []
        # Look for annotations before the current position
        before_text = self.content[:position]
        annotation_pattern = r'@(\w+)(?:\([^)]*\))?'
        
        for match in re.finditer(annotation_pattern, before_text[-200:]):
            annotations.append(f"@{match.group(1)}")
        
        return annotations
    
    def _parse_parameters(self, params_str: str) -> List[str]:
        if not params_str:
            return []
        return [p.strip() for p in params_str.split(',') if p.strip()]
    
    def _class_to_dict(self, cls: ClassInfo) -> Dict[str, Any]:
        return {
            'name': cls.name,
            'methods': cls.methods,
            'attributes': cls.attributes,
            'base_classes': cls.base_classes,
            'decorators': cls.decorators,
            'line_number': cls.line_number
        }
    
    def _function_to_dict(self, func: FunctionInfo) -> Dict[str, Any]:
        return {
            'name': func.name,
            'parameters': func.parameters,
            'return_type': func.return_type,
            'decorators': func.decorators,
            'line_number': func.line_number
        }
    
    def _import_to_dict(self, imp: ImportInfo) -> Dict[str, Any]:
        return {
            'module': imp.module,
            'imported_names': imp.imported_names,
            'line_number': imp.line_number
        }


class GoAnalyzer(LanguageAnalyzer):
    """Go言語用アナライザー"""
    
    def analyze(self) -> Dict[str, Any]:
        classes = self.extract_classes()  # Go has structs, not classes
        functions = self.extract_functions()
        imports = self.extract_imports()
        
        return {
            'file_path': str(self.file_path),
            'language': 'go',
            'classes': [self._class_to_dict(c) for c in classes],
            'functions': [self._function_to_dict(f) for f in functions],
            'imports': [self._import_to_dict(i) for i in imports],
        }
    
    def extract_classes(self) -> List[ClassInfo]:
        """Go言語の構造体を抽出"""
        structs = []
        
        # Go struct pattern
        struct_pattern = r'type\s+(\w+)\s+struct\s*\{'
        
        for match in re.finditer(struct_pattern, self.content):
            struct_name = match.group(1)
            
            # Extract fields and methods
            fields = self._extract_struct_fields(struct_name)
            methods = self._extract_struct_methods(struct_name)
            
            structs.append(ClassInfo(
                name=struct_name,
                type='struct',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                methods=methods,
                attributes=fields,
                base_classes=[],  # Go doesn't have inheritance
                decorators=[]
            ))
        
        return structs
    
    def extract_functions(self) -> List[FunctionInfo]:
        functions = []
        
        # Go function pattern
        func_pattern = r'func\s+(?:\((?:[^)]+)\)\s+)?(\w+)\s*\(([^)]*)\)(?:\s*\(([^)]*)\))?'
        
        for match in re.finditer(func_pattern, self.content):
            func_name = match.group(1)
            params = match.group(2) if match.group(2) else ''
            returns = match.group(3) if match.group(3) else ''
            
            functions.append(FunctionInfo(
                name=func_name,
                type='function',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                parameters=self._parse_go_parameters(params),
                return_type=returns,
                is_async=False,  # Go uses goroutines, not async
                decorators=[]
            ))
        
        return functions
    
    def extract_imports(self) -> List[ImportInfo]:
        imports = []
        
        # Go import patterns
        single_import = r'import\s+"([^"]+)"'
        multi_import = r'import\s*\(([\s\S]*?)\)'
        
        # Single imports
        for match in re.finditer(single_import, self.content):
            import_path = match.group(1)
            imports.append(ImportInfo(
                name=import_path,
                type='import',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                module=import_path,
                imported_names=[import_path.split('/')[-1]],
                is_from_import=False
            ))
        
        # Multiple imports
        for match in re.finditer(multi_import, self.content):
            import_block = match.group(1)
            for line in import_block.split('\n'):
                line = line.strip()
                if line and line.startswith('"'):
                    import_path = line.strip('"')
                    imports.append(ImportInfo(
                        name=import_path,
                        type='import',
                        file_path=str(self.file_path),
                        line_number=self.content[:match.start()].count('\n') + 1,
                        module=import_path,
                        imported_names=[import_path.split('/')[-1]],
                        is_from_import=False
                    ))
        
        return imports
    
    def _extract_struct_fields(self, struct_name: str) -> List[str]:
        fields = []
        struct_pattern = rf'type\s+{struct_name}\s+struct\s*\{{([^}}]+)\}}'
        
        match = re.search(struct_pattern, self.content, re.DOTALL)
        if match:
            struct_body = match.group(1)
            field_pattern = r'(\w+)\s+(\w+)'
            
            for field_match in re.finditer(field_pattern, struct_body):
                field_name = field_match.group(1)
                field_type = field_match.group(2)
                fields.append(f"{field_name}: {field_type}")
        
        return fields
    
    def _extract_struct_methods(self, struct_name: str) -> List[str]:
        methods = []
        method_pattern = rf'func\s+\(\w+\s+\*?{struct_name}\)\s+(\w+)\s*\('
        
        for match in re.finditer(method_pattern, self.content):
            method_name = match.group(1)
            methods.append(method_name)
        
        return methods
    
    def _parse_go_parameters(self, params_str: str) -> List[str]:
        if not params_str:
            return []
        # Simplified parsing
        return [p.strip() for p in params_str.split(',') if p.strip()]
    
    def _class_to_dict(self, cls: ClassInfo) -> Dict[str, Any]:
        return {
            'name': cls.name,
            'type': 'struct',
            'methods': cls.methods,
            'attributes': cls.attributes,
            'line_number': cls.line_number
        }
    
    def _function_to_dict(self, func: FunctionInfo) -> Dict[str, Any]:
        return {
            'name': func.name,
            'parameters': func.parameters,
            'return_type': func.return_type,
            'line_number': func.line_number
        }
    
    def _import_to_dict(self, imp: ImportInfo) -> Dict[str, Any]:
        return {
            'module': imp.module,
            'imported_names': imp.imported_names,
            'line_number': imp.line_number
        }


class UniversalAnalyzer:
    """
    Claude Code CLIと統合する汎用アナライザー
    すべての言語に対して基本的な構造解析を提供
    """
    
    # 言語ごとの専用アナライザー
    LANGUAGE_ANALYZERS = {
        '.py': PythonAnalyzer,
        '.js': JavaScriptAnalyzer,
        '.jsx': JavaScriptAnalyzer,
        '.ts': JavaScriptAnalyzer,
        '.tsx': JavaScriptAnalyzer,
        '.java': JavaAnalyzer,
        '.go': GoAnalyzer,
        # 今後追加
        # '.cpp': CppAnalyzer,
        # '.c': CAnalyzer,
        # '.rs': RustAnalyzer,
        # '.swift': SwiftAnalyzer,
        # '.php': PhpAnalyzer,
        # '.rb': RubyAnalyzer,
        # '.pas': DelphiAnalyzer,
    }
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.extension = self.file_path.suffix.lower()
        self.analyzer = self._get_analyzer()
    
    def _get_analyzer(self) -> Optional[LanguageAnalyzer]:
        """適切な言語アナライザーを取得"""
        analyzer_class = self.LANGUAGE_ANALYZERS.get(self.extension)
        if analyzer_class:
            return analyzer_class(str(self.file_path))
        else:
            # 未対応言語の場合は汎用解析
            return GenericAnalyzer(str(self.file_path))
    
    def analyze(self) -> Dict[str, Any]:
        """ファイルを解析"""
        if self.analyzer:
            result = self.analyzer.analyze()
            result['language'] = self._detect_language()
            return result
        else:
            return {
                'file_path': str(self.file_path),
                'language': 'unknown',
                'error': f'Unsupported file type: {self.extension}'
            }
    
    def _detect_language(self) -> str:
        """言語を検出"""
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.rs': 'rust',
            '.swift': 'swift',
            '.php': 'php',
            '.rb': 'ruby',
            '.pas': 'delphi',
            '.dpr': 'delphi',
            '.cs': 'csharp',
            '.vb': 'visualbasic',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.m': 'objective-c',
            '.mm': 'objective-c++',
            '.r': 'r',
            '.lua': 'lua',
            '.pl': 'perl',
            '.sh': 'shell',
            '.bat': 'batch',
            '.ps1': 'powershell',
        }
        return language_map.get(self.extension, 'unknown')


class GenericAnalyzer(LanguageAnalyzer):
    """
    未対応言語用の汎用アナライザー
    基本的なパターンマッチングで構造を推測
    """
    
    def analyze(self) -> Dict[str, Any]:
        """汎用的な解析"""
        return {
            'file_path': str(self.file_path),
            'language': 'generic',
            'classes': self._extract_generic_classes(),
            'functions': self._extract_generic_functions(),
            'imports': self._extract_generic_imports(),
            'metadata': {
                'lines': len(self.content.splitlines()),
                'size': len(self.content),
                'extension': self.file_path.suffix
            }
        }
    
    def extract_classes(self) -> List[ClassInfo]:
        return []
    
    def extract_functions(self) -> List[FunctionInfo]:
        return []
    
    def extract_imports(self) -> List[ImportInfo]:
        return []
    
    def _extract_generic_classes(self) -> List[Dict[str, Any]]:
        """汎用的なクラス抽出"""
        classes = []
        
        # Common class patterns
        patterns = [
            r'class\s+(\w+)',  # Most languages
            r'struct\s+(\w+)',  # C/C++/Go
            r'interface\s+(\w+)',  # Java/TypeScript
            r'type\s+(\w+)',  # Various
            r'data\s+(\w+)',  # Haskell
            r'trait\s+(\w+)',  # Rust/Scala
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, self.content):
                name = match.group(1)
                classes.append({
                    'name': name,
                    'line_number': self.content[:match.start()].count('\n') + 1,
                    'type': 'class/struct'
                })
        
        return classes
    
    def _extract_generic_functions(self) -> List[Dict[str, Any]]:
        """汎用的な関数抽出"""
        functions = []
        
        # Common function patterns
        patterns = [
            r'(?:function|func|def|sub|method)\s+(\w+)',
            r'(\w+)\s*\([^)]*\)\s*{',  # C-style
            r'(\w+)\s*::\s*\([^)]*\)',  # Ruby/Perl
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, self.content):
                name = match.group(1)
                if name not in ['if', 'for', 'while', 'switch', 'class', 'struct']:
                    functions.append({
                        'name': name,
                        'line_number': self.content[:match.start()].count('\n') + 1
                    })
        
        return functions
    
    def _extract_generic_imports(self) -> List[Dict[str, Any]]:
        """汎用的なインポート抽出"""
        imports = []
        
        # Common import patterns
        patterns = [
            r'import\s+([^\s;]+)',
            r'require\s*\(?[\'"]([^\'\"]+)[\'"]\)?',
            r'include\s+[<"]([^>"]+)[>"]',
            r'using\s+([^\s;]+)',
            r'use\s+([^\s;]+)',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, self.content):
                module = match.group(1)
                imports.append({
                    'module': module,
                    'line_number': self.content[:match.start()].count('\n') + 1
                })
        
        return imports


class ClaudeCodeCLIIntegration:
    """
    Claude Code CLIとの統合
    ADGコマンドとして実行可能
    """
    
    def __init__(self, project_path: str):
        from adg.core.secure_analyzer import PathValidator, SecurityConfig
        self.project_path = Path(project_path).resolve()
        # セキュリティチェック
        try:
            PathValidator.validate_path(Path.cwd(), self.project_path)
        except Exception as e:
            raise ValueError(f"Invalid project path: {e}")
        self.analyzers = {}
        self.max_files = SecurityConfig.MAX_FILES_TO_PROCESS
        
    def analyze_project(self) -> Dict[str, Any]:
        """
        プロジェクト全体を解析
        Claude Code CLIから呼び出される
        """
        results = {
            'project': str(self.project_path),
            'languages': {},
            'files': {},
            'summary': {
                'total_files': 0,
                'total_classes': 0,
                'total_functions': 0,
                'languages_detected': set()
            }
        }
        
        # すべてのソースファイルを解析
        for file_path in self._get_all_source_files():
            try:
                analyzer = UniversalAnalyzer(str(file_path))
                analysis = analyzer.analyze()
                
                if analysis:
                    language = analysis.get('language', 'unknown')
                    results['files'][str(file_path)] = analysis
                    results['summary']['total_files'] += 1
                    results['summary']['languages_detected'].add(language)
                    
                    # 言語別統計
                    if language not in results['languages']:
                        results['languages'][language] = {
                            'files': 0,
                            'classes': 0,
                            'functions': 0
                        }
                    
                    results['languages'][language]['files'] += 1
                    results['languages'][language]['classes'] += len(analysis.get('classes', []))
                    results['languages'][language]['functions'] += len(analysis.get('functions', []))
                    
                    results['summary']['total_classes'] += len(analysis.get('classes', []))
                    results['summary']['total_functions'] += len(analysis.get('functions', []))
                    
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
                continue
        
        # Set to list for JSON serialization
        results['summary']['languages_detected'] = list(results['summary']['languages_detected'])
        
        return results
    
    def _get_all_source_files(self) -> List[Path]:
        """すべてのソースファイルを取得"""
        source_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go',
            '.cpp', '.cc', '.cxx', '.c', '.h', '.hpp',
            '.rs', '.swift', '.php', '.rb', '.pas', '.dpr',
            '.cs', '.vb', '.kt', '.scala', '.m', '.mm',
            '.r', '.lua', '.pl', '.sh', '.bat', '.ps1',
            '.html', '.css', '.scss', '.sass', '.less',
            '.xml', '.json', '.yaml', '.yml', '.toml',
            '.sql', '.graphql', '.proto'
        }
        
        exclude_dirs = {
            '__pycache__', '.git', '.venv', 'venv', 'node_modules',
            '.pytest_cache', '.mypy_cache', 'dist', 'build',
            'target', 'out', 'bin', 'obj', '.idea', '.vscode'
        }
        
        source_files = []
        
        for ext in source_extensions:
            for file_path in self.project_path.rglob(f"*{ext}"):
                # 除外ディレクトリをチェック
                if any(excluded in str(file_path) for excluded in exclude_dirs):
                    continue
                
                # ファイルサイズチェック（10MB以上は除外）
                try:
                    if file_path.stat().st_size > 10 * 1024 * 1024:
                        logger.warning(f"Skipping large file: {file_path}")
                        continue
                except OSError:
                    continue
                
                source_files.append(file_path)
        
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
        
        return results


# CLIコマンド実装
def main():
    """Claude Code CLIから呼び出されるメインエントリーポイント"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Auto Diagram Generator - Multi-language code analyzer'
    )
    parser.add_argument(
        'path',
        help='Path to analyze',
        default='.'
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
        '--languages',
        nargs='+',
        help='Specific languages to analyze'
    )
    
    args = parser.parse_args()
    
    # 統合アナライザーを実行
    integration = ClaudeCodeCLIIntegration(args.path)
    
    print("🔍 Analyzing project...")
    analysis = integration.analyze_project()
    
    print(f"📊 Found {analysis['summary']['total_files']} files")
    print(f"🌐 Languages: {', '.join(analysis['summary']['languages_detected'])}")
    print(f"📦 Classes: {analysis['summary']['total_classes']}")
    print(f"⚙️ Functions: {analysis['summary']['total_functions']}")
    
    if args.format in ['mermaid', 'drawio', 'all']:
        print("\n🎨 Generating diagrams...")
        diagrams = integration.generate_diagrams(analysis)
        
        for language, paths in diagrams.items():
            print(f"  ✅ {language}: {len(paths.get('drawio', []))} diagrams")
    
    # 結果をJSON出力
    output_file = Path(args.output) / 'analysis_result.json'
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"\n📁 Results saved to: {output_file}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())