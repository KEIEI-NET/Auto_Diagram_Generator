"""
追加言語パーサー実装
C++, Rust, Swift, PHP, Ruby, C#等の対応
"""

import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from loguru import logger

from adg.core.multi_language_analyzer import LanguageAnalyzer, ClassInfo, FunctionInfo, ImportInfo


class CppAnalyzer(LanguageAnalyzer):
    """C++用アナライザー"""
    
    def analyze(self) -> Dict[str, Any]:
        classes = self.extract_classes()
        functions = self.extract_functions()
        imports = self.extract_imports()
        
        return {
            'file_path': str(self.file_path),
            'language': 'cpp',
            'classes': [self._class_to_dict(c) for c in classes],
            'functions': [self._function_to_dict(f) for f in functions],
            'imports': [self._import_to_dict(i) for i in imports],
        }
    
    def extract_classes(self) -> List[ClassInfo]:
        classes = []
        
        # C++ class/struct pattern
        class_pattern = r'(?:class|struct)\s+(\w+)(?:\s*:\s*(?:public|private|protected)?\s*(\w+))?'
        
        for match in re.finditer(class_pattern, self.content):
            class_name = match.group(1)
            base_class = match.group(2) if match.group(2) else None
            
            # Extract members
            methods = self._extract_class_methods(class_name)
            attributes = self._extract_class_attributes(class_name)
            
            classes.append(ClassInfo(
                name=class_name,
                type='class',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                methods=methods,
                attributes=attributes,
                base_classes=[base_class] if base_class else [],
                decorators=[]
            ))
        
        return classes
    
    def extract_functions(self) -> List[FunctionInfo]:
        functions = []
        
        # C++ function pattern (simplified)
        func_pattern = r'(?:inline|static|virtual|const)?\s*(\w+[\s*&]*)\s+(\w+)\s*\(([^)]*)\)'
        
        for match in re.finditer(func_pattern, self.content):
            return_type = match.group(1)
            func_name = match.group(2)
            params = match.group(3)
            
            # Skip keywords and constructors
            if return_type in ['if', 'for', 'while', 'switch', 'class', 'struct']:
                continue
            
            functions.append(FunctionInfo(
                name=func_name,
                type='function',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                parameters=self._parse_parameters(params),
                return_type=return_type,
                is_async=False,
                decorators=[]
            ))
        
        return functions
    
    def extract_imports(self) -> List[ImportInfo]:
        imports = []
        
        # C++ include patterns
        include_patterns = [
            r'#include\s*<([^>]+)>',
            r'#include\s*"([^"]+)"',
        ]
        
        for pattern in include_patterns:
            for match in re.finditer(pattern, self.content):
                header = match.group(1)
                imports.append(ImportInfo(
                    name=header,
                    type='include',
                    file_path=str(self.file_path),
                    line_number=self.content[:match.start()].count('\n') + 1,
                    module=header,
                    imported_names=[],
                    is_from_import=False
                ))
        
        # Using namespace
        namespace_pattern = r'using\s+namespace\s+(\w+);'
        for match in re.finditer(namespace_pattern, self.content):
            namespace = match.group(1)
            imports.append(ImportInfo(
                name=namespace,
                type='namespace',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                module=namespace,
                imported_names=[],
                is_from_import=False
            ))
        
        return imports
    
    def _extract_class_methods(self, class_name: str) -> List[str]:
        methods = []
        # Simplified method extraction
        method_pattern = r'(?:public|private|protected):\s*(?:virtual|static)?\s*\w+[\s*&]*\s+(\w+)\s*\('
        
        for match in re.finditer(method_pattern, self.content):
            method_name = match.group(1)
            if method_name != class_name:  # Skip constructors
                methods.append(method_name)
        
        return methods
    
    def _extract_class_attributes(self, class_name: str) -> List[str]:
        attributes = []
        # Simplified attribute extraction
        attr_pattern = r'(?:public|private|protected):\s*(\w+[\s*&]*)\s+(\w+);'
        
        for match in re.finditer(attr_pattern, self.content):
            attr_type = match.group(1)
            attr_name = match.group(2)
            attributes.append(f"{attr_name}: {attr_type}")
        
        return attributes
    
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
            'type': imp.type,
            'line_number': imp.line_number
        }


