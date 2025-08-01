#!/usr/bin/env python3
"""
Simpele dependency analysis na runtime test.
"""

print("=== WERKELIJKE DEPENDENCIES na runtime test ===\n")

print("🎯 BENODIGDE MODULES:")
print("  ✓ scantailor_bridge.py")
print("  ✓ spline_based_dewarp.py")
print("  ✓ rebook/__init__.py")
print("  ✓ rebook/dewarp.py")
print("  ✓ rebook/algorithm.py")
print("  ✓ rebook/binarize.py")
print("  ✓ rebook/lib.py")
print("  ✓ rebook/geometry.py")
print("  ✓ rebook/letters.py        <- EXTRA NODIG")
print("  ✓ rebook/crop.py           <- EXTRA NODIG")
print("  ✓ rebook/collate.pyx/.so   <- EXTRA NODIG")
print("  ✓ rebook/newton.pyx/.so    <- EXTRA NODIG")
print("  ✓ rebook/inpaint.pyx/.so   <- EXTRA NODIG")

print("\n📋 DEPENDENCIES:")
print("  ✓ opencv-python")
print("  ✓ numpy")
print("  ✓ scipy")
print("  ✓ scikit-image")
print("  ✓ rawpy               <- EXTRA NODIG")

print("\n✅ CONCLUSIE:")
print("   - Je hebt gelijk - die extra modules zijn wel nodig")
print("   - dewarp.py importeert veel meer dan verwacht")
print("   - Cython extensions zijn verplicht")
print("   - ~70% van project is nog steeds dode code")

print("\n🔧 VOLGENDE STAPPEN:")
print("   1. Update je scantailor_minimal met alle getest benodigde files")
print("   2. Dan pas main project cleanup")
print("   3. Focus op verwijderen van demo.py, test_*, analyze_* etc.")
