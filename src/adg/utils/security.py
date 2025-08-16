"""
セキュリティ関連のユーティリティ
パス検証、入力サニタイゼーション等
"""

import os
from pathlib import Path
from typing import Optional, Union
import re


class PathSecurityError(Exception):
    """パスセキュリティエラー"""
    pass


def validate_path(path: Union[str, Path], base_dir: Optional[Path] = None) -> Path:
    """
    パスの安全性を検証
    
    Args:
        path: 検証するパス
        base_dir: ベースディレクトリ（指定時はこの配下のみ許可）
    
    Returns:
        検証済みの安全なパス
        
    Raises:
        PathSecurityError: 危険なパスの場合
    """
    # Pathオブジェクトに変換
    if isinstance(path, str):
        path = Path(path)
    
    # 絶対パスに解決
    try:
        resolved_path = path.resolve(strict=False)
    except (OSError, RuntimeError) as e:
        raise PathSecurityError(f"パスの解決に失敗: {e}")
    
    # パストラバーサル攻撃のチェック
    if ".." in str(path):
        raise PathSecurityError("パストラバーサル攻撃の可能性があります")
    
    # NULLバイトインジェクションのチェック
    if "\x00" in str(path):
        raise PathSecurityError("NULLバイトが含まれています")
    
    # シンボリックリンクのチェック
    if resolved_path.exists() and resolved_path.is_symlink():
        # シンボリックリンクの場合、リンク先を検証
        try:
            real_path = resolved_path.resolve(strict=True)
        except (OSError, RuntimeError) as e:
            raise PathSecurityError(f"シンボリックリンクの解決に失敗: {e}")
    else:
        real_path = resolved_path
    
    # ベースディレクトリの制限チェック
    if base_dir:
        base_dir = Path(base_dir).resolve()
        try:
            real_path.relative_to(base_dir)
        except ValueError:
            raise PathSecurityError(
                f"パスがベースディレクトリ外を参照しています: {real_path}"
            )
    
    # 危険な文字のチェック
    dangerous_chars = ['<', '>', '|', '&', ';', '$', '`', '\\n', '\\r']
    path_str = str(real_path)
    for char in dangerous_chars:
        if char in path_str:
            raise PathSecurityError(f"危険な文字が含まれています: {char}")
    
    return real_path


def sanitize_filename(filename: str) -> str:
    """
    ファイル名をサニタイズ
    
    Args:
        filename: サニタイズするファイル名
        
    Returns:
        安全なファイル名
    """
    # 危険な文字を除去または置換
    # Windowsで禁止されている文字も考慮
    forbidden_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(forbidden_chars, '_', filename)
    
    # 先頭・末尾の空白とドットを削除
    sanitized = sanitized.strip('. ')
    
    # Windowsの予約語をチェック
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    name_without_ext = sanitized.split('.')[0].upper()
    if name_without_ext in reserved_names:
        sanitized = f"_{sanitized}"
    
    # 最大長の制限（255文字）
    if len(sanitized) > 255:
        # 拡張子を保持しつつ切り詰め
        name, ext = os.path.splitext(sanitized)
        max_name_len = 255 - len(ext)
        sanitized = name[:max_name_len] + ext
    
    # 空文字列の場合はデフォルト名
    if not sanitized:
        sanitized = "unnamed"
    
    return sanitized


def is_safe_import(module_name: str) -> bool:
    """
    インポートするモジュール名の安全性をチェック
    
    Args:
        module_name: モジュール名
        
    Returns:
        安全な場合True
    """
    # 基本的な検証
    if not module_name:
        return False
    
    # 危険なモジュールのブラックリスト
    dangerous_modules = [
        'os', 'sys', 'subprocess', 'eval', 'exec',
        'compile', '__import__', 'open', 'input',
        'raw_input', 'file'
    ]
    
    # トップレベルモジュール名を取得
    top_module = module_name.split('.')[0]
    
    if top_module in dangerous_modules:
        return False
    
    # 不正な文字のチェック
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*$', module_name):
        return False
    
    return True


def validate_file_size(file_path: Path, max_size_mb: float = 100) -> bool:
    """
    ファイルサイズの検証
    
    Args:
        file_path: 検証するファイルパス
        max_size_mb: 最大サイズ（MB）
        
    Returns:
        サイズが制限内の場合True
    """
    if not file_path.exists():
        return True  # 存在しないファイルは作成可能とする
    
    try:
        size_bytes = file_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        return size_mb <= max_size_mb
    except (OSError, IOError):
        return False