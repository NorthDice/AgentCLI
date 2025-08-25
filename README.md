# AgentCLI

AI-powered developer tool for code operations, analysis, and intelligent project management.

## Features

- **🔍 Smart Search**: Semantic and literal search with .gitignore support
- **🤖 AI Q&A**: Ask questions about your codebase and get intelligent answers
- **📊 Code Analysis**: AST-based analysis with complexity metrics
- **🔄 Safe Operations**: File operations with comprehensive rollback support
- **📝 Code Generation**: AI-powered code generation from descriptions
- **🏗️ Context-Aware Planning**: Use `--structure` flag for better refactoring with full project awareness
- **💻 Interactive Console**: Persistent shell with background indexing and intelligent caching

## Interactive Console Mode

AgentCLI now includes an interactive console mode that provides a persistent shell with background indexing and intelligent caching:

```bash
# Start interactive console
python main.py console

# Or with options
python main.py console --project-path /path/to/project --debug
```

### Interactive Console Features

- **🔄 Background Indexing**: Automatic project indexing starts when console launches
- **💾 Intelligent Caching**: Project structure and search index are cached for fast access
- **⚡ Real-time Updates**: Modified files are automatically re-indexed
- **🎯 Context-Aware Commands**: All commands have access to full project context
- **📊 Status Monitoring**: Real-time status of indexing and cache operations

### Available Console Commands

```bash
# Show help
help

# Check system status
status

# Generate content with project context
gen "Create a Python function to calculate fibonacci" -o fib.py

# Create action plan with full project awareness
plan "Add logging to all CLI commands"

# Apply action plan
apply <plan_id>

# Search in project (uses cached index)
search "class BackgroundIndexer"

# Rebuild project index
index

# Show cache information
cache

# Exit console
quit
```

### Console Workflow

1. **Startup**: Console starts and immediately begins background indexing
2. **Ready**: Once indexing completes, all commands have access to full project context
3. **Auto-Caching**: Any file modifications trigger automatic re-indexing
4. **Optimized LLM**: Context is intelligently cached to minimize token usage

### Virtual Environment Management

Always work within the virtual environment:

```bash
# Activate environment
source .venv/bin/activate

# Install new dependencies
pip install package_name
pip freeze > requirements.txt  # Update requirements

# Deactivate when done
deactivate
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feat/amazing-feature`)
3. Follow conventional commit guidelines
4. Commit your changes (`git commit -m 'feat: add amazing feature'`)
5. Push to the branch (`git push origin feat/amazing-feature`)
6. Open a Pull Request
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
# Planning and execution
agentcli plan "Refactor auth module"

# Use --structure for better refactoring plans
agentcli plan "Fix imports in app/crud.py" --structure
agentcli plan "Refactor models to use Pydantic" --structure

# Apply specific plan
agentcli apply plans/plan-id.json

# Apply last created plan (convenient!)
agentcli apply --last

# Rollback operations
agentcli rollback                    # last operation
agentcli rollback --steps 3          # multiple steps
agentcli rollback --last-plan        # entire plan

# Check execution status
agentcli status
```

**💡 Pro Tip**: When working with refactoring or code structure changes, use the `--structure` flag with `agentcli plan`. This provides the AI with full project context, ensuring accurate file paths, proper imports, and better understanding of your codebase organization.

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

# 4. Create and apply plans easily
agentcli plan "Add logging to authentication module"
agentcli apply --last  # No need for long plan IDs!

# 5. Smart refactoring with project context
agentcli plan "Fix imports in models/user.py" --structure
agentcli apply --last --yes

# 6. Generate new code
agentcli gen "Class for user management" --output user.py
```

### Working with Project Structure

For refactoring tasks, the `--structure` flag is essential:

```bash
# ❌ Without --structure: AI might create incorrect file paths
agentcli plan "Fix imports in crud.py"

# ✅ With --structure: AI understands your project layout
agentcli plan "Fix imports in app/crud.py" --structure
```

The `--structure` flag provides the AI with:
- **📁 Directory structure** - knows where files are located
- **🐍 Python modules** - understands import relationships  
- **🔗 Dependencies** - sees how files connect
- **📋 File exports** - knows what functions/classes exist

This results in more accurate plans with correct file paths and imports.

