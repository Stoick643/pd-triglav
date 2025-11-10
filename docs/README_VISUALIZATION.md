# Project Visualization Graphs

This directory contains generated visualization graphs created by the `generate_project_graph.py` script.

## Prerequisites

Before running the visualization script, you need to install both the Python package and the system Graphviz binary:

### 1. System Graphviz Installation

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install graphviz
```

**macOS:**
```bash
brew install graphviz
```

**Windows:**
Download and install from: https://graphviz.org/download/

### 2. Python Package Installation

The `graphviz` Python package is included in `requirements.in`:

```bash
# If using pip-tools
pip-compile requirements.in
pip-sync requirements.txt

# Or install directly
pip install graphviz
```

## Usage

The script supports three types of visualizations:

### 1. Module Dependencies (`--type=modules`)
Visualizes Python module import relationships.

```bash
python scripts/generate_project_graph.py --type modules
```

**Output:** `docs/module_dependency_graph.png`

This graph shows:
- Each Python file as a node
- Import relationships as edges
- Only local project imports (not external libraries)

### 2. Class Inheritance (`--type=classes`)
Visualizes class inheritance hierarchy.

```bash
python scripts/generate_project_graph.py --type classes
```

**Output:** `docs/class_inheritance_graph.png`

This graph shows:
- Each class as a node
- Parent-child inheritance relationships
- External base classes (like `db.Model`, `UserMixin`) shown in different colors

### 3. Template Relationships (`--type=templates`)
Visualizes Jinja2 template dependencies.

```bash
python scripts/generate_project_graph.py --type templates
```

**Output:** `docs/template_relationship_graph.png`

This graph shows:
- Each template file as a node
- `{% extends %}` relationships (blue solid lines)
- `{% include %}` relationships (green dashed lines)

## Generated Files

All generated `.png` files are automatically ignored by git (see `.gitignore`).

To regenerate all graphs:
```bash
python scripts/generate_project_graph.py --type modules
python scripts/generate_project_graph.py --type classes
python scripts/generate_project_graph.py --type templates
```

## Troubleshooting

### Error: "failed to execute PosixPath('dot')"
**Solution:** Install the system Graphviz package (see Prerequisites above).

### Error: "graphviz package not installed"
**Solution:** Install the Python graphviz package with `pip install graphviz`.

### No classes/modules/templates found
**Solution:** Ensure you're running the script from the project root directory.

## Use Cases

- **Code Reviews:** Understand module dependencies before refactoring
- **Onboarding:** Help new developers understand project structure
- **Documentation:** Visual reference for architecture decisions
- **Refactoring:** Identify tightly coupled modules or complex inheritance chains
