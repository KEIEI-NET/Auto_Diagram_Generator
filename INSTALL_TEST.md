# Installation Test Procedure / インストールテスト手順

## Quick Test (5 minutes)

### 1. Fresh Installation Test

```bash
# Create test directory
mkdir adg_test
cd adg_test

# Create virtual environment
python -m venv test_env

# Activate virtual environment
# Windows:
test_env\Scripts\activate
# macOS/Linux:
source test_env/bin/activate

# Install from GitHub
pip install git+https://github.com/KEIEI-NET/Auto_Diagram_Generator.git

# Verify installation
adg --version
# Expected: Auto Diagram Generator v2.2.1
```

### 2. Basic Functionality Test

```bash
# Create test Python file
cat > test_sample.py << 'EOF'
class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b

def main():
    calc = Calculator()
    print(calc.add(5, 3))

if __name__ == "__main__":
    main()
EOF

# Test analyze command
adg analyze test_sample.py
# Expected: Shows 1 class, 3 functions

# Test diagram generation
adg generate test_sample.py --output test_output --format mermaid --types class
# Expected: Creates test_output/class_diagram_*.mmd

# Verify diagram content
cat test_output/class_diagram_*.mmd
# Expected: Shows Calculator class with methods
```

### 3. Multi-language Support Test

```bash
# Create test Delphi file
cat > test_sample.pas << 'EOF'
unit TestUnit;

interface

type
  TCalculator = class
  private
    FResult: Integer;
  public
    function Add(A, B: Integer): Integer;
    function Subtract(A, B: Integer): Integer;
  end;

implementation

function TCalculator.Add(A, B: Integer): Integer;
begin
  Result := A + B;
end;

function TCalculator.Subtract(A, B: Integer): Integer;
begin
  Result := A - B;
end;

end.
EOF

# Test Delphi analysis
adg analyze test_sample.pas
# Expected: Shows 1 class, 2 methods
```

## Comprehensive Test (15 minutes)

### 1. Development Mode Installation

```bash
# Clone repository
git clone https://github.com/KEIEI-NET/Auto_Diagram_Generator.git
cd Auto_Diagram_Generator

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/ -v
```

### 2. All Diagram Types Test

```bash
# Generate all supported diagram types
adg generate . --output all_diagrams --format all --auto

# Check generated files
ls -la all_diagrams/
# Expected: Multiple .mmd and .drawio files
```

### 3. Encoding Test

```bash
# Create Japanese comment file
cat > test_japanese.py << 'EOF'
#!/usr/bin/env python
# -*- coding: utf-8 -*-

class 日本語クラス:
    """日本語のコメント"""
    
    def 計算(self, 数値1, 数値2):
        """足し算を実行"""
        return 数値1 + 数値2
EOF

# Test with Japanese file
adg analyze test_japanese.py
# Expected: Handles Japanese characters correctly
```

### 4. Command Options Test

```bash
# Test help
adg --help
adg analyze --help
adg generate --help
adg list-types --help

# Test list-types command
adg list-types
# Expected: Shows 30+ diagram types

# Test verbose mode
adg analyze test_sample.py --verbose
# Expected: Shows detailed analysis logs
```

## Platform-Specific Tests

### Windows PowerShell

```powershell
# Test with PowerShell
python -m adg.cli.command analyze test_sample.py

# Test with Windows paths
adg analyze C:\Users\%USERNAME%\test_sample.py
```

### macOS/Linux

```bash
# Test with Unix paths
adg analyze ~/test_sample.py

# Test with symlinks
ln -s test_sample.py link_test.py
adg analyze link_test.py
```

## Troubleshooting Checklist

### ✓ Installation Issues

- [ ] Python version >= 3.10
- [ ] pip is up to date: `pip install --upgrade pip`
- [ ] Virtual environment is activated
- [ ] Network connection for GitHub access

### ✓ Runtime Issues

- [ ] All dependencies installed: `pip list | grep -E "click|loguru|tree-sitter"`
- [ ] Path is correct: `which adg` or `where adg`
- [ ] No conflicting packages: `pip show auto-diagram-generator`

### ✓ Output Issues

- [ ] Output directory exists and is writable
- [ ] Sufficient disk space
- [ ] No file permission issues

## Expected Test Results

### Successful Installation
```
✓ adg command available
✓ Version 2.2.1 displayed
✓ All subcommands accessible
```

### Successful Analysis
```
✓ Files analyzed without errors
✓ Classes/functions detected correctly
✓ Multiple encodings handled
```

### Successful Generation
```
✓ Diagrams created in output directory
✓ Mermaid format valid
✓ DrawIO format can be opened in diagrams.net
```

## Report Issues

If any test fails, please report with:

1. **System Information:**
   ```bash
   python --version
   pip --version
   echo $LANG  # or: echo %LANG% on Windows
   ```

2. **Error Message:**
   - Full error traceback
   - Command that caused the error

3. **Report to:**
   - GitHub Issues: https://github.com/KEIEI-NET/Auto_Diagram_Generator/issues
   - Include this test report

---

**Test Document Version**: 1.0.0  
**Created**: 2025-01-17 (JST)