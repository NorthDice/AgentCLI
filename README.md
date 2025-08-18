# AgentCLI

A developer tool for autonomous code operations.

## Description

AgentCLI is a tool that processes natural language queries and converts them into specific actions for working with code:
- Reading, modifying, and creating files
- Tracking changes
- Code generation
- Analysis of existing code

## Features

- **File Operations**: reading/analyzing code, creating files/directories, safe edits, project search, change logs.
- **Code Generation**: complete programs from descriptions, functions from specifications, tests, project structures, documentation.
- **Planning**: task decomposition, execution order, dependencies, progress control, cancellation.
- **Code Analysis**: explaining functionality, component relationships, problem identification, answers to architecture questions.

## Installation

```bash
pip install -e .
```

## Usage

### Creating a Plan
```bash
agentcli plan "Create a function to calculate factorial"
```

### Executing a Plan
```bash
agentcli apply plan.yaml
```

### Rolling Back Changes
```bash
agentcli rollback
```

### Searching in Files
```bash
agentcli search "factorial function"
```

### Explaining Code
```bash
agentcli explain path/to/file.py
```

### Generating Code
```bash
agentcli gen "Function to calculate Fibonacci numbers" -o fib.py
```

### Viewing Status
```bash
agentcli status
```
