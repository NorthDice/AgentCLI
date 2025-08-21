from setuptools import setup, find_packages

setup(
    name="agentcli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.1.0",
        "rich>=13.0.0",
        "python-dotenv>=1.0.0",
        "openai>=1.0.0",
        "chromadb>=0.4.0",
        "sentence-transformers>=2.2.0",
        "tree-sitter>=0.20.0",
        "tree-sitter-python>=0.20.0",
        "pyyaml>=6.0.0",
        "psutil>=5.9.0",
    ],
    entry_points={
        "console_scripts": [
            "agentcli=agentcli.cli.main:cli",
        ],
    },
    python_requires=">=3.8",
)
