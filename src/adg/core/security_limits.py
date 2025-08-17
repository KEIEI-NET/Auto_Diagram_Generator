"""
セキュリティ制限とリソース保護機能
AST解析時のタイムアウト、メモリ制限、深度制限を提供
"""

import signal
import threading
import time
import psutil
from contextlib import contextmanager
from typing import Optional, Callable, Any
from functools import wraps
from loguru import logger
import sys
import os

# Windows/Unix互換性のためのインポート
# Windows環境ではwin32apiの代わりにthreadingを使用
if sys.platform != 'win32':
    import resource


class SecurityLimits:
    """セキュリティ制限の設定"""
    
    # デフォルト制限値
    DEFAULT_PARSE_TIMEOUT = 5  # パース処理のタイムアウト（秒）
    DEFAULT_TRAVERSE_TIMEOUT = 10  # traversal処理のタイムアウト（秒）
    DEFAULT_MAX_DEPTH = 100  # AST最大深度
    DEFAULT_MAX_MEMORY_MB = 500  # 最大メモリ使用量（MB）
    DEFAULT_MAX_FILE_SIZE_MB = 50  # 最大ファイルサイズ（MB）
    DEFAULT_MAX_NODES = 100000  # 最大ノード数
    
    # 調整可能な制限値
    parse_timeout = DEFAULT_PARSE_TIMEOUT
    traverse_timeout = DEFAULT_TRAVERSE_TIMEOUT
    max_depth = DEFAULT_MAX_DEPTH
    max_memory_mb = DEFAULT_MAX_MEMORY_MB
    max_file_size_mb = DEFAULT_MAX_FILE_SIZE_MB
    max_nodes = DEFAULT_MAX_NODES


class TimeoutError(Exception):
    """タイムアウトエラー"""
    pass


class ResourceLimitError(Exception):
    """リソース制限エラー"""
    pass


class DepthLimitError(Exception):
    """深度制限エラー"""
    pass


@contextmanager
def timeout(seconds: int, error_message: str = "Operation timed out"):
    """
    Unix/Linux用のタイムアウトコンテキストマネージャー
    Windowsでは threading.Timer を使用
    """
    if sys.platform == 'win32':
        # Windows用の実装
        timer = None
        timed_out = threading.Event()
        
        def timeout_handler():
            timed_out.set()
            logger.error(f"Timeout after {seconds} seconds: {error_message}")
        
        try:
            timer = threading.Timer(seconds, timeout_handler)
            timer.start()
            yield timed_out
        finally:
            if timer:
                timer.cancel()
            if timed_out.is_set():
                raise TimeoutError(error_message)
    else:
        # Unix/Linux用の実装
        def signal_handler(signum, frame):
            raise TimeoutError(error_message)
        
        # SIGALRMハンドラを設定
        old_handler = signal.signal(signal.SIGALRM, signal_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)


