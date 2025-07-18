#!/usr/bin/env python3
"""
Fix de l_m parameter initialisatie - het echte probleem.
"""

import cv2
import numpy as np
from rebook.dewarp import go_dewarp

def analyze_l_m_problem(image_path, f_value=3500):
    """Analyseer en fix het l_m initialisatie probleem."""
    
    print("=== L_M INITIALISATIE PROBLEEM ===")
    print("Analyse toont: l_m waarden ~3000-4000, tekst Y ~500-1573")
    print("Verschil van ~3000 pixels suggereert coordinate transform fout")
    print()
    print("Mogelijke oorzaken:")
    print("1. initial_args() berekent l_m verkeerd")
    print("2. Ys.mean() gebruikt verkeerde coördinaten")
    print("3. Surface projectie transformatie incorrect")
    print("4. Of coordinate systeem inconsistentie")
    print()
    
    # In plaats van surface tuning, laten we de l_m berekening intercepten
    print("ACTIE: Monkey patch initial_args voor correcte l_m berekening")
    
    from rebook.dewarp import Kim2014
    original_initial_args = Kim2014.initial_args
    
    def fixed_initial_args(self):
        """Fixed versie van initial_args met correcte l_m berekening."""
        print("\n🔧 FIXED L_M CALCULATION:")
        
        # Call original voor alle andere parameters
        result = original_initial_args(self)
        
        # Extract l_m values (laatste deel van result array)
        n_params_before_lm = 3 + 13 + 2 + 1  # theta + a_m + align + T
        l_m_start = n_params_before_lm
        original_l_m = result[l_m_start:]
        
        print(f"Original l_m waarden: {original_l_m[:5]}...")
        print(f"Original l_m bereik: {original_l_m.min():.1f} - {original_l_m.max():.1f}")
        
        # Bereken correcte l_m op basis van werkelijke tekst Y-posities
        corrected_l_m = []
        for line in self.lines:
            base_points = line.base_points()
            line_y = base_points[:, 1].mean()
            corrected_l_m.append(line_y)
        
        corrected_l_m = np.array(corrected_l_m)
        print(f"Corrected l_m waarden: {corrected_l_m[:5]}...")
        print(f"Corrected l_m bereik: {corrected_l_m.min():.1f} - {corrected_l_m.max():.1f}")
        print(f"Correctie verschil: {np.mean(original_l_m - corrected_l_m):.1f} pixels")
        
        # Replace l_m in result
        result[l_m_start:] = corrected_l_m
        
        return result
    
    # Apply monkey patch
    Kim2014.initial_args = fixed_initial_args
    
    try:
        im = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        ctr = np.array([im.shape[1] / 2, im.shape[0] / 2])
        
        surface_tuning = {'y_offset': 0.0, 'curvature_adjust': 1.0, 'threshold_mult': 1.0}
        
        print("\n=== TESTING FIXED L_M INITIALIZATION ===")
        result = go_dewarp(im, ctr, debug=True, focal_length=f_value, surface_tuning=surface_tuning)
        print("✓ Fixed l_m test completed")
        
        import os
        if os.path.exists('dewarp/surface_lines.png'):
            os.rename('dewarp/surface_lines.png', 'dewarp/fixed_l_m_result.png')
            print("📊 Result saved as: dewarp/fixed_l_m_result.png")
        
    finally:
        # Restore original
        Kim2014.initial_args = original_initial_args
    
    print("\n🎯 VERWACHTING:")
    print("Als l_m fix correct is, zouden groene lijnen veel dichter")
    print("bij blauwe lijnen moeten staan in fixed_l_m_result.png")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python fix_l_m_initialization.py <image_path> [f_value]")
        sys.exit(1)
        
    image_path = sys.argv[1] 
    f_value = int(sys.argv[2]) if len(sys.argv) > 2 else 3500
    
    analyze_l_m_problem(image_path, f_value)
