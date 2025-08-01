#!/usr/bin/env python3
"""
Maak een minimal scantailor_bridge package met alleen benodigde code.
"""

import shutil
import os
from pathlib import Path

def create_minimal_bridge():
    """Create minimal scantailor bridge package."""
    
    print("=== CREATING MINIMAL SCANTAILOR BRIDGE ===\n")
    
    # Create minimal directory
    minimal_dir = Path('scantailor_minimal')
    minimal_dir.mkdir(exist_ok=True)
    
    # Core files die zeker nodig zijn
    essential_files = [
        'scantailor_bridge.py',
        'spline_based_dewarp.py',  # Voor identify_textblocks_smart
        'requirements.txt',
        'setup.py',  # Mogelijk nodig voor Cython
    ]
    
    # Rebook modules die nodig zijn
    rebook_dir = minimal_dir / 'rebook'
    rebook_dir.mkdir(exist_ok=True)
    
    rebook_files = [
        'rebook/__init__.py',
        'rebook/dewarp.py',      # Voor get_AH_lines
        'rebook/algorithm.py',   # Gebruikt door dewarp
        'rebook/binarize.py',    # Voor sauvola_noisy
        'rebook/lib.py',         # Voor debug flags
        'rebook/geometry.py',    # Mogelijk gebruikt door algorithm
    ]
    
    print("Copying essential files...")
    for file_path in essential_files:
        src = Path(file_path)
        if src.exists():
            dst = minimal_dir / src.name
            shutil.copy2(src, dst)
            print(f"✓ {file_path}")
        else:
            print(f"❌ {file_path} - NOT FOUND")
    
    print("\nCopying rebook modules...")
    for file_path in rebook_files:
        src = Path(file_path)
        if src.exists():
            dst = minimal_dir / file_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"✓ {file_path}")
        else:
            print(f"❌ {file_path} - NOT FOUND")
    
    # Create minimal requirements.txt
    minimal_requirements = [
        "opencv-python",
        "numpy",
        "scikit-image",
        "scipy",  # Mogelijk nodig voor interpolatie
        "pathlib",  # (meestal stdlib)"
    ]
    
    with open(minimal_dir / 'requirements_minimal.txt', 'w') as f:
        for req in minimal_requirements:
            f.write(f"{req}\n")
    
    print(f"\n✓ Created minimal package in: {minimal_dir}")
    print(f"  Files copied: {len(essential_files + rebook_files)}")
    
    # Test the minimal package
    print("\n=== TESTING MINIMAL PACKAGE ===")
    os.chdir(minimal_dir)
    
    try:
        # Test import
        import sys
        sys.path.insert(0, '.')
        
        print("Testing imports...")
        import scantailor_bridge
        print("✓ scantailor_bridge imported successfully")
        
        # Test if main functions are available
        if hasattr(scantailor_bridge, 'export_for_scantailor'):
            print("✓ export_for_scantailor function found")
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
    
    os.chdir('..')
    
    return minimal_dir

def create_cleanup_script():
    """Create script to safely remove dead code from main project."""
    
    dead_files = [
        'analyze_line_difference.py',
        'analyze_quick.py', 
        'analyze_results.py',
        'batch_resize_aspect.py',
        'compare_results.py',
        'constrained_dewarp.py',
        'demo.py',
        'fix_coordinate_system.py',
        'fix_l_m_initialization.py',
        'focus_on_curvature.py',
        'hybrid_dewarp.py',
        'inspect_export.py',
        'landscape_fixed_dewarp.py',
        'minimal_dewarp.py',
        'monitor_experiment.py',
        'orientation_test.py',
        'simple_curve_correction.py',
        'simple_landscape_dewarp.py',
        'surface_only_dewarp.py',
        'test_focal_sweep.py',
        'test_single.py',
        'tune_surface.py',
        # Cython files
        'collate.pyx',
        'feature_sign.pyx', 
        'inpaint.pyx',
        'newton.pyx',
        # Compiled extensions
        'collate.cpython-*.so',
        'feature_sign.cpython-*.so',
        'inpaint.cpython-*.so', 
        'newton.cpython-*.so',
    ]
    
    cleanup_script = '''#!/bin/bash
# Safe cleanup script - BACKUP FIRST!

echo "=== EXCERPTORO3 DEAD CODE CLEANUP ==="
echo "This will remove dead code not needed for scantailor_bridge.py"
echo ""
echo "⚠️  MAKE SURE YOU HAVE A BACKUP FIRST!"
read -p "Continue? (y/N): " confirm

if [[ $confirm != [yY] ]]; then
    echo "Cancelled."
    exit 1
fi

# Create archive of dead code before deletion
echo "Creating archive of dead code..."
mkdir -p dead_code_archive
'''
    
    for file in dead_files:
        cleanup_script += f'''
if [ -f "{file}" ]; then
    echo "Archiving: {file}"
    mv "{file}" dead_code_archive/
fi
'''
    
    cleanup_script += '''
# Remove test directories 
echo "Archiving test directories..."
for dir in test_* archive_* analyze cache out-dewarped dewarped_img; do
    if [ -d "$dir" ]; then
        echo "Archiving directory: $dir"
        mv "$dir" dead_code_archive/
    fi
done

# Clean build artifacts
echo "Cleaning build artifacts..."
rm -rf build/ __pycache__/ rebook/__pycache__/
find . -name "*.pyc" -delete

echo ""
echo "✅ Cleanup complete!"
echo "   Dead code archived in: dead_code_archive/"
echo "   Remaining files focused on scantailor_bridge functionality"
echo ""
echo "Next steps:"
echo "1. Test: python scantailor_bridge.py 'path/to/test/image.tif'"
echo "2. Update requirements.txt if needed"
echo "3. Remove any remaining unused dependencies"
'''
    
    with open('cleanup_dead_code.sh', 'w') as f:
        f.write(cleanup_script)
    
    os.chmod('cleanup_dead_code.sh', 0o755)
    print("✓ Created cleanup_dead_code.sh")

if __name__ == '__main__':
    minimal_dir = create_minimal_bridge()
    create_cleanup_script()
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"1. Test minimal package: cd {minimal_dir} && python scantailor_bridge.py test_image.tif")
    print(f"2. If working, run: ./cleanup_dead_code.sh")
    print(f"3. Update main requirements.txt to remove unused deps")
    print(f"4. Update README.md to reflect new scope")