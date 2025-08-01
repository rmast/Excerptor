#!/bin/bash
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

if [ -f "analyze_line_difference.py" ]; then
    echo "Archiving: analyze_line_difference.py"
    mv "analyze_line_difference.py" dead_code_archive/
fi

if [ -f "analyze_quick.py" ]; then
    echo "Archiving: analyze_quick.py"
    mv "analyze_quick.py" dead_code_archive/
fi

if [ -f "analyze_results.py" ]; then
    echo "Archiving: analyze_results.py"
    mv "analyze_results.py" dead_code_archive/
fi

if [ -f "batch_resize_aspect.py" ]; then
    echo "Archiving: batch_resize_aspect.py"
    mv "batch_resize_aspect.py" dead_code_archive/
fi

if [ -f "compare_results.py" ]; then
    echo "Archiving: compare_results.py"
    mv "compare_results.py" dead_code_archive/
fi

if [ -f "constrained_dewarp.py" ]; then
    echo "Archiving: constrained_dewarp.py"
    mv "constrained_dewarp.py" dead_code_archive/
fi

if [ -f "demo.py" ]; then
    echo "Archiving: demo.py"
    mv "demo.py" dead_code_archive/
fi

if [ -f "fix_coordinate_system.py" ]; then
    echo "Archiving: fix_coordinate_system.py"
    mv "fix_coordinate_system.py" dead_code_archive/
fi

if [ -f "fix_l_m_initialization.py" ]; then
    echo "Archiving: fix_l_m_initialization.py"
    mv "fix_l_m_initialization.py" dead_code_archive/
fi

if [ -f "focus_on_curvature.py" ]; then
    echo "Archiving: focus_on_curvature.py"
    mv "focus_on_curvature.py" dead_code_archive/
fi

if [ -f "hybrid_dewarp.py" ]; then
    echo "Archiving: hybrid_dewarp.py"
    mv "hybrid_dewarp.py" dead_code_archive/
fi

if [ -f "inspect_export.py" ]; then
    echo "Archiving: inspect_export.py"
    mv "inspect_export.py" dead_code_archive/
fi

if [ -f "landscape_fixed_dewarp.py" ]; then
    echo "Archiving: landscape_fixed_dewarp.py"
    mv "landscape_fixed_dewarp.py" dead_code_archive/
fi

if [ -f "minimal_dewarp.py" ]; then
    echo "Archiving: minimal_dewarp.py"
    mv "minimal_dewarp.py" dead_code_archive/
fi

if [ -f "monitor_experiment.py" ]; then
    echo "Archiving: monitor_experiment.py"
    mv "monitor_experiment.py" dead_code_archive/
fi

if [ -f "orientation_test.py" ]; then
    echo "Archiving: orientation_test.py"
    mv "orientation_test.py" dead_code_archive/
fi

if [ -f "simple_curve_correction.py" ]; then
    echo "Archiving: simple_curve_correction.py"
    mv "simple_curve_correction.py" dead_code_archive/
fi

if [ -f "simple_landscape_dewarp.py" ]; then
    echo "Archiving: simple_landscape_dewarp.py"
    mv "simple_landscape_dewarp.py" dead_code_archive/
fi

if [ -f "surface_only_dewarp.py" ]; then
    echo "Archiving: surface_only_dewarp.py"
    mv "surface_only_dewarp.py" dead_code_archive/
fi

if [ -f "test_focal_sweep.py" ]; then
    echo "Archiving: test_focal_sweep.py"
    mv "test_focal_sweep.py" dead_code_archive/
fi

if [ -f "test_single.py" ]; then
    echo "Archiving: test_single.py"
    mv "test_single.py" dead_code_archive/
fi

if [ -f "tune_surface.py" ]; then
    echo "Archiving: tune_surface.py"
    mv "tune_surface.py" dead_code_archive/
fi

if [ -f "collate.pyx" ]; then
    echo "Archiving: collate.pyx"
    mv "collate.pyx" dead_code_archive/
fi

if [ -f "feature_sign.pyx" ]; then
    echo "Archiving: feature_sign.pyx"
    mv "feature_sign.pyx" dead_code_archive/
fi

if [ -f "inpaint.pyx" ]; then
    echo "Archiving: inpaint.pyx"
    mv "inpaint.pyx" dead_code_archive/
fi

if [ -f "newton.pyx" ]; then
    echo "Archiving: newton.pyx"
    mv "newton.pyx" dead_code_archive/
fi

if [ -f "collate.cpython-*.so" ]; then
    echo "Archiving: collate.cpython-*.so"
    mv "collate.cpython-*.so" dead_code_archive/
fi

if [ -f "feature_sign.cpython-*.so" ]; then
    echo "Archiving: feature_sign.cpython-*.so"
    mv "feature_sign.cpython-*.so" dead_code_archive/
fi

if [ -f "inpaint.cpython-*.so" ]; then
    echo "Archiving: inpaint.cpython-*.so"
    mv "inpaint.cpython-*.so" dead_code_archive/
fi

if [ -f "newton.cpython-*.so" ]; then
    echo "Archiving: newton.cpython-*.so"
    mv "newton.cpython-*.so" dead_code_archive/
fi

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