class RustAnalyzer(LanguageAnalyzer):
    """Rust用アナライザー"""
    
    def analyze(self) -> Dict[str, Any]:
        classes = self.extract_classes()  # structs and traits
        functions = self.extract_functions()
        imports = self.extract_imports()
        
        return {
            'file_path': str(self.file_path),
            'language': 'rust',
            'classes': [self._class_to_dict(c) for c in classes],
            'functions': [self._function_to_dict(f) for f in functions],
            'imports': [self._import_to_dict(i) for i in imports],
        }
    
    def extract_classes(self) -> List[ClassInfo]:
        classes = []
        
        # Rust struct pattern
        struct_pattern = r'(?:pub\s+)?struct\s+(\w+)(?:<[^>]+>)?'
        
        for match in re.finditer(struct_pattern, self.content):
            struct_name = match.group(1)
            
            # Extract fields and methods
            fields = self._extract_struct_fields(struct_name)
            methods = self._extract_impl_methods(struct_name)
            
            classes.append(ClassInfo(
                name=struct_name,
                type='struct',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                methods=methods,
                attributes=fields,
                base_classes=[],
                decorators=self._extract_derives(match.start())
            ))
        
        # Rust trait pattern
        trait_pattern = r'(?:pub\s+)?trait\s+(\w+)'
        
        for match in re.finditer(trait_pattern, self.content):
            trait_name = match.group(1)
            
            classes.append(ClassInfo(
                name=trait_name,
                type='trait',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                methods=self._extract_trait_methods(trait_name),
                attributes=[],
                base_classes=[],
                decorators=[]
            ))
        
        return classes
    
    def extract_functions(self) -> List[FunctionInfo]:
        functions = []
        
        # Rust function pattern
        func_pattern = r'(?:pub\s+)?(?:async\s+)?fn\s+(\w+)(?:<[^>]+>)?\s*\(([^)]*)\)(?:\s*->\s*([^\s{]+))?'
        
        for match in re.finditer(func_pattern, self.content):
            func_name = match.group(1)
            params = match.group(2) if match.group(2) else ''
            return_type = match.group(3) if match.group(3) else '()'
            
            is_async = 'async fn' in self.content[max(0, match.start()-10):match.start()+10]
            
            functions.append(FunctionInfo(
                name=func_name,
                type='function',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                parameters=self._parse_rust_parameters(params),
                return_type=return_type,
                is_async=is_async,
                decorators=[]
            ))
        
        return functions
    
    def extract_imports(self) -> List[ImportInfo]:
        imports = []
        
        # Rust use statements
        use_pattern = r'use\s+([^;]+);'
        
        for match in re.finditer(use_pattern, self.content):
            import_path = match.group(1)
            
            imports.append(ImportInfo(
                name=import_path,
                type='use',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                module=import_path,
                imported_names=self._extract_imported_items(import_path),
                is_from_import=True
            ))
        
        return imports
    
    def _extract_struct_fields(self, struct_name: str) -> List[str]:
        fields = []
        struct_pattern = rf'struct\s+{struct_name}\s*\{{([^}}]+)\}}'
        
        match = re.search(struct_pattern, self.content, re.DOTALL)
        if match:
            struct_body = match.group(1)
            field_pattern = r'(?:pub\s+)?(\w+)\s*:\s*([^,\n]+)'
            
            for field_match in re.finditer(field_pattern, struct_body):
                field_name = field_match.group(1)
                field_type = field_match.group(2).strip()
                fields.append(f"{field_name}: {field_type}")
        
        return fields
    
    def _extract_impl_methods(self, struct_name: str) -> List[str]:
        methods = []
        impl_pattern = rf'impl(?:<[^>]+>)?\s+{struct_name}(?:<[^>]+>)?\s*\{{([^}}]+)\}}'
        
        match = re.search(impl_pattern, self.content, re.DOTALL)
        if match:
            impl_body = match.group(1)
            method_pattern = r'(?:pub\s+)?fn\s+(\w+)'
            
            for method_match in re.finditer(method_pattern, impl_body):
                method_name = method_match.group(1)
                methods.append(method_name)
        
        return methods
    
    def _extract_trait_methods(self, trait_name: str) -> List[str]:
        methods = []
        trait_pattern = rf'trait\s+{trait_name}\s*\{{([^}}]+)\}}'
        
        match = re.search(trait_pattern, self.content, re.DOTALL)
        if match:
            trait_body = match.group(1)
            method_pattern = r'fn\s+(\w+)'
            
            for method_match in re.finditer(method_pattern, trait_body):
                method_name = method_match.group(1)
                methods.append(method_name)
        
        return methods
    
    def _extract_derives(self, position: int) -> List[str]:
        derives = []
        # Look for #[derive(...)] before the struct
        before_text = self.content[max(0, position-200):position]
        derive_pattern = r'#\[derive\(([^)]+)\)\]'
        
        for match in re.finditer(derive_pattern, before_text):
            derive_list = match.group(1)
            derives.extend([d.strip() for d in derive_list.split(',')])
        
        return derives
    
    def _extract_imported_items(self, import_path: str) -> List[str]:
        # Extract items from use statements like use std::collections::{HashMap, HashSet}
        if '{' in import_path and '}' in import_path:
            match = re.search(r'\{([^}]+)\}', import_path)
            if match:
                return [item.strip() for item in match.group(1).split(',')]
        
        # Single item import
        parts = import_path.split('::')
        return [parts[-1]] if parts else []
    
    def _parse_rust_parameters(self, params_str: str) -> List[str]:
        if not params_str:
            return []
        # Handle self parameter
        params = []
        for param in params_str.split(','):
            param = param.strip()
            if param and param != 'self' and param != '&self' and param != '&mut self':
                params.append(param)
        return params
    
    def _class_to_dict(self, cls: ClassInfo) -> Dict[str, Any]:
        return {
            'name': cls.name,
            'type': cls.type,
            'methods': cls.methods,
            'attributes': cls.attributes,
            'decorators': cls.decorators,
            'line_number': cls.line_number
        }
    
    def _function_to_dict(self, func: FunctionInfo) -> Dict[str, Any]:
        return {
            'name': func.name,
            'parameters': func.parameters,
            'return_type': func.return_type,
            'is_async': func.is_async,
            'line_number': func.line_number
        }
    
    def _import_to_dict(self, imp: ImportInfo) -> Dict[str, Any]:
        return {
            'module': imp.module,
            'imported_names': imp.imported_names,
            'line_number': imp.line_number
        }


