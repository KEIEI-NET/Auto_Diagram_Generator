"""
Auto Diagram Generator (ADG)
自動図生成ツール - Claude Code CLIカスタムコマンド
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="auto-diagram-generator",
    version="0.1.0",
    author="KEIEI-NET",
    description="コードを解析して必要な図を自動生成するインテリジェントなツール",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/KEIEI-NET/Auto_Diagram_Generator",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Documentation",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "click>=8.1.0",
        "pyyaml>=6.0",
        "rich>=13.0.0",
        "pytz>=2023.3",
        "tree-sitter>=0.20.0",
        "pygments>=2.16.0",
        "astroid>=3.0.0",
        "graphviz>=0.20.0",
        "python-dotenv>=1.0.0",
        "loguru>=0.7.0",
        "diskcache>=5.6.0",
    ],
    entry_points={
        "console_scripts": [
            "adg=adg.cli.command:main",
        ],
    },
)