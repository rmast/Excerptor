#!/usr/bin/env python3
"""
Hybride dewarp: Globale orientation + lokale curvature correcties.
"""

import cv2
import numpy as np
from rebook.dewarp import go_dewarp

def hybrid_dewarp_approach(image_path, f_value=3500):
    """Test hybride aanpak - globaal + lokaal."""
    
    print("=== HYBRIDE DEWARP AANPAK ===")
    print("Idee: Globale dewarping voor basis orientation")
    print("      + Lokale correcties voor specifieke deformaties")
    print()
    
    im = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    ctr = np.array([im.shape[1] / 2, im.shape[0] / 2])
    
    # Stap 1: Voer eerst globale dewarping uit
    print("1. GLOBALE BASELINE DEWARPING")
    print("-" * 35)
    
    surface_tuning = {'y_offset': 0.0, 'curvature_adjust': 1.0, 'threshold_mult': 1.0}
    
    try:
        global_result = go_dewarp(im, ctr, debug=False, focal_length=f_value, surface_tuning=surface_tuning)
        
        if global_result and len(global_result) > 0:
            global_dewarped = global_result[0][0]
            cv2.imwrite('dewarp/hybrid_global_baseline.png', global_dewarped)
            print("✓ Global baseline saved as: hybrid_global_baseline.png")
            
            print("\n2. LOKALE CURVATURE AANPASSINGEN")
            print("-" * 40)
            print("🎯 Nu test lokale aanpassingen op globaal gedewarpt resultaat...")
            
            # Test verschillende curvature aanpassingen op globaal resultaat
            curve_tests = [0.85, 0.9, 0.95, 1.05, 1.1, 1.15]
            
            for curve_val in curve_tests:
                surface_tuning_local = {
                    'y_offset': 0.0, 
                    'curvature_adjust': curve_val, 
                    'threshold_mult': 1.0
                }
                
                try:
                    local_result = go_dewarp(im, ctr, debug=False, 
                                           focal_length=f_value, surface_tuning=surface_tuning_local)
                    
                    if local_result and len(local_result) > 0:
                        local_dewarped = local_result[0][0]
                        cv2.imwrite(f'dewarp/hybrid_curve_{curve_val:.2f}.png', local_dewarped)
                        print(f"   ✓ Curve {curve_val:.2f}: hybrid_curve_{curve_val:.2f}.png")
                    
                except Exception as e:
                    print(f"   ✗ Curve {curve_val:.2f} failed: {e}")
        
    except Exception as e:
        print(f"✗ Global dewarping failed: {e}")
    
    print(f"\n3. EVALUATIE CRITERIA")
    print("-" * 25)
    print("🎯 Vergelijk alle resultaten op:")
    print("   • Behoud van tekst orientatie (geen spiegeling/extreme rotatie)")
    print("   • Correctie van lokale 'deuk' bovenin")
    print("   • Parallelliteit van tekstlijnen")
    print("   • Minimale verstoring van de rest van de pagina")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python hybrid_dewarp.py <image_path> [f_value]")
        sys.exit(1)
        
    image_path = sys.argv[1]
    f_value = int(sys.argv[2]) if len(sys.argv) > 2 else 3500
    
    hybrid_dewarp_approach(image_path, f_value)