class PhpAnalyzer(LanguageAnalyzer):
    """PHP用アナライザー"""
    
    def analyze(self) -> Dict[str, Any]:
        classes = self.extract_classes()
        functions = self.extract_functions()
        imports = self.extract_imports()
        
        return {
            'file_path': str(self.file_path),
            'language': 'php',
            'classes': [self._class_to_dict(c) for c in classes],
            'functions': [self._function_to_dict(f) for f in functions],
            'imports': [self._import_to_dict(i) for i in imports],
        }
    
    def extract_classes(self) -> List[ClassInfo]:
        classes = []
        
        # PHP class pattern
        class_pattern = r'(?:abstract\s+|final\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?'
        
        for match in re.finditer(class_pattern, self.content):
            class_name = match.group(1)
            base_class = match.group(2)
            interfaces = match.group(3)
            
            # Extract methods and properties
            methods = self._extract_class_methods(class_name)
            properties = self._extract_class_properties(class_name)
            
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
                attributes=properties,
                base_classes=base_classes,
                decorators=[]
            ))
        
        return classes
    
    def extract_functions(self) -> List[FunctionInfo]:
        functions = []
        
        # PHP function pattern
        func_pattern = r'(?:public|private|protected|static)?\s*function\s+(\w+)\s*\(([^)]*)\)'
        
        for match in re.finditer(func_pattern, self.content):
            func_name = match.group(1)
            params = match.group(2) if match.group(2) else ''
            
            functions.append(FunctionInfo(
                name=func_name,
                type='function',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                parameters=self._parse_php_parameters(params),
                return_type=None,
                is_async=False,
                decorators=[]
            ))
        
        return functions
    
    def extract_imports(self) -> List[ImportInfo]:
        imports = []
        
        # PHP use statements
        use_pattern = r'use\s+([^;]+);'
        
        for match in re.finditer(use_pattern, self.content):
            import_path = match.group(1)
            
            # Handle aliasing
            if ' as ' in import_path:
                import_path, alias = import_path.split(' as ')
                import_path = import_path.strip()
                alias = alias.strip()
            else:
                alias = import_path.split('\\')[-1]
            
            imports.append(ImportInfo(
                name=import_path,
                type='use',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                module=import_path,
                imported_names=[alias],
                is_from_import=True
            ))
        
        # PHP require/include
        require_pattern = r'(?:require|include)(?:_once)?\s*[\'"]([^\'"]+)[\'"]'
        
        for match in re.finditer(require_pattern, self.content):
            file_path = match.group(1)
            
            imports.append(ImportInfo(
                name=file_path,
                type='require',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                module=file_path,
                imported_names=[],
                is_from_import=False
            ))
        
        return imports
    
    def _extract_class_methods(self, class_name: str) -> List[str]:
        methods = []
        method_pattern = r'(?:public|private|protected)?\s*(?:static)?\s*function\s+(\w+)'
        
        for match in re.finditer(method_pattern, self.content):
            method_name = match.group(1)
            if method_name != '__construct' and method_name != '__destruct':
                methods.append(method_name)
        
        return methods
    
    def _extract_class_properties(self, class_name: str) -> List[str]:
        properties = []
        property_pattern = r'(?:public|private|protected)\s+(?:static\s+)?\$(\w+)'
        
        for match in re.finditer(property_pattern, self.content):
            property_name = match.group(1)
            properties.append(f"${property_name}")
        
        return properties
    
    def _parse_php_parameters(self, params_str: str) -> List[str]:
        if not params_str:
            return []
        
        params = []
        for param in params_str.split(','):
            param = param.strip()
            if param:
                # Remove type hints and default values for simplicity
                if '$' in param:
                    param_name = param[param.index('$'):].split('=')[0].strip()
                    params.append(param_name)
        
        return params
    
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
            'line_number': func.line_number
        }
    
    def _import_to_dict(self, imp: ImportInfo) -> Dict[str, Any]:
        return {
            'module': imp.module,
            'imported_names': imp.imported_names,
            'type': imp.type,
            'line_number': imp.line_number
        }


