# 自動図生成ツール（ADG）実装計画書

## プロジェクト概要
Claude Code CLIのカスタムコマンドとして動作する、コード解析による自動図生成ツールの実装計画

## 実装フェーズ

### 📋 フェーズ1: プロジェクト基盤構築（2-3日）

#### 1.1 プロジェクト構造のセットアップ
```
Auto_Diagram_Generator/
├── src/
│   ├── core/              # コア機能
│   │   ├── analyzer.py    # コード解析エンジン
│   │   ├── detector.py    # 図種別自動判定
│   │   └── generator.py   # 図生成コントローラー
│   ├── generators/        # 各フォーマット生成器
│   │   ├── mermaid.py
│   │   ├── plantuml.py
│   │   └── drawio.py
│   ├── utils/            # ユーティリティ
│   │   ├── cache.py     # キャッシュ管理
│   │   ├── version.py   # バージョン管理
│   │   └── logger.py    # ログ機能
│   └── cli/             # CLIインターフェース
│       └── command.py
├── config/
│   └── diagram-generator.yaml
├── templates/            # 図テンプレート
├── output/              # 生成図出力先
├── tests/               # テストコード
└── docs/                # ドキュメント
```

#### 1.2 必要なパッケージのインストール
- **基本パッケージ**: Python 3.9+, pip
- **解析ツール**: ast, tree-sitter, pygments
- **図生成**: graphviz, mermaid-cli, plantuml
- **ユーティリティ**: pyyaml, click, rich, pytz

#### 1.3 設定ファイルの実装
- YAML設定ローダーの実装
- 環境変数対応
- デフォルト設定の定義

### 📊 フェーズ2: コード解析モジュール（3-4日）

#### 2.1 言語別パーサーの実装
- **Python**: AST解析
- **JavaScript/TypeScript**: tree-sitter
- **Java/C#**: 正規表現ベース解析
- **SQL**: SQLパーサー

#### 2.2 コード構造抽出
- クラス・関数の抽出
- 依存関係の解析
- データベーススキーマの解析
- API エンドポイントの検出

#### 2.3 メタデータ収集
- ファイル構造の解析
- インポート/エクスポートの追跡
- コメント・ドキュメントの抽出

### 🔍 フェーズ3: 図種別判定ロジック（2-3日）

#### 3.1 判定エンジンの実装
```python
class DiagramDetector:
    def detect_required_diagrams(self, code_analysis):
        """コード解析結果から必要な図を判定"""
        diagrams = []
        
        # ER図判定
        if self.has_database_schema(code_analysis):
            diagrams.append('er_diagram')
        
        # クラス図判定
        if self.has_classes(code_analysis):
            diagrams.append('class_diagram')
        
        # シーケンス図判定
        if self.has_api_calls(code_analysis):
            diagrams.append('sequence_diagram')
        
        return diagrams
```

#### 3.2 優先度スコアリング
- 図の重要度計算
- プロジェクトタイプ別の重み付け
- ユーザー設定による調整

#### 3.3 依存関係の解決
- 図間の関連性分析
- 生成順序の最適化

### 🎨 フェーズ4: 図生成機能（4-5日）

#### 4.1 Mermaid生成器
```python
class MermaidGenerator:
    def generate_er_diagram(self, schema):
        """ER図をMermaid形式で生成"""
        
    def generate_class_diagram(self, classes):
        """クラス図をMermaid形式で生成"""
        
    def generate_sequence_diagram(self, flows):
        """シーケンス図をMermaid形式で生成"""
```

#### 4.2 PlantUML生成器
- 同様の構造でPlantUML形式対応

#### 4.3 Draw.io生成器
- XML形式での図生成
- レイアウト自動調整

#### 4.4 フォーマット変換器
- Mermaid → PlantUML
- PlantUML → Draw.io
- 相互変換機能

### 🔄 フェーズ5: バージョン管理とインクリメンタル更新（2-3日）

#### 5.1 バージョン管理システム
```python
class VersionManager:
    def generate_version(self):
        """セマンティックバージョニング"""
        
    def generate_timestamp(self):
        """東京時間でのタイムスタンプ生成"""
        return datetime.now(pytz.timezone('Asia/Tokyo'))
```

#### 5.2 差分検出
- Gitとの統合
- ファイルハッシュによる変更検出
- 依存関係の追跡

#### 5.3 インクリメンタル生成
- 変更箇所のみの再生成
- キャッシュの活用
- 並列処理の実装

### 🧪 フェーズ6: テストと最適化（3-4日）

#### 6.1 単体テスト
- 各モジュールのテスト
- モックデータによるテスト
- エッジケースの検証

#### 6.2 統合テスト
- エンドツーエンドテスト
- 実プロジェクトでのテスト
- パフォーマンステスト

#### 6.3 最適化
- 処理速度の改善
- メモリ使用量の最適化
- 並列処理の調整

## タスク管理

### 優先度: 高
1. ✅ ファイル名の適切な変更
2. ⏳ 基本的なプロジェクト構造の作成
3. ⏳ コード解析の基本実装
4. ⏳ Mermaid形式での基本的な図生成

### 優先度: 中
5. ⏳ 図種別自動判定の実装
6. ⏳ PlantUML/Draw.io対応
7. ⏳ バージョン管理機能
8. ⏳ キャッシュ機能

### 優先度: 低
9. ⏳ 高度な図種（30種類）の対応
10. ⏳ フォーマット変換機能
11. ⏳ GUI/Web インターフェース
12. ⏳ Claude API統合

## 技術スタック

### 必須
- **言語**: Python 3.9+
- **CLI**: Click
- **設定**: PyYAML
- **図生成**: Mermaid, PlantUML, graphviz

### 推奨
- **コード解析**: tree-sitter, ast
- **並列処理**: asyncio, multiprocessing
- **キャッシュ**: diskcache
- **ログ**: loguru

## 成果物

### フェーズ1完了時
- 基本的なプロジェクト構造
- 設定システム
- CLIの骨格

### フェーズ2完了時
- コード解析機能
- 言語別パーサー

### フェーズ3完了時
- 自動図判定機能
- 優先度システム

### フェーズ4完了時
- 3フォーマットでの図生成
- 基本的な8種類の図対応

### フェーズ5完了時
- バージョン管理
- インクリメンタル更新
- キャッシュシステム

### フェーズ6完了時
- 完全なテストカバレッジ
- パフォーマンス最適化
- 本番環境対応

## 見積もり工数

- **総工数**: 17-22日
- **最小実装（MVP）**: 7-8日（フェーズ1-3）
- **基本機能完成**: 14-16日（フェーズ1-5）
- **完全版**: 17-22日（全フェーズ）

## リスクと対策

### リスク1: 複雑なコード構造の解析
**対策**: 段階的に対応言語を増やし、基本的なパターンから実装

### リスク2: 図の自動レイアウト
**対策**: 既存のレイアウトアルゴリズムを活用、手動調整オプションを提供

### リスク3: パフォーマンス問題
**対策**: キャッシュの積極活用、並列処理、インクリメンタル更新

## 次のアクション

1. ✅ 実装計画書の作成（このドキュメント）
2. ⏳ Pythonプロジェクトの初期化
3. ⏳ 必要なパッケージのインストール
4. ⏳ 基本的なCLIコマンドの実装
5. ⏳ 最初のコード解析機能の実装

---

*最終更新: 2025年8月16日 23:00 JST*