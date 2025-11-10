#!/usr/bin/env python3
"""
Project Visualization Script

Generate different types of dependency graphs for the PD Triglav project.
Supports three visualization types:
- modules: Python module import dependencies
- classes: Class inheritance relationships
- templates: Jinja2 template relationships (extends/includes)

Usage:
    python scripts/generate_project_graph.py --type modules
    python scripts/generate_project_graph.py --type classes
    python scripts/generate_project_graph.py --type templates
"""

import argparse
import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

try:
    from graphviz import Digraph
except ImportError:
    print("Error: graphviz package not installed.")
    print("Please install it with: pip install graphviz")
    print("Also ensure the system graphviz is installed (e.g., apt-get install graphviz)")
    exit(1)


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
MODELS_DIR = PROJECT_ROOT / "models"
ROUTES_DIR = PROJECT_ROOT / "routes"
FORMS_DIR = PROJECT_ROOT / "forms"
UTILS_DIR = PROJECT_ROOT / "utils"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# Source directories to scan for Python files
PYTHON_SOURCE_DIRS = [MODELS_DIR, ROUTES_DIR, FORMS_DIR, UTILS_DIR]


def ensure_docs_directory():
    """Create docs directory if it doesn't exist."""
    DOCS_DIR.mkdir(exist_ok=True)
    print(f"Output directory: {DOCS_DIR}")


def get_python_files(directory: Path) -> List[Path]:
    """Get all Python files in a directory."""
    if not directory.exists():
        return []
    return [f for f in directory.rglob("*.py") if f.name != "__init__.py"]


def extract_imports_from_file(file_path: Path) -> Set[str]:
    """
    Extract local project imports from a Python file.
    Returns a set of imported module names (local to the project).
    """
    imports = set()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        for node in ast.walk(tree):
            # Handle "import module"
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Check if it's a local import (models, routes, forms, utils, config)
                    module_name = alias.name.split('.')[0]
                    if module_name in ['models', 'routes', 'forms', 'utils', 'config']:
                        imports.add(alias.name)

            # Handle "from module import something"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split('.')[0]
                    if module_name in ['models', 'routes', 'forms', 'utils', 'config']:
                        imports.add(node.module)

    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}")

    return imports


def generate_module_dependency_graph():
    """
    Generate a graph showing module-level import dependencies.
    Each file is a node, and edges show imports between files.
    """
    print("\n=== Generating Module Dependency Graph ===")

    dot = Digraph(comment='Module Dependencies', format='png')
    dot.attr(rankdir='LR')
    dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')

    # Dictionary to store file -> imports mapping
    file_imports: Dict[str, Set[str]] = {}

    # Scan all Python source directories
    all_files = []
    for src_dir in PYTHON_SOURCE_DIRS:
        all_files.extend(get_python_files(src_dir))

    # Also check app.py and config.py
    if (PROJECT_ROOT / "app.py").exists():
        all_files.append(PROJECT_ROOT / "app.py")
    if (PROJECT_ROOT / "config.py").exists():
        all_files.append(PROJECT_ROOT / "config.py")

    print(f"Scanning {len(all_files)} Python files...")

    # Extract imports from each file
    for file_path in all_files:
        relative_path = file_path.relative_to(PROJECT_ROOT)
        module_name = str(relative_path).replace('/', '.').replace('.py', '')

        imports = extract_imports_from_file(file_path)
        if imports:
            file_imports[module_name] = imports

            # Add node for this file
            dot.node(module_name, module_name)

    # Add edges for imports
    edge_count = 0
    for module, imports in file_imports.items():
        for imported_module in imports:
            # Try to find the actual file being imported
            imported_file_name = None

            # Check if it's a direct match
            if imported_module in file_imports:
                imported_file_name = imported_module
            else:
                # Try to find partial matches (e.g., 'models.user' -> 'models.user')
                for other_module in file_imports.keys():
                    if imported_module in other_module or other_module in imported_module:
                        imported_file_name = other_module
                        break

            if imported_file_name and imported_file_name != module:
                dot.edge(module, imported_file_name)
                edge_count += 1

    # Generate the graph
    output_path = DOCS_DIR / "module_dependency_graph"
    dot.render(output_path, cleanup=True)

    print(f"✓ Generated module dependency graph with {len(file_imports)} nodes and {edge_count} edges")
    print(f"✓ Saved to: {output_path}.png")


def extract_classes_from_file(file_path: Path) -> List[Tuple[str, List[str]]]:
    """
    Extract class definitions and their base classes from a Python file.
    Returns list of tuples: (class_name, [base_class_names])
    """
    classes = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                base_classes = []

                for base in node.bases:
                    # Handle simple names like "Model"
                    if isinstance(base, ast.Name):
                        base_classes.append(base.id)
                    # Handle attribute access like "db.Model"
                    elif isinstance(base, ast.Attribute):
                        base_classes.append(base.attr)

                classes.append((class_name, base_classes))

    except Exception as e:
        print(f"Warning: Could not parse {file_path}: {e}")

    return classes