class RubyAnalyzer(LanguageAnalyzer):
    """Ruby用アナライザー"""
    
    def analyze(self) -> Dict[str, Any]:
        classes = self.extract_classes()
        functions = self.extract_functions()
        imports = self.extract_imports()
        
        return {
            'file_path': str(self.file_path),
            'language': 'ruby',
            'classes': [self._class_to_dict(c) for c in classes],
            'functions': [self._function_to_dict(f) for f in functions],
            'imports': [self._import_to_dict(i) for i in imports],
        }
    
    def extract_classes(self) -> List[ClassInfo]:
        classes = []
        
        # Ruby class pattern
        class_pattern = r'class\s+(\w+)(?:\s*<\s*(\w+))?'
        
        for match in re.finditer(class_pattern, self.content):
            class_name = match.group(1)
            base_class = match.group(2) if match.group(2) else None
            
            # Extract methods
            methods = self._extract_class_methods(class_name)
            attributes = self._extract_class_attributes(class_name)
            
            classes.append(ClassInfo(
                name=class_name,
                type='class',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                methods=methods,
                attributes=attributes,
                base_classes=[base_class] if base_class else [],
                decorators=[]
            ))
        
        # Ruby module pattern
        module_pattern = r'module\s+(\w+)'
        
        for match in re.finditer(module_pattern, self.content):
            module_name = match.group(1)
            
            classes.append(ClassInfo(
                name=module_name,
                type='module',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                methods=self._extract_module_methods(module_name),
                attributes=[],
                base_classes=[],
                decorators=[]
            ))
        
        return classes
    
    def extract_functions(self) -> List[FunctionInfo]:
        functions = []
        
        # Ruby method pattern
        method_pattern = r'def\s+(?:self\.)?(\w+)(?:\(([^)]*)\))?'
        
        for match in re.finditer(method_pattern, self.content):
            method_name = match.group(1)
            params = match.group(2) if match.group(2) else ''
            
            functions.append(FunctionInfo(
                name=method_name,
                type='method',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                parameters=self._parse_ruby_parameters(params),
                return_type=None,
                is_async=False,
                decorators=[]
            ))
        
        return functions
    
    def extract_imports(self) -> List[ImportInfo]:
        imports = []
        
        # Ruby require/require_relative
        require_patterns = [
            r'require\s+[\'"]([^\'"]+)[\'"]',
            r'require_relative\s+[\'"]([^\'"]+)[\'"]',
        ]
        
        for pattern in require_patterns:
            for match in re.finditer(pattern, self.content):
                import_path = match.group(1)
                
                imports.append(ImportInfo(
                    name=import_path,
                    type='require',
                    file_path=str(self.file_path),
                    line_number=self.content[:match.start()].count('\n') + 1,
                    module=import_path,
                    imported_names=[],
                    is_from_import=False
                ))
        
        # Ruby include/extend
        include_pattern = r'(?:include|extend)\s+(\w+)'
        
        for match in re.finditer(include_pattern, self.content):
            module_name = match.group(1)
            
            imports.append(ImportInfo(
                name=module_name,
                type='include',
                file_path=str(self.file_path),
                line_number=self.content[:match.start()].count('\n') + 1,
                module=module_name,
                imported_names=[],
                is_from_import=False
            ))
        
        return imports
    
    def _extract_class_methods(self, class_name: str) -> List[str]:
        methods = []
        # Find methods within class
        class_pattern = rf'class\s+{class_name}[^{{]*\n(.*?)(?:^class\s+|\Z)'
        
        match = re.search(class_pattern, self.content, re.MULTILINE | re.DOTALL)
        if match:
            class_body = match.group(1)
            method_pattern = r'def\s+(\w+)'
            
            for method_match in re.finditer(method_pattern, class_body):
                method_name = method_match.group(1)
                methods.append(method_name)
        
        return methods
    
    def _extract_module_methods(self, module_name: str) -> List[str]:
        methods = []
        module_pattern = rf'module\s+{module_name}[^{{]*\n(.*?)(?:^module\s+|\Z)'
        
        match = re.search(module_pattern, self.content, re.MULTILINE | re.DOTALL)
        if match:
            module_body = match.group(1)
            method_pattern = r'def\s+(?:self\.)?(\w+)'
            
            for method_match in re.finditer(method_pattern, module_body):
                method_name = method_match.group(1)
                methods.append(method_name)
        
        return methods
    
    def _extract_class_attributes(self, class_name: str) -> List[str]:
        attributes = []
        # Ruby attr_accessor, attr_reader, attr_writer
        attr_pattern = r'attr_(?:accessor|reader|writer)\s+:(\w+)'
        
        for match in re.finditer(attr_pattern, self.content):
            attr_name = match.group(1)
            attributes.append(f"@{attr_name}")
        
        # Instance variables
        ivar_pattern = r'@(\w+)\s*='
        
        for match in re.finditer(ivar_pattern, self.content):
            var_name = match.group(1)
            if f"@{var_name}" not in attributes:
                attributes.append(f"@{var_name}")
        
        return attributes
    
    def _parse_ruby_parameters(self, params_str: str) -> List[str]:
        if not params_str:
            return []
        
        params = []
        for param in params_str.split(','):
            param = param.strip()
            if param:
                # Remove default values
                param = param.split('=')[0].strip()
                params.append(param)
        
        return params
    
    def _class_to_dict(self, cls: ClassInfo) -> Dict[str, Any]:
        return {
            'name': cls.name,
            'type': cls.type,
            'methods': cls.methods,
            'attributes': cls.attributes,
            'base_classes': cls.base_classes,
            'line_number': cls.line_number
        }
    
    def _function_to_dict(self, func: FunctionInfo) -> Dict[str, Any]:
        return {
            'name': func.name,
            'parameters': func.parameters,
            'line_number': func.line_number
        }
    
    def _import_to_dict(self, imp: ImportInfo) -> Dict[str, Any]:
        return {
            'module': imp.module,
            'type': imp.type,
            'line_number': imp.line_number
        }


# 言語アナライザーの登録
ADDITIONAL_ANALYZERS = {
    '.cpp': CppAnalyzer,
    '.cc': CppAnalyzer,
    '.cxx': CppAnalyzer,
    '.hpp': CppAnalyzer,
    '.h': CppAnalyzer,
    '.rs': RustAnalyzer,
    '.php': PhpAnalyzer,
    '.rb': RubyAnalyzer,
    # 今後追加
    # '.swift': SwiftAnalyzer,
    # '.cs': CSharpAnalyzer,
    # '.kt': KotlinAnalyzer,
    # '.scala': ScalaAnalyzer,
    # '.pas': DelphiAnalyzer,
    # '.dpr': DelphiAnalyzer,
}