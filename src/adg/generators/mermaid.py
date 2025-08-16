"""
Mermaid形式の図生成モジュール
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pytz
from loguru import logger

try:
    from ..utils.validation import (
        is_valid_dict, is_valid_list, is_valid_string,
        sanitize_mermaid_text, validate_analysis_structure
    )
except ImportError:
    # フォールバック関数
    def is_valid_dict(obj): return isinstance(obj, dict)
    def is_valid_list(obj): return isinstance(obj, list)
    def is_valid_string(obj): return isinstance(obj, str)
    def sanitize_mermaid_text(text): return str(text)[:50] if text else "Unknown"
    def validate_analysis_structure(analysis): return True


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
                if not isinstance(file_analysis, dict):
                    continue
                
                classes = file_analysis.get('classes', [])
                if not isinstance(classes, list):
                    continue
                
                for class_info in classes:
                    if not isinstance(class_info, dict) or 'name' not in class_info:
                        logger.warning(f"Invalid class_info structure in {file_path}")
                        continue
                    
                    class_name = sanitize_mermaid_text(class_info.get('name', ''))
                    if not class_name or class_name == 'Unknown':
                        logger.warning(f"Invalid class name in {file_path}")
                        continue
                    
                    # クラス定義
                    mermaid_code.append(f"    class {class_name} {{")
                    
                    # 属性
                    attributes = class_info.get('attributes', [])
                    if isinstance(attributes, list):
                        for attr in attributes:
                            if isinstance(attr, str) and attr.isidentifier():
                                mermaid_code.append(f"        +{attr}")
                    
                    # メソッド
                    methods = class_info.get('methods', [])
                    if isinstance(methods, list):
                        for method in methods:
                            if isinstance(method, str) and method.isidentifier():
                                mermaid_code.append(f"        +{method}()")
                    
                    mermaid_code.append("    }")
                    
                    # 継承関係
                    base_classes = class_info.get('base_classes', [])
                    if isinstance(base_classes, list):
                        for base in base_classes:
                            if isinstance(base, str) and base.isidentifier() and base != 'object':
                                mermaid_code.append(f"    {base} <|-- {class_name}")
            
            # ファイルに保存
            timestamp = datetime.now(self.tokyo_tz).strftime("%Y%m%d_%H%M%S")
            filename = f"class_diagram_{timestamp}.mmd"
            file_path = output_dir / filename
            
            # 出力ディレクトリの存在確認と作成
            output_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(mermaid_code))
                
                logger.info(f"Generated class diagram: {file_path}")
                return str(file_path)
            except (PermissionError, OSError) as e:
                logger.error(f"Failed to write file {file_path}: {e}")
                return None
            
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