def with_timeout(seconds: Optional[int] = None):
    """
    関数にタイムアウトを適用するデコレータ
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            timeout_sec = seconds or SecurityLimits.parse_timeout
            
            if sys.platform == 'win32':
                # Windows: スレッドベースのタイムアウト
                result = [None]
                exception = [None]
                
                def target():
                    try:
                        result[0] = func(*args, **kwargs)
                    except Exception as e:
                        exception[0] = e
                
                thread = threading.Thread(target=target)
                thread.daemon = True
                thread.start()
                thread.join(timeout_sec)
                
                if thread.is_alive():
                    logger.error(f"Function {func.__name__} timed out after {timeout_sec} seconds")
                    raise TimeoutError(f"{func.__name__} timed out")
                
                if exception[0]:
                    raise exception[0]
                return result[0]
            else:
                # Unix/Linux: シグナルベースのタイムアウト
                with timeout(timeout_sec, f"{func.__name__} timed out"):
                    return func(*args, **kwargs)
        
        return wrapper
    return decorator


def check_memory_limit():
    """
    現在のメモリ使用量をチェック
    制限を超えている場合は例外を発生
    """
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    if memory_mb > SecurityLimits.max_memory_mb:
        logger.error(f"Memory limit exceeded: {memory_mb:.2f}MB > {SecurityLimits.max_memory_mb}MB")
        raise ResourceLimitError(f"Memory limit exceeded: {memory_mb:.2f}MB")
    
    return memory_mb


def check_file_size(file_path: str) -> bool:
    """
    ファイルサイズをチェック
    
    Args:
        file_path: チェックするファイルパス
        
    Returns:
        制限内の場合True
        
    Raises:
        ResourceLimitError: ファイルサイズが制限を超えている場合
    """
    file_size_mb = os.path.getsize(file_path) / 1024 / 1024
    
    if file_size_mb > SecurityLimits.max_file_size_mb:
        logger.error(f"File size limit exceeded: {file_size_mb:.2f}MB > {SecurityLimits.max_file_size_mb}MB")
        raise ResourceLimitError(
            f"File size {file_size_mb:.2f}MB exceeds limit of {SecurityLimits.max_file_size_mb}MB"
        )
    
    return True


class DepthLimitedTraversal:
    """
    深度制限付きAST traversal
    """
    
    def __init__(self, max_depth: Optional[int] = None, max_nodes: Optional[int] = None):
        """
        初期化
        
        Args:
            max_depth: 最大深度（デフォルト: SecurityLimits.max_depth）
            max_nodes: 最大ノード数（デフォルト: SecurityLimits.max_nodes）
        """
        self.max_depth = max_depth or SecurityLimits.max_depth
        self.max_nodes = max_nodes or SecurityLimits.max_nodes
        self.node_count = 0
        
    def check_depth(self, depth: int) -> bool:
        """
        深度制限をチェック
        
        Args:
            depth: 現在の深度
            
        Returns:
            制限内の場合True
            
        Raises:
            DepthLimitError: 深度制限を超えた場合
        """
        if depth > self.max_depth:
            raise DepthLimitError(f"Maximum depth {self.max_depth} exceeded at depth {depth}")
        return True
    
    def check_node_count(self) -> bool:
        """
        ノード数制限をチェック
        
        Returns:
            制限内の場合True
            
        Raises:
            ResourceLimitError: ノード数制限を超えた場合
        """
        self.node_count += 1
        if self.node_count > self.max_nodes:
            raise ResourceLimitError(f"Maximum node count {self.max_nodes} exceeded")
        return True
    
    def traverse_with_limit(self, node: Any, visitor_func: Callable, depth: int = 0):
        """
        深度制限付きでASTをtraverse
        
        Args:
            node: 現在のノード
            visitor_func: 各ノードで実行する関数
            depth: 現在の深度
        """
        # 制限チェック
        self.check_depth(depth)
        self.check_node_count()
        
        # 定期的にメモリチェック（100ノードごと）
        if self.node_count % 100 == 0:
            check_memory_limit()
        
        # ノード訪問
        try:
            visitor_func(node, depth)
        except RecursionError:
            logger.error(f"Recursion limit reached at depth {depth}")
            raise DepthLimitError(f"Recursion limit reached at depth {depth}")
        
        # 子ノードのtraverse
        children = self._get_children(node)
        for child in children:
            if child is not None:
                self.traverse_with_limit(child, visitor_func, depth + 1)
    
    def _get_children(self, node: Any) -> list:
        """
        ノードの子要素を取得（実装は各ASTタイプに依存）
        
        Args:
            node: 親ノード
            
        Returns:
            子ノードのリスト
        """
        # Tree-sitter nodes
        if hasattr(node, 'children'):
            return node.children
        
        # Python AST nodes
        if hasattr(node, '_fields'):
            children = []
            for field_name in node._fields:
                field_value = getattr(node, field_name, None)
                if isinstance(field_value, list):
                    children.extend(field_value)
                elif field_value is not None and hasattr(field_value, '_fields'):
                    children.append(field_value)
            return children
        
        # Esprima/JavaScript nodes (dict形式)
        if isinstance(node, dict):
            children = []
            for key, value in node.items():
                if isinstance(value, dict) and 'type' in value:
                    children.append(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and 'type' in item:
                            children.append(item)
            return children
        
        return []


def secure_parse_with_timeout(parser_func: Callable, content: str, 
                             timeout_seconds: Optional[int] = None) -> Any:
    """
    タイムアウトとリソース制限付きでパース処理を実行
    
    Args:
        parser_func: パーサー関数
        content: パース対象のコンテンツ
        timeout_seconds: タイムアウト秒数
        
    Returns:
        パース結果
        
    Raises:
        TimeoutError: タイムアウトした場合
        ResourceLimitError: リソース制限を超えた場合
    """
    timeout_sec = timeout_seconds or SecurityLimits.parse_timeout
    
    # メモリチェック
    check_memory_limit()
    
    # コンテンツサイズチェック
    content_size_mb = len(content.encode('utf-8')) / 1024 / 1024
    if content_size_mb > SecurityLimits.max_file_size_mb:
        raise ResourceLimitError(f"Content size {content_size_mb:.2f}MB exceeds limit")
    
    # タイムアウト付きでパース実行
    @with_timeout(timeout_sec)
    def parse_with_protection():
        return parser_func(content)
    
    try:
        result = parse_with_protection()
        logger.debug(f"Parse completed successfully")
        return result
    except TimeoutError:
        logger.error(f"Parse operation timed out after {timeout_sec} seconds")
        raise
    except Exception as e:
        logger.error(f"Parse operation failed: {e}")
        raise


def configure_limits(parse_timeout: Optional[int] = None,
                     traverse_timeout: Optional[int] = None,
                     max_depth: Optional[int] = None,
                     max_memory_mb: Optional[int] = None,
                     max_file_size_mb: Optional[int] = None,
                     max_nodes: Optional[int] = None):
    """
    セキュリティ制限を設定
    
    Args:
        parse_timeout: パースタイムアウト（秒）
        traverse_timeout: traversalタイムアウト（秒）
        max_depth: 最大深度
        max_memory_mb: 最大メモリ（MB）
        max_file_size_mb: 最大ファイルサイズ（MB）
        max_nodes: 最大ノード数
    """
    if parse_timeout is not None:
        SecurityLimits.parse_timeout = parse_timeout
    if traverse_timeout is not None:
        SecurityLimits.traverse_timeout = traverse_timeout
    if max_depth is not None:
        SecurityLimits.max_depth = max_depth
    if max_memory_mb is not None:
        SecurityLimits.max_memory_mb = max_memory_mb
    if max_file_size_mb is not None:
        SecurityLimits.max_file_size_mb = max_file_size_mb
    if max_nodes is not None:
        SecurityLimits.max_nodes = max_nodes
    
    logger.info(f"Security limits configured: "
                f"parse_timeout={SecurityLimits.parse_timeout}s, "
                f"max_depth={SecurityLimits.max_depth}, "
                f"max_memory={SecurityLimits.max_memory_mb}MB")