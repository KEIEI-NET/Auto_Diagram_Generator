"""
図種別自動判定モジュール
コード解析結果から必要な図を自動判定
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class DiagramRecommendation:
    """図の推奨情報"""
    type: str
    priority: int  # 1-10, 10が最高
    reason: str
    confidence: float  # 0.0-1.0


class DiagramDetector:
    """図種別の自動判定"""
    
    def __init__(self):
        self.detection_rules = {
            'class': self._detect_class_diagram,
            'er': self._detect_er_diagram,
            'sequence': self._detect_sequence_diagram,
            'flow': self._detect_flow_diagram,
            'component': self._detect_component_diagram,
        }
    
    def detect(self, analysis_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """解析結果から必要な図を判定"""
        recommendations = []
        
        for diagram_type, detector_func in self.detection_rules.items():
            recommendation = detector_func(analysis_result)
            if recommendation and recommendation.confidence > 0.5:
                recommendations.append({
                    'type': recommendation.type,
                    'priority': recommendation.priority,
                    'reason': recommendation.reason,
                    'confidence': recommendation.confidence
                })
        
        # 優先度でソート
        recommendations.sort(key=lambda x: x['priority'], reverse=True)
        return recommendations
    
    def _detect_class_diagram(self, analysis: Dict[str, Any]) -> Optional[DiagramRecommendation]:
        """クラス図の必要性を判定"""
        try:
            summary = analysis.get('summary', {})
            if not isinstance(summary, dict):
                logger.warning("Invalid summary structure in analysis")
                return None
            
            total_classes = summary.get('total_classes', 0)
            if not isinstance(total_classes, (int, float)) or total_classes <= 0:
                return None
        except Exception as e:
            logger.error(f"Error in class diagram detection: {e}")
            return None
        
        # クラス数に基づいて優先度を決定
        if total_classes >= 5:
            priority = 9
            confidence = 0.95
            reason = f"{total_classes}個のクラスが検出されました。クラス構造の可視化が推奨されます。"
        elif total_classes >= 2:
            priority = 7
            confidence = 0.8
            reason = f"{total_classes}個のクラスが検出されました。関係性の把握に有用です。"
        else:
            priority = 5
            confidence = 0.6
            reason = "クラスが検出されました。"
        
        return DiagramRecommendation(
            type='class',
            priority=priority,
            reason=reason,
            confidence=confidence
        )
    
    def _detect_er_diagram(self, analysis: Dict[str, Any]) -> DiagramRecommendation:
        """ER図の必要性を判定"""
        # データベース関連のキーワードを検索
        db_keywords = ['model', 'entity', 'database', 'table', 'schema', 'migration']
        db_score = 0
        
        for file_path, file_analysis in analysis.get('files', {}).items():
            # ファイル名チェック
            file_lower = file_path.lower()
            if any(keyword in file_lower for keyword in db_keywords):
                db_score += 2
            
            # クラス名チェック
            for class_info in file_analysis.get('classes', []):
                if any(keyword in class_info.name.lower() for keyword in ['model', 'entity', 'table']):
                    db_score += 3
        
        if db_score == 0:
            return None
        
        if db_score >= 10:
            return DiagramRecommendation(
                type='er',
                priority=8,
                reason="データベースモデルが検出されました。ER図の作成を強く推奨します。",
                confidence=0.9
            )
        elif db_score >= 5:
            return DiagramRecommendation(
                type='er',
                priority=6,
                reason="データベース関連のコードが検出されました。",
                confidence=0.7
            )
        else:
            return None
    
    def _detect_sequence_diagram(self, analysis: Dict[str, Any]) -> DiagramRecommendation:
        """シーケンス図の必要性を判定"""
        # API、サービス、コントローラーなどのキーワードを検索
        api_keywords = ['api', 'service', 'controller', 'handler', 'endpoint', 'route']
        api_score = 0
        async_count = 0
        
        for file_path, file_analysis in analysis.get('files', {}).items():
            if not isinstance(file_analysis, dict):
                continue
            
            # 非同期関数のカウント
            functions = file_analysis.get('functions', [])
            if not isinstance(functions, list):
                continue
                
            for func in functions:
                if isinstance(func, dict) and func.get('is_async'):
                    async_count += 1
            
            # APIキーワードチェック
            file_lower = file_path.lower()
            if any(keyword in file_lower for keyword in api_keywords):
                api_score += 2
        
        if api_score == 0 and async_count == 0:
            return None
        
        if api_score >= 5 or async_count >= 3:
            return DiagramRecommendation(
                type='sequence',
                priority=7,
                reason="API処理や非同期処理が検出されました。処理フローの可視化を推奨します。",
                confidence=0.85
            )
        else:
            return DiagramRecommendation(
                type='sequence',
                priority=5,
                reason="処理フローの可視化が有用かもしれません。",
                confidence=0.6
            )
    
    def _detect_flow_diagram(self, analysis: Dict[str, Any]) -> DiagramRecommendation:
        """フロー図の必要性を判定"""
        total_functions = analysis['summary'].get('total_functions', 0)
        
        if total_functions < 3:
            return None
        
        if total_functions >= 10:
            return DiagramRecommendation(
                type='flow',
                priority=6,
                reason=f"{total_functions}個の関数が検出されました。処理フローの整理を推奨します。",
                confidence=0.75
            )
        else:
            return DiagramRecommendation(
                type='flow',
                priority=4,
                reason="複数の関数が検出されました。",
                confidence=0.5
            )
    
    def _detect_component_diagram(self, analysis: Dict[str, Any]) -> DiagramRecommendation:
        """コンポーネント図の必要性を判定"""
        # モジュール構造の複雑さを評価
        unique_modules = set()
        
        for file_path, file_analysis in analysis.get('files', {}).items():
            for import_info in file_analysis.get('imports', []):
                if import_info.get('module'):
                    unique_modules.add(import_info['module'])
        
        if len(unique_modules) < 5:
            return None
        
        if len(unique_modules) >= 10:
            return DiagramRecommendation(
                type='component',
                priority=7,
                reason=f"{len(unique_modules)}個のモジュールが検出されました。依存関係の可視化を推奨します。",
                confidence=0.8
            )
        else:
            return DiagramRecommendation(
                type='component',
                priority=5,
                reason="複数のモジュールが検出されました。",
                confidence=0.6
            )