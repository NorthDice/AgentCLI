# AgentCLI

AI-powered developer tool for code operations, analysis, and intelligent project management.

## Features

- **🔍 Smart Search**: Semantic and literal search with .gitignore support
- **🤖 AI Q&A**: Ask questions about your codebase and get intelligent answers
- **📊 Code Analysis**: AST-based analysis with complexity metrics
- **🔄 Safe Operations**: File operations with comprehensive rollback support
- **📝 Code Generation**: AI-powered code generation from descriptions

## Installation

```bash
# Clone and install with Poetry (recommended)
git clone https://github.com/NorthDice/AgentCLI.git
cd AgentCLI
poetry install
poetry shell

# Or install directly with pip
pip install -e .
```

## Configuration

Create a `.env` file with your Azure OpenAI credentials:

```env
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT=your_deployment_name
AZURE_OPENAI_API_VERSION=2023-05-15
```

## Commands

### Search
```bash
# Text search
agentcli search "function name" --file-pattern "*.py"

# Regex search
agentcli search "def\s+\w+" --regex

# Semantic AI search
agentcli search "database connection" --semantic

# Respect/ignore .gitignore
agentcli search "test" --use-gitignore
agentcli search "test" --ignore-gitignore

# Output formats
agentcli search "error" --format links    # file:line format
agentcli search "error" --format compact  # compact output
```

### AI Q&A
```bash
# Ask questions about your codebase
agentcli ask "How does authentication work?"
agentcli ask "What files handle database operations?"
agentcli ask "How is error handling implemented?"

# Control analysis depth
agentcli ask "Explain the config system" --top-k 3
```

### Code Analysis
```bash
# Analyze Python files
agentcli explain path/to/file.py
agentcli explain src/main.py --verbose
agentcli explain module.py --format json
```

### File Operations
```bash
# Safe file deletion with rollback
agentcli delete path/to/file.py --reason "cleanup"
agentcli delete temp.py --dry-run

# Code generation
agentcli gen "Function to calculate factorial" --output math.py
agentcli gen "Add error handling" --output existing.py --dry-run
```

### Change Management
```bash
# Rollback operations
agentcli rollback                    # last operation
agentcli rollback --steps 3          # multiple steps
agentcli rollback --last-plan        # entire plan

# Planning and execution
agentcli plan "Refactor auth module"
agentcli apply plan.yaml
agentcli status
```

### System
```bash
# Check configuration
agentcli llm-config
agentcli llm-config --test

# Manage search index
agentcli search "query" --rebuild-index
```

## Quick Start

```bash
# 1. Search your codebase
agentcli search "import" --file-pattern "*.py" --format links

# 2. Ask questions about your project
agentcli ask "What is the main entry point?"

# 3. Analyze complex files
agentcli explain src/main.py --verbose

# 4. Generate new code
agentcli gen "Class for user management" --output user.py
```

