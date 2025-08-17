# AST パーサー要件と実装計画

## 現状の問題点

### 正規表現解析の限界
1. **誤検出率が高い**: コメントや文字列内のコードパターンを実際のコードと誤認
2. **構造理解の欠如**: ネストした構造や継承関係を正確に把握できない
3. **言語機能の非対応**: ジェネリクス、ラムダ式、デコレータなどの高度な機能を解析できない

## 必要なAST パーサー

### 優先度高（主要言語）

| 言語 | 推奨パーサー | 状態 | 理由 |
|------|------------|------|------|
| Python | `ast` (標準ライブラリ) | ✅ 実装済み | 標準ライブラリで完全対応 |
| JavaScript/TypeScript | `esprima` | ✅ 実装済み | ES6+対応、npm エコシステム |
| Java | `javalang` | 📦 インストール済み・未実装 | Pure Python実装、Java 8対応 |
| C/C++ | `tree-sitter-cpp` | ❌ 未実装 | 高速、インクリメンタル解析 |
| C# | `tree-sitter-c-sharp` | ❌ 未実装 | .NET エコシステム対応 |
| Go | `tree-sitter-go` | ❌ 未実装 | Go modules対応 |

### 優先度中（人気言語）

| 言語 | 推奨パーサー | 理由 |
|------|------------|------|
| Rust | `tree-sitter-rust` | Cargo エコシステム対応 |
| PHP | `tree-sitter-php` | WordPress/Laravel 解析 |
| Ruby | `tree-sitter-ruby` | Rails アプリケーション対応 |
| Swift | `tree-sitter-swift` | iOS/macOS 開発 |
| Kotlin | `tree-sitter-kotlin` | Android 開発 |

## 実装アプローチ

### 1. Tree-sitter 統合（推奨）

```python
# tree-sitter を使った汎用AST解析
import tree_sitter
from tree_sitter import Language, Parser

class TreeSitterAnalyzer:
    LANGUAGE_LIBS = {
        'java': 'tree-sitter-java',
        'cpp': 'tree-sitter-cpp',
        'go': 'tree-sitter-go',
        'rust': 'tree-sitter-rust',
        # ... 他の言語
    }
    
    def analyze_with_tree_sitter(self, code: str, language: str):
        parser = Parser()
        parser.set_language(Language(self.LANGUAGE_LIBS[language]))
        tree = parser.parse(bytes(code, 'utf8'))
        return self.extract_structure(tree.root_node)
```

### 2. 段階的移行計画

#### Phase 1: Java AST実装（javalang使用）
```python
import javalang

class JavaASTAnalyzer:
    def analyze(self, code: str):
        tree = javalang.parse.parse(code)
        return self.extract_java_structure(tree)
```

#### Phase 2: Tree-sitter基盤整備
- tree-sitter-cli のインストール
- 各言語のgrammarファイル取得
- 統一インターフェース実装

#### Phase 3: 言語別移行
1. C/C++ → tree-sitter-cpp
2. Go → tree-sitter-go  
3. その他言語を順次移行

## 期待される改善

### 精度向上
- **誤検出率**: 30-40% → 1%未満
- **構造認識**: 60% → 95%以上
- **言語機能対応**: 基本構造のみ → 完全対応

### 新機能
- 型情報の取得
- 依存関係の正確な把握
- リファクタリング提案
- コード品質メトリクス

## 必要なリソース

### 開発時間
- Phase 1 (Java): 1-2日
- Phase 2 (Tree-sitter): 3-4日
- Phase 3 (全言語): 1-2週間

### 依存関係
```toml
[dependencies]
javalang = ">=0.13.0"
tree-sitter = ">=0.20.0"
tree-sitter-java = "*"
tree-sitter-javascript = "*"
tree-sitter-python = "*"
tree-sitter-cpp = "*"
tree-sitter-go = "*"
tree-sitter-rust = "*"
```

## 結論

正規表現解析は簡易的な構造把握には有用だが、本格的なコード解析には不適切。
各言語専用のASTパーサーへの移行が必須。Tree-sitterを基盤とした統一的な
解析システムの構築を推奨。