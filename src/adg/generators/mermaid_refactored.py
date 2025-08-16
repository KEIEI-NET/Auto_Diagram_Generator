"""
リファクタリングされたMermaid図生成モジュール
DRY原則に従い、検証機能付き
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from abc import ABC, abstractmethod
import pytz
import json
import re
from loguru import logger
from dataclasses import dataclass

from adg.core.results import DiagramResult


@dataclass
class MermaidDiagram:
    """Mermaidダイアグラムの情報"""
    type: str
    content: List[str]
    metadata: Dict[str, Any]
    validation_errors: List[str] = None
    
    def __post_init__(self):
        if self.validation_errors is None:
            self.validation_errors = []
    
    def to_string(self) -> str:
        """文字列に変換"""
        return '\n'.join(self.content)
    
    def is_valid(self) -> bool:
        """検証結果を返す"""
        return len(self.validation_errors) == 0


class MermaidValidator:
    """Mermaid構文の検証"""
    
    @staticmethod
    def validate(diagram: MermaidDiagram) -> Tuple[bool, List[str]]:
        """
        Mermaidダイアグラムを検証
        
        Returns:
            (is_valid, errors)
        """
        errors = []
        content = diagram.to_string()
        
        # 基本構文チェック
        if not content.strip():
            errors.append("ダイアグラムが空です")
            return False, errors
        
        # ダイアグラムタイプの検証
        valid_types = [
            'graph', 'flowchart', 'sequenceDiagram', 'classDiagram',
            'stateDiagram', 'erDiagram', 'gantt', 'pie', 'gitGraph'
        ]
        
        first_line = diagram.content[0] if diagram.content else ""
        diagram_type = first_line.split()[0] if first_line else ""
        
        if diagram_type not in valid_types:
            errors.append(f"不正なダイアグラムタイプ: {diagram_type}")
        
        # 構文検証
        errors.extend(MermaidValidator._validate_syntax(diagram))
        
        # 特定タイプの検証
        if diagram.type == 'class':
            errors.extend(MermaidValidator._validate_class_diagram(diagram))
        elif diagram.type == 'sequence':
            errors.extend(MermaidValidator._validate_sequence_diagram(diagram))
        elif diagram.type == 'er':
            errors.extend(MermaidValidator._validate_er_diagram(diagram))
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_syntax(diagram: MermaidDiagram) -> List[str]:
        """基本構文を検証"""
        errors = []
        content = diagram.to_string()
        
        # 括弧のバランスチェック
        open_brackets = content.count('{')
        close_brackets = content.count('}')
        if open_brackets != close_brackets:
            errors.append(f"括弧のバランスが不正: {{ {open_brackets} vs }} {close_brackets}")
        
        open_parens = content.count('(')
        close_parens = content.count(')')
        if open_parens != close_parens:
            errors.append(f"括弧のバランスが不正: ( {open_parens} vs ) {close_parens}")
        
        # 危険な文字のチェック
        dangerous_patterns = [
            r'<script', r'javascript:', r'onclick', r'onerror',
            r'eval\(', r'alert\('
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                errors.append(f"危険なパターンが検出されました: {pattern}")
        
        return errors
    
    @staticmethod
    def _validate_class_diagram(diagram: MermaidDiagram) -> List[str]:
        """クラス図を検証"""
        errors = []
        content = diagram.to_string()
        
        # クラス定義の検証
        class_pattern = r'class\s+(\w+)\s*\{'
        classes = re.findall(class_pattern, content)
        
        if not classes:
            errors.append("クラス定義が見つかりません")
        
        # 関係の検証
        relation_patterns = [
            r'(\w+)\s*<\|--\s*(\w+)',  # 継承
            r'(\w+)\s*\*--\s*(\w+)',   # コンポジション
            r'(\w+)\s*o--\s*(\w+)',    # アグリゲーション
            r'(\w+)\s*-->\s*(\w+)',    # 依存
        ]
        
        for pattern in relation_patterns:
            relations = re.findall(pattern, content)
            for source, target in relations:
                if source not in classes and target not in classes:
                    errors.append(f"未定義のクラス参照: {source} -> {target}")
        
        return errors
    
    @staticmethod
    def _validate_sequence_diagram(diagram: MermaidDiagram) -> List[str]:
        """シーケンス図を検証"""
        errors = []
        content = diagram.to_string()
        
        # 参加者の検証
        participant_pattern = r'participant\s+(\w+)'
        participants = re.findall(participant_pattern, content)
        
        # メッセージの検証
        message_pattern = r'(\w+)\s*->>?\s*(\w+)'
        messages = re.findall(message_pattern, content)
        
        for sender, receiver in messages:
            if sender not in participants and receiver not in participants:
                errors.append(f"未定義の参加者: {sender} or {receiver}")
        
        return errors
    
    @staticmethod
    def _validate_er_diagram(diagram: MermaidDiagram) -> List[str]:
        """ER図を検証"""
        errors = []
        content = diagram.to_string()
        
        # エンティティの検証
        entity_pattern = r'(\w+)\s*\{'
        entities = re.findall(entity_pattern, content)
        
        if not entities:
            errors.append("エンティティ定義が見つかりません")
        
        # リレーションシップの検証
        relation_pattern = r'(\w+)\s*\|\|--o\{\s*(\w+)'
        relations = re.findall(relation_pattern, content)
        
        for entity1, entity2 in relations:
            if entity1 not in entities or entity2 not in entities:
                errors.append(f"未定義のエンティティ参照: {entity1} - {entity2}")
        
        return errors


class BaseMermaidBuilder(ABC):
    """Mermaidビルダーの基底クラス"""
    
    def __init__(self, analysis_result: Dict[str, Any]):
        self.analysis = analysis_result
        self.tokyo_tz = pytz.timezone('Asia/Tokyo')
    
    @abstractmethod
    def build(self) -> MermaidDiagram:
        """ダイアグラムを構築"""
        pass
    
    def _create_metadata(self, diagram_type: str) -> Dict[str, Any]:
        """メタデータを作成"""
        return {
            'type': diagram_type,
            'generated_at': datetime.now(self.tokyo_tz).isoformat(),
            'source_files': len(self.analysis.get('files', {})),
            'version': '1.0.0'
        }
    
    def _sanitize_name(self, name: str) -> str:
        """名前をサニタイズ"""
        # Mermaidで問題となる文字を置換
        sanitized = re.sub(r'[^\w]', '_', name)
        # 数字で始まる場合は接頭辞を追加
        if sanitized and sanitized[0].isdigit():
            sanitized = f"c_{sanitized}"
        return sanitized or "unnamed"


class ClassDiagramBuilder(BaseMermaidBuilder):
    """クラス図ビルダー"""
    
    def build(self) -> MermaidDiagram:
        """クラス図を構築"""
        lines = ["classDiagram"]
        relationships = []
        
        for file_path, file_analysis in self.analysis.get('files', {}).items():
            for class_info in file_analysis.get('classes', []):
                class_name = self._sanitize_name(class_info.get('name', 'Unknown'))
                
                # クラス定義
                lines.append(f"    class {class_name} {{")
                
                # 属性
                for attr in class_info.get('attributes', []):
                    attr_name = self._sanitize_name(attr)
                    lines.append(f"        +{attr_name}")
                
                # メソッド
                for method in class_info.get('methods', []):
                    method_name = self._sanitize_name(method)
                    lines.append(f"        +{method_name}()")
                
                lines.append("    }")
                
                # 継承関係
                for base in class_info.get('base_classes', []):
                    if base and base != 'object':
                        base_name = self._sanitize_name(base)
                        relationships.append(f"    {base_name} <|-- {class_name}")
        
        # 関係を追加
        lines.extend(relationships)
        
        return MermaidDiagram(
            type='class',
            content=lines,
            metadata=self._create_metadata('class')
        )


class SequenceDiagramBuilder(BaseMermaidBuilder):
    """シーケンス図ビルダー"""
    
    def build(self) -> MermaidDiagram:
        """シーケンス図を構築"""
        lines = ["sequenceDiagram"]
        
        # 参加者を定義
        participants = set()
        for file_path, file_analysis in self.analysis.get('files', {}).items():
            for class_info in file_analysis.get('classes', []):
                class_name = self._sanitize_name(class_info.get('name', 'Unknown'))
                participants.add(class_name)
        
        # 参加者を追加
        for participant in sorted(participants):
            lines.append(f"    participant {participant}")
        
        # 基本的なインタラクション（実際のコールフロー解析は今後実装）
        if len(participants) >= 2:
            participants_list = sorted(participants)
            lines.append(f"    {participants_list[0]}->>+{participants_list[1]}: Request")
            lines.append(f"    {participants_list[1]}-->>-{participants_list[0]}: Response")
        
        return MermaidDiagram(
            type='sequence',
            content=lines,
            metadata=self._create_metadata('sequence')
        )


class ERDiagramBuilder(BaseMermaidBuilder):
    """ER図ビルダー"""
    
    def build(self) -> MermaidDiagram:
        """ER図を構築"""
        lines = ["erDiagram"]
        
        for file_path, file_analysis in self.analysis.get('files', {}).items():
            for class_info in file_analysis.get('classes', []):
                class_name = class_info.get('name', 'Unknown')
                
                # ModelやEntityを含むクラスをエンティティとして扱う
                if 'model' in class_name.lower() or 'entity' in class_name.lower():
                    entity_name = self._sanitize_name(
                        class_name.replace('Model', '').replace('Entity', '')
                    )
                    
                    lines.append(f"    {entity_name} {{")
                    
                    # 属性をフィールドとして追加
                    for attr in class_info.get('attributes', []):
                        attr_name = self._sanitize_name(attr)
                        # 型は推測（実際の実装では型情報を解析）
                        lines.append(f"        string {attr_name}")
                    
                    lines.append("    }")
        
        return MermaidDiagram(
            type='er',
            content=lines,
            metadata=self._create_metadata('er')
        )


class FlowDiagramBuilder(BaseMermaidBuilder):
    """フロー図ビルダー"""
    
    def build(self) -> MermaidDiagram:
        """フロー図を構築"""
        lines = ["flowchart TD"]
        
        node_id = 0
        for file_path, file_analysis in self.analysis.get('files', {}).items():
            for func in file_analysis.get('functions', []):
                node_id += 1
                func_name = self._sanitize_name(func.get('name', 'Unknown'))
                
                if func.get('is_async'):
                    lines.append(f"    node{node_id}[{func_name} - async]")
                else:
                    lines.append(f"    node{node_id}[{func_name}]")
                
                # 簡単な連結（実際のフロー解析は今後実装）
                if node_id > 1:
                    lines.append(f"    node{node_id-1} --> node{node_id}")
        
        return MermaidDiagram(
            type='flow',
            content=lines,
            metadata=self._create_metadata('flow')
        )


class MermaidGeneratorRefactored:
    """リファクタリングされたMermaid生成器"""
    
    def __init__(self, analysis_result: Dict[str, Any]):
        self.analysis = analysis_result
        self.tokyo_tz = pytz.timezone('Asia/Tokyo')
        self.builders = {
            'class': ClassDiagramBuilder,
            'sequence': SequenceDiagramBuilder,
            'er': ERDiagramBuilder,
            'flow': FlowDiagramBuilder,
        }
        self.validator = MermaidValidator()
    
    def generate(self, diagram_type: str, output_dir: Path, validate: bool = True) -> DiagramResult:
        """
        指定された種類の図を生成
        
        Args:
            diagram_type: 図の種類
            output_dir: 出力ディレクトリ
            validate: 検証を実行するか
        
        Returns:
            DiagramResult
        """
        try:
            # ビルダーを取得
            builder_class = self.builders.get(diagram_type)
            if not builder_class:
                return DiagramResult.error_result(
                    diagram_type=diagram_type,
                    format='mermaid',
                    error=f"未対応の図種類: {diagram_type}"
                )
            
            # ダイアグラムを構築
            builder = builder_class(self.analysis)
            diagram = builder.build()
            
            # 検証
            if validate:
                is_valid, errors = self.validator.validate(diagram)
                if not is_valid:
                    logger.warning(f"Validation errors: {errors}")
                    diagram.validation_errors = errors
            
            # ファイルに保存
            file_path = self._save_diagram(diagram, output_dir)
            
            return DiagramResult.success_result(
                diagram_type=diagram_type,
                file_path=str(file_path),
                format='mermaid',
                content=diagram.to_string(),
                metadata={
                    **diagram.metadata,
                    'validation_errors': diagram.validation_errors,
                    'is_valid': diagram.is_valid()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to generate {diagram_type} diagram: {e}")
            return DiagramResult.error_result(
                diagram_type=diagram_type,
                format='mermaid',
                error=str(e)
            )
    
    def _save_diagram(self, diagram: MermaidDiagram, output_dir: Path) -> Path:
        """ダイアグラムをファイルに保存"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now(self.tokyo_tz).strftime("%Y%m%d_%H%M%S")
        filename = f"{diagram.type}_diagram_{timestamp}.mmd"
        file_path = output_dir / filename
        
        # メタデータを含むコメントを追加
        content_with_metadata = [
            f"%% Generated by ADG at {diagram.metadata['generated_at']}",
            f"%% Type: {diagram.type}",
            f"%% Version: {diagram.metadata.get('version', 'unknown')}",
            ""
        ]
        content_with_metadata.extend(diagram.content)
        
        # 検証エラーがある場合はコメントとして追加
        if diagram.validation_errors:
            content_with_metadata.extend([
                "",
                "%% Validation Errors:",
            ])
            for error in diagram.validation_errors:
                content_with_metadata.append(f"%% - {error}")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_with_metadata))
        
        logger.info(f"Generated {diagram.type} diagram: {file_path}")
        return file_path
    
    def generate_all(self, output_dir: Path) -> List[DiagramResult]:
        """すべての種類の図を生成"""
        results = []
        for diagram_type in self.builders.keys():
            result = self.generate(diagram_type, output_dir)
            results.append(result)
        return results