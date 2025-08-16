"""
Mermaid形式の図生成モジュール
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pytz
from loguru import logger


class MermaidGenerator:
    """Mermaid形式の図生成"""
    
    def __init__(self, analysis_result: Dict[str, Any]):
        self.analysis = analysis_result
        self.tokyo_tz = pytz.timezone('Asia/Tokyo')
    
    def generate_class_diagram(self, output_dir: Path) -> Optional[str]:
        """クラス図を生成"""
        try:
            mermaid_code = ["classDiagram"]
            
            # 各ファイルのクラスを処理
            for file_path, file_analysis in self.analysis.get('files', {}).items():
                for class_info in file_analysis.get('classes', []):
                    # クラス定義
                    mermaid_code.append(f"    class {class_info['name']} {{")
                    
                    # 属性
                    for attr in class_info.get('attributes', []):
                        mermaid_code.append(f"        +{attr}")
                    
                    # メソッド
                    for method in class_info.get('methods', []):
                        mermaid_code.append(f"        +{method}()")
                    
                    mermaid_code.append("    }")
                    
                    # 継承関係
                    for base in class_info.get('base_classes', []):
                        if base and base != 'object':
                            mermaid_code.append(f"    {base} <|-- {class_info['name']}")
            
            # ファイルに保存
            timestamp = datetime.now(self.tokyo_tz).strftime("%Y%m%d_%H%M%S")
            filename = f"class_diagram_{timestamp}.mmd"
            file_path = output_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(mermaid_code))
            
            logger.info(f"Generated class diagram: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to generate class diagram: {e}")
            return None
    
    def generate_sequence_diagram(self, output_dir: Path) -> Optional[str]:
        """シーケンス図を生成"""
        try:
            mermaid_code = ["sequenceDiagram"]
            
            # 関数呼び出しの簡単な例
            # TODO: より詳細な呼び出し関係の解析
            mermaid_code.append("    participant User")
            mermaid_code.append("    participant System")
            mermaid_code.append("    User->>System: Request")
            mermaid_code.append("    System-->>User: Response")
            
            # ファイルに保存
            timestamp = datetime.now(self.tokyo_tz).strftime("%Y%m%d_%H%M%S")
            filename = f"sequence_diagram_{timestamp}.mmd"
            file_path = output_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(mermaid_code))
            
            logger.info(f"Generated sequence diagram: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to generate sequence diagram: {e}")
            return None
    
    def generate_er_diagram(self, output_dir: Path) -> Optional[str]:
        """ER図を生成"""
        try:
            mermaid_code = ["erDiagram"]
            
            # データモデルクラスを探す
            for file_path, file_analysis in self.analysis.get('files', {}).items():
                for class_info in file_analysis.get('classes', []):
                    # Model や Entity を含むクラスをエンティティとして扱う
                    if 'model' in class_info['name'].lower() or 'entity' in class_info['name'].lower():
                        entity_name = class_info['name'].replace('Model', '').replace('Entity', '')
                        
                        # エンティティと属性
                        mermaid_code.append(f"    {entity_name} {{")
                        for attr in class_info.get('attributes', []):
                            mermaid_code.append(f"        string {attr}")
                        mermaid_code.append("    }")
            
            # ファイルに保存
            timestamp = datetime.now(self.tokyo_tz).strftime("%Y%m%d_%H%M%S")
            filename = f"er_diagram_{timestamp}.mmd"
            file_path = output_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(mermaid_code))
            
            logger.info(f"Generated ER diagram: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to generate ER diagram: {e}")
            return None
    
    def generate_flow_diagram(self, output_dir: Path) -> Optional[str]:
        """フロー図を生成"""
        try:
            mermaid_code = ["flowchart TD"]
            
            # 関数の流れを表現
            node_id = 0
            for file_path, file_analysis in self.analysis.get('files', {}).items():
                for func in file_analysis.get('functions', []):
                    node_id += 1
                    func_name = func['name']
                    if func.get('is_async'):
                        mermaid_code.append(f"    {node_id}[{func_name} - async]")
                    else:
                        mermaid_code.append(f"    {node_id}[{func_name}]")
            
            # ファイルに保存
            timestamp = datetime.now(self.tokyo_tz).strftime("%Y%m%d_%H%M%S")
            filename = f"flow_diagram_{timestamp}.mmd"
            file_path = output_dir / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(mermaid_code))
            
            logger.info(f"Generated flow diagram: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to generate flow diagram: {e}")
            return None