#!/usr/bin/env python3
"""
Verbeterde dependency analysis voor scantailor_bridge.py
Gebaseerd op runtime test resultaten.
"""

def print_corrected_dependencies():
    """Print de werkelijke dependencies die nodig zijn."""
    
    print("=== CORRECTED DEPENDENCY ANALYSIS ===\n")
    
    print("🎯 WERKELIJK BENODIGDE MODULES (na runtime test):")
    
    # Core bridge
    print("\n📄 Main bridge:")
    print("  ✓ scantailor_bridge.py")
    print("  ✓ spline_based_dewarp.py")
    
    # Rebook modules - COMPLETE set
    print("\n📦 rebook/ package:")
    essential_rebook = [
        "rebook/__init__.py",
        "rebook/dewarp.py",        # Main dewarping (imports veel andere modules)
        "rebook/algorithm.py",     # Text line detection
        "rebook/binarize.py",      # Sauvola binarization
        "rebook/lib.py",           # Debug utilities, colors, drawing
        "rebook/geometry.py",      # Crop class en geometric primitives
        "rebook/letters.py",       # Letter/TextLine classes (gebruikt door algorithm)
        "rebook/crop.py",          # Crop utilities (gebruikt door dewarp)
    ]
    
    for module in essential_rebook:
        print(f"  ✓ {module}")
    
    # Cython extensions - NEEDED!
    print("\n⚙️  Cython extensions (compiled modules):")
    cython_modules = [
        "rebook/collate.pyx + .so",    # Text collation (gebruikt door dewarp)
        "rebook/newton.pyx + .so",     # Newton optimization (gebruikt door dewarp)
        "rebook/inpaint.pyx + .so",    # Image inpainting (mogelijk gebruikt)
    ]
    
    for module in cython_modules:
        print(f"  ✓ {module}")
    
    # Dependencies
    print("\n📋 Python dependencies:")
    required_deps = [
        "opencv-python",     # CV2 - computer vision
        "numpy",            # Numerical computing
        "scipy",            # Scientific computing (optimize, interpolate)
        "scikit-image",     # Image processing (ransac)
        "rawpy",            # RAW image processing
        # "pathlib" is stdlib
    ]
    
    for dep in required_deps:
        print(f"  ✓ {dep}")
    
    print("\n❌ DEFINITIEVE DODE CODE (na correctie):")
    dead_code = [
        "demo.py",                    # Main app met OCR - NIET NODIG
        "rebook/batch.py",           # Batch processing - NIET NODIG  
        "rebook/spliter.py",         # Page splitting - NIET NODIG
        "rebook/upscale.py",         # Super resolution - NIET NODIG
        "rebook/block.py",           # Text structuring - NIET NODIG
        "rebook/sparse_rep.py",      # Sparse representation - NIET NODIG
        "rebook/training.py",        # ML training - NIET NODIG
        "alle test_*.py scripts",    # Test scripts - NIET NODIG
        "alle fix_*.py scripts",     # Debug scripts - NIET NODIG
        "alle analyze_*.py scripts", # Analysis scripts - NIET NODIG
    ]
    
    for item in dead_code:
        print(f"  ❌ {item}")
    
    print(f"\n📊 HERZIENDE STATISTIEKEN:")
    print(f"   Benodigde core modules: ~8-10 Python files")
    print(f"   Benodigde Cython extensions: 3")
    print(f"   Benodigde dependencies: 5")
    print(f"   Schatting: ~70% van originele project is nog steeds dode code")
    
    print(f"\n🔧 AANBEVELING:")
    print(f"   1. Update create_minimal.py om alle benodigde rebook modules te kopiëren")
    print(f"   2. Zorg dat Cython extensions ook gekopieerd/gecompileerd worden")
    print(f"   3. Test nogmaals na volledige setup")
    print(f"   4. Dan pas main project cleanup doen")

def create_corrected_minimal_setup():
    """Create corrected setup voor minimal bridge."""
    
    script_content = '''#!/usr/bin/env python3
"""
CORRECTED minimal setup voor scantailor bridge.
Gebaseerd op runtime dependency test.
"""

import shutil
import os
from pathlib import Path

def create_corrected_minimal():
    """Create complete minimal package met alle benodigde dependencies."""
    
    print("=== CORRECTED MINIMAL SCANTAILOR BRIDGE ===\\n")
    
    minimal_dir = Path('scantailor_minimal_v2')
    minimal_dir.mkdir(exist_ok=True)
    
    # Core bridge files
    core_files = [
        'scantailor_bridge.py',
        'spline_based_dewarp.py',
    ]
    
    # COMPLETE rebook module set
    rebook_files = [
        'rebook/__init__.py',
        'rebook/dewarp.py',
        'rebook/algorithm.py', 
        'rebook/binarize.py',
        'rebook/lib.py',
        'rebook/geometry.py',
        'rebook/letters.py',      # TOEGEVOEGD - nodig voor algorithm
        'rebook/crop.py',         # TOEGEVOEGD - nodig voor dewarp
    ]
    
    # Cython extensions - source EN compiled
    cython_files = [
        'rebook/collate.pyx',
        'rebook/collate.cpython-*.so',
        'rebook/newton.pyx', 
        'rebook/newton.cpython-*.so',
        'rebook/inpaint.pyx',
        'rebook/inpaint.cpython-*.so',
    ]
    
    print("Copying core files...")
    for file_path in core_files:
        src = Path(file_path)
        if src.exists():
            dst = minimal_dir / src.name
            shutil.copy2(src, dst)
            print(f"✓ {file_path}")
    
    print("\\nCopying complete rebook module...")
    rebook_dst = minimal_dir / 'rebook'
    rebook_dst.mkdir(exist_ok=True)
    
    for file_path in rebook_files:
        src = Path(file_path)
        if src.exists():
            dst = minimal_dir / file_path
            shutil.copy2(src, dst)
            print(f"✓ {file_path}")
    
    print("\\nCopying Cython extensions...")
    import glob
    for pattern in cython_files:
        matches = glob.glob(pattern)
        for match in matches:
            src = Path(match)
            dst = minimal_dir / match
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"✓ {match}")
    
    # Corrected requirements
    requirements = [
        "opencv-python",
        "numpy", 
        "scipy",
        "scikit-image",
        "rawpy",
        "# Cython only needed for building extensions",
        "# Cython",
    ]
    
    with open(minimal_dir / 'requirements_corrected.txt', 'w') as f:
        for req in requirements:
            f.write(f"{req}\\n")
    
    # Test script
    test_script = f'''#!/bin/bash
# Test script for minimal bridge
cd {minimal_dir}
echo "Installing requirements..."
pip install -r requirements_corrected.txt

echo "Testing bridge..."
python scantailor_bridge.py '../book/Scan_20250618 (8)_1L.tif' || echo "Test failed - check missing dependencies"
'''
    
    with open('test_minimal_v2.sh', 'w') as f:
        f.write(test_script)
    os.chmod('test_minimal_v2.sh', 0o755)
    
    print(f"\\n✅ Created corrected minimal package: {minimal_dir}")
    print(f"   Test with: ./test_minimal_v2.sh")
    
    return minimal_dir

if __name__ == '__main__':
    create_corrected_minimal()
'''
    
    with open('create_minimal_corrected.py', 'w') as f:
        f.write(script_content)
    
    print("✓ Created create_minimal_corrected.py")

if __name__ == '__main__':
    print_corrected_dependencies()
    create_corrected_minimal_setup()
