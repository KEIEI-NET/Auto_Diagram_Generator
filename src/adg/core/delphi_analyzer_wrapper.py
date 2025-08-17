"""
DelphiAnalyzer wrapper for ProjectAnalyzer compatibility
"""

from pathlib import Path
from typing import Dict, Any
from loguru import logger
from .analyzer import CodeAnalyzer
from .ast_analyzers import DelphiAnalyzer as ASTDelphiAnalyzer


class DelphiAnalyzer(CodeAnalyzer):
    """Delphi/Pascal code analyzer wrapper"""
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze Delphi/Pascal code"""
        try:
            # ASTベースのDelphiAnalyzerを使用（file_pathが必要）
            ast_analyzer = ASTDelphiAnalyzer(str(self.file_path))
            
            # parse_astは引数を取らない - contentはコンストラクタで渡される
            tree = ast_analyzer.parse_ast()
            
            # ASTから情報を抽出
            result = ast_analyzer.extract_from_ast(tree) if tree else {}
            
            # ProjectAnalyzerが期待する形式に変換
            return self._convert_to_standard_format(result)
            
        except Exception as e:
            logger.error(f"Failed to analyze Delphi file {self.file_path}: {e}")
            return {
                "error": str(e),
                "classes": [],
                "functions": [],
                "imports": [],
                "variables": []
            }
    
    def _convert_to_standard_format(self, ast_result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert AST result to standard format"""
        
        # 標準フォーマットに変換
        standard_format = {
            "classes": [],
            "functions": [],
            "imports": [],
            "variables": [],
            "metadata": {}
        }
        
        # クラス情報の変換
        if "classes" in ast_result:
            for cls in ast_result["classes"]:
                class_info = {
                    "name": cls.get("name", ""),
                    "methods": cls.get("methods", []),
                    "attributes": cls.get("properties", []),
                    "base_classes": cls.get("base_classes", []),
                    "line_number": cls.get("line_number", 0)
                }
                standard_format["classes"].append(class_info)
        
        # 関数/プロシージャの変換
        if "functions" in ast_result:
            for func in ast_result["functions"]:
                func_info = {
                    "name": func.get("name", ""),
                    "parameters": func.get("parameters", []),
                    "return_type": func.get("return_type", None),
                    "line_number": func.get("line_number", 0)
                }
                standard_format["functions"].append(func_info)
        
        # プロシージャも関数として追加
        if "procedures" in ast_result:
            for proc in ast_result["procedures"]:
                proc_info = {
                    "name": proc.get("name", ""),
                    "parameters": proc.get("parameters", []),
                    "return_type": None,  # プロシージャは戻り値なし
                    "line_number": proc.get("line_number", 0)
                }
                standard_format["functions"].append(proc_info)
        
        # インポート（uses）の変換
        if "uses" in ast_result:
            for unit in ast_result["uses"]:
                import_info = {
                    "module": unit,
                    "imported_names": [],
                    "is_from_import": False
                }
                standard_format["imports"].append(import_info)
        
        # 変数の変換
        if "variables" in ast_result:
            standard_format["variables"] = ast_result["variables"]
        
        # メタデータ
        if "metadata" in ast_result:
            standard_format["metadata"] = ast_result["metadata"]
        
        return standard_format