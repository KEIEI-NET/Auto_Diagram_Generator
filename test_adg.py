"""
ADGの簡単なテストスクリプト
"""

import sys
from pathlib import Path

# srcディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from adg.core.analyzer import PythonAnalyzer, ProjectAnalyzer
from adg.core.detector import DiagramDetector
from adg.generators.mermaid import MermaidGenerator


def test_analyzer():
    """アナライザーのテスト"""
    print("=== Pythonコード解析テスト ===")
    
    # 自身のコードを解析
    analyzer = PythonAnalyzer("src/adg/core/analyzer.py")
    result = analyzer.analyze()
    
    print(f"クラス数: {len(result.get('classes', []))}")
    print(f"関数数: {len(result.get('functions', []))}")
    print(f"インポート数: {len(result.get('imports', []))}")
    
    if result.get('classes'):
        print("\n検出されたクラス:")
        for cls in result['classes']:
            if isinstance(cls, dict):
                # 辞書形式の場合
                class_name = cls.get('name', 'Unknown')
                methods = cls.get('methods', [])
                print(f"  - {class_name}")
                if methods:
                    method_str = ', '.join(methods[:3])
                    print(f"    メソッド: {method_str}...")
            else:
                # オブジェクト形式の場合
                print(f"  - {cls.name}")
                if hasattr(cls, 'methods') and cls.methods:
                    method_str = ', '.join(cls.methods[:3])
                    print(f"    メソッド: {method_str}...")


def test_project_analyzer():
    """プロジェクト全体の解析テスト"""
    print("\n=== プロジェクト解析テスト ===")
    
    analyzer = ProjectAnalyzer("src")
    result = analyzer.analyze()
    
    summary = result['summary']
    print(f"総ファイル数: {summary['total_files']}")
    print(f"総クラス数: {summary['total_classes']}")
    print(f"総関数数: {summary['total_functions']}")


def test_detector():
    """図判定のテスト"""
    print("\n=== 図判定テスト ===")
    
    analyzer = ProjectAnalyzer("src")
    analysis = analyzer.analyze()
    
    detector = DiagramDetector()
    recommendations = detector.detect(analysis)
    
    print("推奨される図:")
    for rec in recommendations:
        print(f"  - {rec['type']} (優先度: {rec['priority']}, 確信度: {rec['confidence']:.2f})")
        print(f"    理由: {rec['reason']}")


def test_mermaid_generator():
    """Mermaid生成テスト"""
    print("\n=== Mermaid生成テスト ===")
    
    analyzer = ProjectAnalyzer("src")
    analysis = analyzer.analyze()
    
    # 出力ディレクトリ作成
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    generator = MermaidGenerator(analysis)
    
    # クラス図生成
    class_file = generator.generate_class_diagram(output_dir)
    if class_file:
        print(f"クラス図生成: {class_file}")
        
        # ファイル内容を表示
        with open(class_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print("\n生成されたMermaidコード (最初の10行):")
            lines = content.split('\n')[:10]
            for line in lines:
                print(f"  {line}")


if __name__ == "__main__":
    test_analyzer()
    test_project_analyzer()
    test_detector()
    test_mermaid_generator()
    
    print("\n✅ すべてのテストが完了しました！")