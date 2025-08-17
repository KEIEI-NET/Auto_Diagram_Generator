"""
AST Analyzer用のセキュリティパッチ
既存のtraversal関数に深度制限を追加するためのヘルパー関数
"""

from typing import Callable, Any, Optional
from loguru import logger
from adg.core.security_limits import (
    DepthLimitedTraversal,
    DepthLimitError,
    ResourceLimitError,
    check_memory_limit
)


def create_secure_visitor(max_depth: Optional[int] = None, 
                          max_nodes: Optional[int] = None) -> tuple:
    """
    セキュアなvisitor関数を作成
    
    Returns:
        (traversal_limiter, visitor_wrapper)のタプル
    """
    traversal = DepthLimitedTraversal(max_depth, max_nodes)
    
    def visitor_wrapper(original_visitor: Callable) -> Callable:
        """
        元のvisitor関数をラップして深度制限を追加
        """
        def secure_visitor(node: Any, depth: int = 0, *args, **kwargs):
            # 深度とノード数チェック
            try:
                traversal.check_depth(depth)
                traversal.check_node_count()
            except (DepthLimitError, ResourceLimitError) as e:
                logger.warning(f"Visitor limited: {e}")
                return None
            
            # 定期的なメモリチェック
            if traversal.node_count % 100 == 0:
                try:
                    check_memory_limit()
                except ResourceLimitError as e:
                    logger.error(f"Memory limit exceeded: {e}")
                    return None
            
            # 元のvisitor関数を実行
            return original_visitor(node, depth, *args, **kwargs)
        
        return secure_visitor
    
    return traversal, visitor_wrapper


def apply_depth_limit_to_recursive_function(func: Callable,
                                           max_depth: Optional[int] = None,
                                           depth_param_index: int = 1) -> Callable:
    """
    再帰関数に深度制限を適用
    
    Args:
        func: 元の再帰関数
        max_depth: 最大深度
        depth_param_index: depth引数の位置（0-based）
        
    Returns:
        深度制限付きの関数
    """
    from functools import wraps
    
    traversal = DepthLimitedTraversal(max_depth)
    
    @wraps(func)
    def limited_func(*args, **kwargs):
        # depth引数を取得
        depth = 0
        if len(args) > depth_param_index:
            depth = args[depth_param_index]
        elif 'depth' in kwargs:
            depth = kwargs['depth']
        
        # 深度チェック
        try:
            traversal.check_depth(depth)
            traversal.check_node_count()
        except (DepthLimitError, ResourceLimitError) as e:
            logger.warning(f"Function {func.__name__} limited: {e}")
            return None
        
        # 元の関数を実行
        return func(*args, **kwargs)
    
    return limited_func