def generate_class_inheritance_graph():
    """
    Generate a graph showing class inheritance relationships.
    Each class is a node, edges point from child to parent.
    """
    print("\n=== Generating Class Inheritance Graph ===")

    dot = Digraph(comment='Class Inheritance', format='png')
    dot.attr(rankdir='BT')  # Bottom to top (child -> parent)
    dot.attr('node', shape='record', style='filled', fillcolor='lightgreen')

    # Dictionary to store all classes: {class_name: [parent_classes]}
    all_classes: Dict[str, List[str]] = {}
    class_to_file: Dict[str, str] = {}  # Track which file each class is in

    # Scan all Python source directories
    all_files = []
    for src_dir in PYTHON_SOURCE_DIRS:
        all_files.extend(get_python_files(src_dir))

    # Also check app.py
    if (PROJECT_ROOT / "app.py").exists():
        all_files.append(PROJECT_ROOT / "app.py")

    print(f"Scanning {len(all_files)} Python files for class definitions...")

    # Extract classes from each file
    for file_path in all_files:
        relative_path = file_path.relative_to(PROJECT_ROOT)
        module_name = str(relative_path).replace('/', '.').replace('.py', '')

        classes = extract_classes_from_file(file_path)
        for class_name, base_classes in classes:
            full_class_name = f"{module_name}.{class_name}"
            all_classes[class_name] = base_classes
            class_to_file[class_name] = module_name

    if not all_classes:
        print("Warning: No classes found in the project!")
        return

    # Add nodes for all classes
    for class_name, _ in all_classes.items():
        module = class_to_file.get(class_name, "unknown")
        label = f"{class_name}|{module}"
        dot.node(class_name, label)

    # Add edges for inheritance (child -> parent)
    edge_count = 0
    for class_name, parent_classes in all_classes.items():
        for parent in parent_classes:
            # Only create edges if the parent class is also in our project
            if parent in all_classes:
                dot.edge(class_name, parent, label='inherits')
                edge_count += 1
            else:
                # External base class (like db.Model, UserMixin, etc.)
                # Add it as a different colored node
                if parent not in dot.body:
                    dot.node(parent, parent, shape='ellipse', fillcolor='lightyellow')
                dot.edge(class_name, parent, style='dashed', label='extends')
                edge_count += 1

    # Generate the graph
    output_path = DOCS_DIR / "class_inheritance_graph"
    dot.render(output_path, cleanup=True)

    print(f"✓ Generated class inheritance graph with {len(all_classes)} classes and {edge_count} relationships")
    print(f"✓ Saved to: {output_path}.png")


def extract_template_relationships(file_path: Path) -> Tuple[List[str], List[str]]:
    """
    Extract template relationships from a Jinja2 HTML file.
    Returns tuple: ([extended_templates], [included_templates])
    """
    extends = []
    includes = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Match {% extends "template.html" %} or {% extends 'template.html' %}
        extends_pattern = r'{%\s*extends\s+["\']([^"\']+)["\']\s*%}'
        extends_matches = re.findall(extends_pattern, content)
        extends.extend(extends_matches)

        # Match {% include "template.html" %} or {% include 'template.html' %}
        include_pattern = r'{%\s*include\s+["\']([^"\']+)["\']\s*%}'
        include_matches = re.findall(include_pattern, content)
        includes.extend(include_matches)

    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")

    return extends, includes


def generate_template_relationship_graph():
    """
    Generate a graph showing template relationships (extends and includes).
    """
    print("\n=== Generating Template Relationship Graph ===")

    dot = Digraph(comment='Template Relationships', format='png')
    dot.attr(rankdir='TB')  # Top to bottom
    dot.attr('node', shape='note', style='filled', fillcolor='wheat')

    # Get all HTML template files
    if not TEMPLATES_DIR.exists():
        print(f"Error: Templates directory not found: {TEMPLATES_DIR}")
        return

    template_files = list(TEMPLATES_DIR.rglob("*.html"))
    print(f"Scanning {len(template_files)} template files...")

    # Dictionary to store template relationships
    template_relationships: Dict[str, Tuple[List[str], List[str]]] = {}

    # Extract relationships from each template
    for template_path in template_files:
        relative_path = template_path.relative_to(TEMPLATES_DIR)
        template_name = str(relative_path)

        extends, includes = extract_template_relationships(template_path)

        if extends or includes:
            template_relationships[template_name] = (extends, includes)

        # Add node for this template
        dot.node(template_name, template_name)

    # Add edges for relationships
    extends_count = 0
    includes_count = 0

    for template, (extends, includes) in template_relationships.items():
        # Add extends relationships (inheritance)
        for parent_template in extends:
            # Normalize path (remove leading './')
            parent_template = parent_template.lstrip('./')

            # Make sure the parent node exists
            if parent_template not in [node for node in dot.body if 'label' in node]:
                dot.node(parent_template, parent_template)

            dot.edge(template, parent_template, label='extends', color='blue', style='bold')
            extends_count += 1

        # Add include relationships (composition)
        for included_template in includes:
            # Normalize path
            included_template = included_template.lstrip('./')

            # Make sure the included node exists
            if included_template not in [node for node in dot.body if 'label' in node]:
                dot.node(included_template, included_template)

            dot.edge(template, included_template, label='includes', color='green', style='dashed')
            includes_count += 1

    # Generate the graph
    output_path = DOCS_DIR / "template_relationship_graph"
    dot.render(output_path, cleanup=True)

    print(f"✓ Generated template relationship graph with {len(template_files)} templates")
    print(f"  - {extends_count} extends relationships")
    print(f"  - {includes_count} include relationships")
    print(f"✓ Saved to: {output_path}.png")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Generate project visualization graphs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/generate_project_graph.py --type modules
  python scripts/generate_project_graph.py --type classes
  python scripts/generate_project_graph.py --type templates
        """
    )

    parser.add_argument(
        '--type',
        required=True,
        choices=['modules', 'classes', 'templates'],
        help='Type of graph to generate'
    )

    args = parser.parse_args()

    # Ensure docs directory exists
    ensure_docs_directory()

    # Generate the requested graph type
    if args.type == 'modules':
        generate_module_dependency_graph()
    elif args.type == 'classes':
        generate_class_inheritance_graph()
    elif args.type == 'templates':
        generate_template_relationship_graph()

    print("\n✓ Graph generation complete!")


if __name__ == '__main__':
    main()
