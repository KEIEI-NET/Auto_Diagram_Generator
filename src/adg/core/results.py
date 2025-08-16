"""
統一的な結果型の定義
エラーハンドリングの一貫性を保証
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional, TypeVar, Generic
from enum import Enum


class ErrorType(Enum):
    """エラーの種類"""
    SYNTAX_ERROR = "syntax_error"
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_ERROR = "permission_error"
    VALIDATION_ERROR = "validation_error"
    ANALYSIS_ERROR = "analysis_error"
    GENERATION_ERROR = "generation_error"
    UNKNOWN_ERROR = "unknown_error"


T = TypeVar('T')


@dataclass
class Result(Generic[T]):
    """
    統一的な結果型
    成功/失敗を明示的に表現
    """
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    error_type: Optional[ErrorType] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        
        # 一貫性チェック
        if self.success and self.error:
            raise ValueError("成功時にエラーは設定できません")
        if not self.success and not self.error:
            self.error = "不明なエラー"
            self.error_type = ErrorType.UNKNOWN_ERROR
    
    @classmethod
    def ok(cls, data: T, warnings: List[str] = None) -> 'Result[T]':
        """成功結果を作成"""
        return cls(success=True, data=data, warnings=warnings)
    
    @classmethod
    def err(cls, error: str, error_type: ErrorType = ErrorType.UNKNOWN_ERROR) -> 'Result[T]':
        """エラー結果を作成"""
        return cls(success=False, error=error, error_type=error_type)
    
    def unwrap(self) -> T:
        """データを取得（失敗時は例外）"""
        if not self.success:
            raise ValueError(f"Result is error: {self.error}")
        return self.data
    
    def unwrap_or(self, default: T) -> T:
        """データを取得（失敗時はデフォルト値）"""
        return self.data if self.success else default
    
    def map(self, func) -> 'Result':
        """成功時のみ関数を適用"""
        if self.success:
            try:
                new_data = func(self.data)
                return Result.ok(new_data, self.warnings)
            except Exception as e:
                return Result.err(str(e), ErrorType.UNKNOWN_ERROR)
        return self


@dataclass
class AnalysisResult:
    """コード解析結果の統一型"""
    file_path: str
    classes: List[Dict[str, Any]]
    functions: List[Dict[str, Any]]
    imports: List[Dict[str, Any]]
    variables: List[Dict[str, Any]]
    errors: List[Dict[str, str]]
    warnings: List[str]
    
    @classmethod
    def empty(cls, file_path: str) -> 'AnalysisResult':
        """空の結果を作成"""
        return cls(
            file_path=file_path,
            classes=[],
            functions=[],
            imports=[],
            variables=[],
            errors=[],
            warnings=[]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'file_path': self.file_path,
            'classes': self.classes,
            'functions': self.functions,
            'imports': self.imports,
            'variables': self.variables,
            'errors': self.errors,
            'warnings': self.warnings
        }


@dataclass
class DiagramResult:
    """図生成結果の統一型"""
    diagram_type: str
    file_path: Optional[str]
    content: Optional[str]
    format: str
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @classmethod
    def success_result(
        cls,
        diagram_type: str,
        file_path: str,
        format: str,
        content: str = None,
        metadata: Dict[str, Any] = None
    ) -> 'DiagramResult':
        """成功結果を作成"""
        return cls(
            diagram_type=diagram_type,
            file_path=file_path,
            content=content,
            format=format,
            success=True,
            metadata=metadata
        )
    
    @classmethod
    def error_result(
        cls,
        diagram_type: str,
        format: str,
        error: str
    ) -> 'DiagramResult':
        """エラー結果を作成"""
        return cls(
            diagram_type=diagram_type,
            file_path=None,
            content=None,
            format=format,
            success=False,
            error=error
        )