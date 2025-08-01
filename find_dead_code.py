#!/usr/bin/env python3
"""
Trace alle dependencies van scantailor_bridge.py om dode code te identificeren.
"""

import ast
import os
import sys
from pathlib import Path

def extract_imports(file_path):
    """Extract alle imports uit een Python file."""
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(('import', alias.name, None))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(('from', module, alias.name))
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return imports

def find_local_dependencies(imports, project_root):
    """Filter imports voor lokale project modules."""
    local_deps = []
    
    for imp_type, module, name in imports:
        if imp_type == 'import':
            # Check if it's a local module
            if module.startswith('rebook') or Path(project_root / f"{module}.py").exists():
                local_deps.append(module)
        elif imp_type == 'from':
            if module.startswith('rebook') or Path(project_root / f"{module}.py").exists():
                local_deps.append(module)
    
    return local_deps

def trace_dependencies(start_file, project_root, visited=None):
    """Recursively trace alle dependencies."""
    if visited is None:
        visited = set()
    
    if start_file in visited:
        return visited
    
    visited.add(start_file)
    print(f"Analyzing: {start_file}")
    
    file_path = project_root / start_file
    if not file_path.exists():
        # Try with .py extension
        file_path = project_root / f"{start_file}.py"
        if not file_path.exists():
            print(f"  File not found: {start_file}")
            return visited
    
    imports = extract_imports(file_path)
    local_deps = find_local_dependencies(imports, project_root)
    
    print(f"  Local imports: {local_deps}")
    
    for dep in local_deps:
        trace_dependencies(dep, project_root, visited)
    
    return visited

def find_dead_code(project_root):
    """Find alle Python files die niet gebruikt worden door scantailor_bridge."""
    
    print("=== DEPENDENCY TRACE voor scantailor_bridge.py ===\n")
    
    # Start trace vanaf scantailor_bridge.py
    needed_files = trace_dependencies('scantailor_bridge.py', project_root)
    
    print("\n=== BENODIGDE FILES ===")
    for f in sorted(needed_files):
        print(f"✓ {f}")
    
    print("\n=== DODE CODE DETECTIE ===")
    
    # Find alle Python files in project
    all_py_files = []
    for py_file in project_root.rglob("*.py"):
        rel_path = py_file.relative_to(project_root)
        all_py_files.append(str(rel_path))
    
    # Filter obvious dead code
    dead_files = []
    for py_file in all_py_files:
        # Skip __pycache__ etc
        if '__pycache__' in py_file or py_file.startswith('.'):
            continue
            
        # Check if needed
        file_stem = py_file.replace('.py', '').replace('/', '.')
        if py_file not in needed_files and file_stem not in needed_files:
            # Additional checks for obvious dead code
            if any(pattern in py_file for pattern in [
                'demo.py', 'test_', 'fix_', 'tune_', 'analyze_', 'compare_',
                'monitor_', 'inspect_', 'batch_', 'focus_', 'simple_',
                'landscape_', 'surface_', 'hybrid_', 'constrained_',
                'minimal_', 'spline_', 'orientation_'
            ]):
                dead_files.append(py_file)
    
    print("\n🗑️  WAARSCHIJNLIJK DODE CODE:")
    for f in sorted(dead_files):
        print(f"❌ {f}")
    
    # Check Cython files
    print("\n=== CYTHON EXTENSIONS CHECK ===")
    cython_files = list(project_root.glob("*.pyx"))
    for pyx_file in cython_files:
        module_name = pyx_file.stem
        # Check if imported anywhere in needed files
        used = False
        for needed_file in needed_files:
            try:
                file_path = project_root / needed_file
                if not file_path.exists():
                    file_path = project_root / f"{needed_file}.py"
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if module_name in content:
                            used = True
                            break
            except:
                pass
        
        if used:
            print(f"✓ {pyx_file.name} - GEBRUIKT")
        else:
            print(f"❌ {pyx_file.name} - WAARSCHIJNLIJK ONGEBRUIKT")
    
    print(f"\n📊 STATISTIEKEN:")
    print(f"   Totaal Python files: {len(all_py_files)}")
    print(f"   Benodigde files: {len(needed_files)}")
    print(f"   Waarschijnlijk dode files: {len(dead_files)}")
    print(f"   Potentiële cleanup: {len(dead_files)/len(all_py_files)*100:.1f}%")

if __name__ == '__main__':
    project_root = Path('.')
    find_dead_code(project_root)