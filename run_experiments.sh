#!/bin/bash

# Experimenteel script voor systematische filter-vergelijking
# Dit script runt dezelfde test met verschillende filter-instellingen

echo "=== Experimentele Filter Vergelijking ==="
echo "Test afbeelding: book/"
echo "Datum: $(date)"
echo ""

# Maak output directories
mkdir -p test_std test_exp

echo "1. Test met standaard filters..."
python demo.py -d -i book -vt --scantailor-split -o test_std -a test_archive -n test_std.md

echo ""
echo "2. Test met experimentele filters..."
python demo.py -d -i book -vt --scantailor-split -o test_exp -a test_archive -n test_exp.md -ef

echo ""
echo "=== Vergelijking compleet ==="
echo "Resultaten:"
echo "- Standaard: test_std/"
echo "- Experimenteel: test_exp/"
echo "- Debug images: dewarp/"
echo ""
echo "Bekijk de volgende bestanden voor analyse:"
echo "- dewarp/all_lines.png (rode=alle lijnen, blauwe=gebruikte lijnen)"
echo "- dewarp/surface_lines.png (groene=3D oppervlaklijnen)"
echo "- test_std/*_dewarped.* vs test_exp/*_dewarped.*"
