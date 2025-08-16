"""
DrawIO図をMermaid図の構造を参考に生成
Mermaidの解析結果を基に、構造化されたDrawIO XML形式の図を作成
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import pytz
import json
import base64
import zlib
from loguru import logger
from dataclasses import dataclass, field

from adg.core.results import DiagramResult
from adg.generators.mermaid_refactored import (
    MermaidGeneratorRefactored,
    MermaidDiagram
)


@dataclass
class DrawIOElement:
    """DrawIO要素の基本情報"""
    id: str
    type: str  # box, arrow, text
    label: str
    x: int
    y: int
    width: int = 100
    height: int = 60
    style: str = ""
    source: Optional[str] = None
    target: Optional[str] = None


@dataclass
class DrawIOLayout:
    """レイアウト情報"""
    elements: List[DrawIOElement] = field(default_factory=list)
    connections: List[DrawIOElement] = field(default_factory=list)
    width: int = 800
    height: int = 600
    padding: int = 20
    element_spacing: int = 150
    layer_spacing: int = 100


class MermaidToDrawIOParser:
    """Mermaid図をDrawIO用に解析"""
    
    def __init__(self):
        self.element_counter = 0
        
    def parse_mermaid_diagram(self, mermaid_diagram: MermaidDiagram) -> Dict[str, Any]:
        """
        Mermaidダイアグラムを解析してDrawIO用のデータ構造に変換
        """
        if mermaid_diagram.type == 'class':
            return self._parse_class_diagram(mermaid_diagram)
        elif mermaid_diagram.type == 'sequence':
            return self._parse_sequence_diagram(mermaid_diagram)
        elif mermaid_diagram.type == 'flow':
            return self._parse_flow_diagram(mermaid_diagram)
        elif mermaid_diagram.type == 'er':
            return self._parse_er_diagram(mermaid_diagram)
        else:
            return self._parse_generic_diagram(mermaid_diagram)
    
    def _parse_class_diagram(self, diagram: MermaidDiagram) -> Dict[str, Any]:
        """クラス図を解析"""
        classes = {}
        relationships = []
        
        for line in diagram.content:
            line = line.strip()
            
            # クラス定義の開始
            if line.startswith("class ") and "{" in line:
                class_name = line.split("class ")[1].split("{")[0].strip()
                classes[class_name] = {
                    'name': class_name,
                    'attributes': [],
                    'methods': []
                }
                current_class = class_name
            
            # 属性やメソッド
            elif line.startswith("+") or line.startswith("-") or line.startswith("#"):
                if current_class and current_class in classes:
                    if "()" in line:
                        classes[current_class]['methods'].append(line.strip())
                    else:
                        classes[current_class]['attributes'].append(line.strip())
            
            # 継承関係
            elif "<|--" in line:
                parts = line.split("<|--")
                if len(parts) == 2:
                    relationships.append({
                        'type': 'inheritance',
                        'from': parts[1].strip(),
                        'to': parts[0].strip()
                    })
        
        return {
            'type': 'class',
            'classes': classes,
            'relationships': relationships
        }
    
    def _parse_sequence_diagram(self, diagram: MermaidDiagram) -> Dict[str, Any]:
        """シーケンス図を解析"""
        participants = []
        messages = []
        
        for line in diagram.content:
            line = line.strip()
            
            # 参加者
            if line.startswith("participant "):
                participant = line.split("participant ")[1].strip()
                participants.append(participant)
            
            # メッセージ
            elif "->>" in line or "-->" in line or "->" in line:
                arrow = "->>" if "->>" in line else ("-->" if "-->" in line else "->")
                parts = line.split(arrow)
                if len(parts) == 2:
                    from_part = parts[0].strip()
                    to_and_msg = parts[1].strip()
                    
                    # メッセージテキストを抽出
                    if ":" in to_and_msg:
                        to, msg = to_and_msg.split(":", 1)
                        messages.append({
                            'from': from_part,
                            'to': to.strip(),
                            'message': msg.strip(),
                            'type': arrow
                        })
        
        return {
            'type': 'sequence',
            'participants': participants,
            'messages': messages
        }
    
    def _parse_flow_diagram(self, diagram: MermaidDiagram) -> Dict[str, Any]:
        """フロー図を解析"""
        nodes = {}
        edges = []
        
        for line in diagram.content:
            line = line.strip()
            
            # ノード定義
            if "[" in line and "]" in line:
                # node1[Label]形式
                node_match = line.split("[")
                if len(node_match) >= 2:
                    node_id = node_match[0].strip()
                    label = node_match[1].split("]")[0]
                    nodes[node_id] = {'id': node_id, 'label': label}
            
            # エッジ（矢印）
            if "-->" in line:
                parts = line.split("-->")
                if len(parts) == 2:
                    from_node = parts[0].strip()
                    to_node = parts[1].strip()
                    
                    # ラベル付きノードの場合はIDのみ抽出
                    if "[" in from_node:
                        from_node = from_node.split("[")[0].strip()
                    if "[" in to_node:
                        to_node = to_node.split("[")[0].strip()
                    
                    edges.append({
                        'from': from_node,
                        'to': to_node
                    })
        
        return {
            'type': 'flow',
            'nodes': nodes,
            'edges': edges
        }
    
    def _parse_er_diagram(self, diagram: MermaidDiagram) -> Dict[str, Any]:
        """ER図を解析"""
        entities = {}
        relationships = []
        
        current_entity = None
        for line in diagram.content:
            line = line.strip()
            
            # エンティティ定義
            if line.endswith("{"):
                entity_name = line.replace("{", "").strip()
                if entity_name and entity_name != "erDiagram":
                    entities[entity_name] = {
                        'name': entity_name,
                        'attributes': []
                    }
                    current_entity = entity_name
            
            # 属性
            elif current_entity and line and not line.startswith("}"):
                if line != "}":
                    entities[current_entity]['attributes'].append(line.strip())
            
            # エンティティ定義の終了
            elif line == "}":
                current_entity = None
        
        return {
            'type': 'er',
            'entities': entities,
            'relationships': relationships
        }
    
    def _parse_generic_diagram(self, diagram: MermaidDiagram) -> Dict[str, Any]:
        """汎用的な解析"""
        return {
            'type': 'generic',
            'content': diagram.content
        }


class DrawIOGenerator:
    """DrawIO XML形式の図を生成"""
    
    def __init__(self):
        self.tokyo_tz = pytz.timezone('Asia/Tokyo')
        self.parser = MermaidToDrawIOParser()
        
    def generate_from_mermaid(
        self, 
        mermaid_diagram: MermaidDiagram,
        output_dir: Path
    ) -> DiagramResult:
        """
        Mermaid図を基にDrawIO図を生成
        
        Args:
            mermaid_diagram: 参考にするMermaid図
            output_dir: 出力ディレクトリ
        
        Returns:
            DiagramResult
        """
        try:
            # Mermaid図を解析
            parsed_data = self.parser.parse_mermaid_diagram(mermaid_diagram)
            
            # レイアウトを計算
            layout = self._calculate_layout(parsed_data)
            
            # DrawIO XMLを生成
            xml_content = self._generate_drawio_xml(layout, parsed_data)
            
            # ファイルに保存
            timestamp = datetime.now(self.tokyo_tz).strftime("%Y%m%d_%H%M%S")
            filename = f"{mermaid_diagram.type}_drawio_{timestamp}.drawio"
            file_path = output_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            logger.info(f"Generated DrawIO diagram from Mermaid: {file_path}")
            
            return DiagramResult.success_result(
                diagram_type=mermaid_diagram.type,
                file_path=str(file_path),
                format='drawio',
                content=xml_content,
                metadata={
                    'generated_at': datetime.now(self.tokyo_tz).isoformat(),
                    'source': 'mermaid',
                    'mermaid_type': mermaid_diagram.type
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to generate DrawIO from Mermaid: {e}")
            return DiagramResult.error_result(
                diagram_type=mermaid_diagram.type,
                format='drawio',
                error=str(e)
            )
    
    def _calculate_layout(self, parsed_data: Dict[str, Any]) -> DrawIOLayout:
        """レイアウトを計算"""
        layout = DrawIOLayout()
        
        if parsed_data['type'] == 'class':
            layout = self._layout_class_diagram(parsed_data)
        elif parsed_data['type'] == 'sequence':
            layout = self._layout_sequence_diagram(parsed_data)
        elif parsed_data['type'] == 'flow':
            layout = self._layout_flow_diagram(parsed_data)
        elif parsed_data['type'] == 'er':
            layout = self._layout_er_diagram(parsed_data)
        
        return layout
    
    def _layout_class_diagram(self, data: Dict[str, Any]) -> DrawIOLayout:
        """クラス図のレイアウト"""
        layout = DrawIOLayout()
        
        classes = data.get('classes', {})
        relationships = data.get('relationships', [])
        
        # クラスを配置
        x, y = 50, 50
        class_positions = {}
        
        for i, (class_name, class_info) in enumerate(classes.items()):
            # クラスボックスのサイズを計算
            num_members = len(class_info['attributes']) + len(class_info['methods'])
            height = max(80, 40 + num_members * 20)
            width = 200
            
            # UMLクラス図のスタイル
            style = "swimlane;fontStyle=1;align=center;verticalAlign=top;childLayout=stackLayout;horizontal=1;startSize=26;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=1;marginBottom=0;"
            
            element = DrawIOElement(
                id=f"class_{i}",
                type='class',
                label=self._format_class_label(class_info),
                x=x,
                y=y,
                width=width,
                height=height,
                style=style
            )
            layout.elements.append(element)
            class_positions[class_name] = element
            
            # 次の位置を計算
            x += 300
            if x > 900:
                x = 50
                y += 200
        
        # 関係を追加
        for i, rel in enumerate(relationships):
            if rel['from'] in class_positions and rel['to'] in class_positions:
                style = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;"
                if rel['type'] == 'inheritance':
                    style += "endArrow=block;endFill=0;"  # 継承の矢印
                
                connection = DrawIOElement(
                    id=f"edge_{i}",
                    type='edge',
                    label='',
                    x=0,
                    y=0,
                    style=style,
                    source=class_positions[rel['from']].id,
                    target=class_positions[rel['to']].id
                )
                layout.connections.append(connection)
        
        return layout
    
    def _layout_sequence_diagram(self, data: Dict[str, Any]) -> DrawIOLayout:
        """シーケンス図のレイアウト"""
        layout = DrawIOLayout()
        
        participants = data.get('participants', [])
        messages = data.get('messages', [])
        
        # 参加者を配置
        x = 100
        participant_positions = {}
        
        for i, participant in enumerate(participants):
            # 参加者ボックス
            style = "shape=umlLifeline;perimeter=lifelinePerimeter;whiteSpace=wrap;html=1;container=1;collapsible=0;recursiveResize=0;outlineConnect=0;"
            
            element = DrawIOElement(
                id=f"participant_{i}",
                type='lifeline',
                label=participant,
                x=x,
                y=50,
                width=100,
                height=400,
                style=style
            )
            layout.elements.append(element)
            participant_positions[participant] = element
            
            x += 200
        
        # メッセージを追加
        y = 100
        for i, msg in enumerate(messages):
            if msg['from'] in participant_positions and msg['to'] in participant_positions:
                from_elem = participant_positions[msg['from']]
                to_elem = participant_positions[msg['to']]
                
                # メッセージの矢印スタイル
                style = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;"
                if msg['type'] == '-->>':
                    style += "dashed=1;"  # 破線
                
                connection = DrawIOElement(
                    id=f"message_{i}",
                    type='message',
                    label=msg.get('message', ''),
                    x=0,
                    y=y,
                    style=style,
                    source=from_elem.id,
                    target=to_elem.id
                )
                layout.connections.append(connection)
                
                y += 50
        
        return layout
    
    def _layout_flow_diagram(self, data: Dict[str, Any]) -> DrawIOLayout:
        """フロー図のレイアウト"""
        layout = DrawIOLayout()
        
        nodes = data.get('nodes', {})
        edges = data.get('edges', [])
        
        # ノードを階層的に配置
        node_positions = {}
        x, y = 100, 50
        
        for i, (node_id, node_info) in enumerate(nodes.items()):
            # フローチャートのスタイル
            style = "rounded=1;whiteSpace=wrap;html=1;"
            
            element = DrawIOElement(
                id=f"node_{i}",
                type='process',
                label=node_info.get('label', node_id),
                x=x,
                y=y,
                width=120,
                height=60,
                style=style
            )
            layout.elements.append(element)
            node_positions[node_id] = element
            
            # 次の位置
            x += 200
            if x > 700:
                x = 100
                y += 100
        
        # エッジを追加
        for i, edge in enumerate(edges):
            if edge['from'] in node_positions and edge['to'] in node_positions:
                style = "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;"
                
                connection = DrawIOElement(
                    id=f"flow_edge_{i}",
                    type='flow',
                    label='',
                    x=0,
                    y=0,
                    style=style,
                    source=node_positions[edge['from']].id,
                    target=node_positions[edge['to']].id
                )
                layout.connections.append(connection)
        
        return layout
    
    def _layout_er_diagram(self, data: Dict[str, Any]) -> DrawIOLayout:
        """ER図のレイアウト"""
        layout = DrawIOLayout()
        
        entities = data.get('entities', {})
        
        # エンティティを配置
        x, y = 50, 50
        
        for i, (entity_name, entity_info) in enumerate(entities.items()):
            # エンティティのサイズ
            height = 40 + len(entity_info['attributes']) * 25
            width = 200
            
            # ERDのスタイル
            style = "swimlane;fontStyle=0;childLayout=stackLayout;horizontal=1;startSize=26;fillColor=none;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=1;marginBottom=0;"
            
            element = DrawIOElement(
                id=f"entity_{i}",
                type='entity',
                label=self._format_entity_label(entity_info),
                x=x,
                y=y,
                width=width,
                height=height,
                style=style
            )
            layout.elements.append(element)
            
            # 次の位置
            x += 250
            if x > 800:
                x = 50
                y += height + 50
        
        return layout
    
    def _format_class_label(self, class_info: Dict[str, Any]) -> str:
        """クラスのラベルを整形"""
        label = class_info['name'] + '\n'
        
        # 属性
        for attr in class_info.get('attributes', []):
            label += attr + '\n'
        
        # 区切り線
        if class_info.get('methods'):
            label += '---\n'
        
        # メソッド
        for method in class_info.get('methods', []):
            label += method + '\n'
        
        return label.strip()
    
    def _format_entity_label(self, entity_info: Dict[str, Any]) -> str:
        """エンティティのラベルを整形"""
        label = entity_info['name'] + '\n'
        
        for attr in entity_info.get('attributes', []):
            label += attr + '\n'
        
        return label.strip()
    
    def _generate_drawio_xml(self, layout: DrawIOLayout, parsed_data: Dict[str, Any]) -> str:
        """DrawIO XML形式を生成"""
        # ルート要素
        mxfile = ET.Element('mxfile')
        mxfile.set('version', '21.1.2')
        mxfile.set('type', 'device')
        
        # diagram要素
        diagram = ET.SubElement(mxfile, 'diagram')
        diagram.set('id', 'generated_from_mermaid')
        diagram.set('name', parsed_data.get('type', 'diagram'))
        
        # mxGraphModel
        graph_model = ET.SubElement(diagram, 'mxGraphModel')
        graph_model.set('dx', '0')
        graph_model.set('dy', '0')
        graph_model.set('grid', '1')
        graph_model.set('gridSize', '10')
        graph_model.set('guides', '1')
        graph_model.set('tooltips', '1')
        graph_model.set('connect', '1')
        graph_model.set('arrows', '1')
        graph_model.set('fold', '1')
        graph_model.set('page', '1')
        graph_model.set('pageScale', '1')
        graph_model.set('pageWidth', '827')
        graph_model.set('pageHeight', '1169')
        
        # root要素
        root = ET.SubElement(graph_model, 'root')
        
        # デフォルトセル
        cell0 = ET.SubElement(root, 'mxCell')
        cell0.set('id', '0')
        
        cell1 = ET.SubElement(root, 'mxCell')
        cell1.set('id', '1')
        cell1.set('parent', '0')
        
        # 要素を追加
        for element in layout.elements:
            cell = ET.SubElement(root, 'mxCell')
            cell.set('id', element.id)
            cell.set('value', element.label)
            cell.set('style', element.style)
            cell.set('vertex', '1')
            cell.set('parent', '1')
            
            # geometry
            geometry = ET.SubElement(cell, 'mxGeometry')
            geometry.set('x', str(element.x))
            geometry.set('y', str(element.y))
            geometry.set('width', str(element.width))
            geometry.set('height', str(element.height))
            geometry.set('as', 'geometry')
        
        # 接続を追加
        for connection in layout.connections:
            cell = ET.SubElement(root, 'mxCell')
            cell.set('id', connection.id)
            cell.set('value', connection.label)
            cell.set('style', connection.style)
            cell.set('edge', '1')
            cell.set('parent', '1')
            cell.set('source', connection.source)
            cell.set('target', connection.target)
            
            # geometry
            geometry = ET.SubElement(cell, 'mxGeometry')
            geometry.set('relative', '1')
            geometry.set('as', 'geometry')
        
        # XMLを整形
        xml_str = ET.tostring(mxfile, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent="  ")
        
        # 余分な空行を削除
        lines = pretty_xml.split('\n')
        lines = [line for line in lines if line.strip()]
        
        return '\n'.join(lines)


class MermaidBasedDrawIOGenerator:
    """Mermaid図を基にしたDrawIO生成の統合クラス"""
    
    def __init__(self, analysis_result: Dict[str, Any]):
        self.analysis_result = analysis_result
        self.mermaid_generator = MermaidGeneratorRefactored(analysis_result)
        self.drawio_generator = DrawIOGenerator()
        
    def generate_all(self, output_dir: Path) -> List[DiagramResult]:
        """
        すべての図をMermaid→DrawIOの順で生成
        
        Args:
            output_dir: 出力ディレクトリ
        
        Returns:
            生成結果のリスト
        """
        results = []
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 各図タイプについて処理
        for diagram_type in ['class', 'sequence', 'flow', 'er']:
            try:
                # まずMermaid図を生成
                logger.info(f"Generating Mermaid {diagram_type} diagram...")
                mermaid_result = self.mermaid_generator.generate(
                    diagram_type, 
                    output_dir,
                    validate=True
                )
                
                if mermaid_result.success:
                    # Mermaid図を基にDrawIO図を生成
                    logger.info(f"Converting to DrawIO {diagram_type} diagram...")
                    
                    # Mermaidダイアグラムオブジェクトを再構築
                    builder = self.mermaid_generator.builders[diagram_type](self.analysis_result)
                    mermaid_diagram = builder.build()
                    
                    # DrawIO生成
                    drawio_result = self.drawio_generator.generate_from_mermaid(
                        mermaid_diagram,
                        output_dir
                    )
                    
                    results.append(drawio_result)
                else:
                    logger.warning(f"Skipping DrawIO generation for {diagram_type}: Mermaid generation failed")
                    results.append(mermaid_result)
                    
            except Exception as e:
                logger.error(f"Failed to generate {diagram_type} diagram: {e}")
                results.append(DiagramResult.error_result(
                    diagram_type=diagram_type,
                    format='drawio',
                    error=str(e)
                ))
        
        # サマリーレポート生成
        self._generate_summary_report(results, output_dir)
        
        return results
    
    def _generate_summary_report(self, results: List[DiagramResult], output_dir: Path):
        """サマリーレポートを生成"""
        summary = {
            'timestamp': datetime.now(pytz.timezone('Asia/Tokyo')).isoformat(),
            'total': len(results),
            'successful': sum(1 for r in results if r.success),
            'failed': sum(1 for r in results if not r.success),
            'details': []
        }
        
        for result in results:
            detail = {
                'type': result.diagram_type,
                'format': result.format,
                'success': result.success,
                'file': result.file_path,
                'error': result.error
            }
            summary['details'].append(detail)
        
        # レポートファイルを保存
        report_file = output_dir / 'mermaid_to_drawio_summary.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Summary report saved: {report_file}")


# テスト関数
def test_mermaid_to_drawio():
    """Mermaid→DrawIO変換のテスト"""
    from adg.core.analyzer import ProjectAnalyzer
    
    # プロジェクト解析
    analyzer = ProjectAnalyzer("src")
    analysis_result = analyzer.analyze()
    
    # 出力ディレクトリ
    output_dir = Path("output/mermaid_to_drawio")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成
    generator = MermaidBasedDrawIOGenerator(analysis_result)
    results = generator.generate_all(output_dir)
    
    # 結果表示
    for result in results:
        if result.success:
            print(f"✓ {result.diagram_type} ({result.format}): {result.file_path}")
        else:
            print(f"✗ {result.diagram_type} ({result.format}): {result.error}")
    
    return results


if __name__ == "__main__":
    test_results = test_mermaid_to_drawio()