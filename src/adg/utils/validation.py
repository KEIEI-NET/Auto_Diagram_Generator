"""
型安全性とバリデーション関数
"""

from typing import Any, Dict, List, Union, TypeGuard
from loguru import logger


def is_valid_dict(obj: Any) -> TypeGuard[Dict[str, Any]]:
    """オブジェクトが有効な辞書かチェック"""
    return isinstance(obj, dict)


def is_valid_list(obj: Any) -> TypeGuard[List[Any]]:
    """オブジェクトが有効なリストかチェック"""
    return isinstance(obj, list)


def is_valid_string(obj: Any) -> TypeGuard[str]:
    """オブジェクトが有効な文字列かチェック"""
    return isinstance(obj, str) and len(obj.strip()) > 0


def is_valid_identifier(name: str) -> bool:
    """有効なPython識別子かチェック"""
    return name.isidentifier() and not name.startswith('__')


def safe_get_dict_value(
    data: Dict[str, Any], 
    key: str, 
    default: Any = None,
    expected_type: type = None
) -> Any:
    """辞書から安全に値を取得"""
    try:
        value = data.get(key, default)
        if expected_type and not isinstance(value, expected_type):
            logger.warning(f"Expected {expected_type.__name__} for key '{key}', got {type(value).__name__}")
            return default
        return value
    except Exception as e:
        logger.error(f"Error getting key '{key}': {e}")
        return default


def validate_analysis_structure(analysis: Dict[str, Any]) -> bool:
    """解析結果の構造を検証"""
    try:
        # 必須キーの存在確認
        required_keys = ['classes', 'functions', 'imports']
        for key in required_keys:
            if key not in analysis:
                logger.error(f"Missing required key: {key}")
                return False
            
            if not isinstance(analysis[key], list):
                logger.error(f"Key '{key}' must be a list")
                return False
        
        return True
    except Exception as e:
        logger.error(f"Analysis structure validation error: {e}")
        return False


def sanitize_mermaid_text(text: str) -> str:
    """Mermaidで安全に使える文字列に変換"""
    if not isinstance(text, str):
        return "Invalid"
    
    # 特殊文字を除去
    sanitized = ''.join(c for c in text if c.isalnum() or c in '_-')
    
    # 空の場合はデフォルト値を返す
    if not sanitized:
        return "Unknown"
    
    return sanitized[:50]  # 長さ制限