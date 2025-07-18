#!/usr/bin/env python3
"""
Constrained dewarp - alleen lokale curvature correctie, geen extreme perspective changes.
"""

import cv2
import numpy as np
from rebook.dewarp import go_dewarp, Kim2014

def constrained_dewarp_test(image_path, f_value=3500):
    """Test constrained dewarping - geen extreme transformaties."""
    
    print("=== CONSTRAINED DEWARP TEST ===")
    print("Doel: Alleen lokale curvature correctie")
    print("Uitschakelen: Extreme perspective, spiegeling, rotatie")
    print()
    
    im = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    ctr = np.array([im.shape[1] / 2, im.shape[0] / 2])
    
    # Monkey patch om extreme transformaties te beperken
    original_initial_args = Kim2014.initial_args
    
    def constrained_initial_args(self):
        """Constrained initial args - voorkom extreme theta waarden."""
        result = original_initial_args(self)
        
        # Extract theta (eerste 3 parameters)
        theta = result[:3]
        print(f"Original theta: {theta}")
        
        # Limit theta to small values (no extreme rotations)
        max_theta = 0.1  # Ongeveer 6 graden
        theta_constrained = np.clip(theta, -max_theta, max_theta)
        
        print(f"Constrained theta: {theta_constrained}")
        
        # Replace theta in result
        result[:3] = theta_constrained
        
        return result
    
    # Monkey patch om tijdens optimization theta te beperken
    from rebook.dewarp import R_theta
    original_R_theta = R_theta
    
    def constrained_R_theta(theta):
        """Constrained rotation matrix - limit extreme rotations."""
        # Limit each component of theta
        max_component = 0.2  # Ongeveer 11 graden per as
        theta_limited = np.clip(theta, -max_component, max_component)
        
        return original_R_theta(theta_limited)
    
    # Apply monkey patches
    Kim2014.initial_args = constrained_initial_args
    import rebook.dewarp as dewarp_module
    dewarp_module.R_theta = constrained_R_theta
    
    try:
        print("1. CONSTRAINED GLOBAL DEWARP")
        print("-" * 35)
        
        surface_tuning = {'y_offset': 0.0, 'curvature_adjust': 1.0, 'threshold_mult': 1.0}
        
        result = go_dewarp(im, ctr, debug=True, focal_length=f_value, surface_tuning=surface_tuning)
        
        if result and len(result) > 0:
            constrained_output = result[0][0]
            cv2.imwrite('dewarp/constrained_global.png', constrained_output)
            print("✓ Constrained global saved: constrained_global.png")
            
            print("\n2. CONSTRAINED CURVATURE TESTS")
            print("-" * 40)
            
            # Test alleen curvature aanpassingen (geen extreme perspective)
            curve_values = [0.95, 0.9, 0.85, 1.05, 1.1]
            
            for curve_val in curve_values:
                print(f"Testing curvature_adjust={curve_val}...")
                
                surface_tuning_curve = {
                    'y_offset': 0.0,
                    'curvature_adjust': curve_val,
                    'threshold_mult': 1.0
                }
                
                try:
                    curve_result = go_dewarp(im, ctr, debug=False, 
                                           focal_length=f_value, surface_tuning=surface_tuning_curve)
                    
                    if curve_result and len(curve_result) > 0:
                        curve_output = curve_result[0][0]
                        cv2.imwrite(f'dewarp/constrained_curve_{curve_val:.2f}.png', curve_output)
                        print(f"  ✓ Saved: constrained_curve_{curve_val:.2f}.png")
                    
                except Exception as e:
                    print(f"  ✗ Failed: {e}")
        
    finally:
        # Restore original functions
        Kim2014.initial_args = original_initial_args
        dewarp_module.R_theta = original_R_theta
    
    print(f"\n3. EVALUATIE")
    print("-" * 15)
    print("🎯 Constrained results zouden moeten tonen:")
    print("   • Geen extreme rotaties/spiegelingen")
    print("   • Behoud van tekst orientatie")
    print("   • Alleen subtiele curvature correcties")
    print("   • Lokale 'deuk' correctie zonder globale verstoring")
    print()
    print("📊 Vergelijk met origineel om effect te zien van:")
    print("   • Theta limiting (rotation constraints)")
    print("   • Curvature-only adjustments")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python constrained_dewarp.py <image_path> [f_value]")
        sys.exit(1)
        
    image_path = sys.argv[1]
    f_value = int(sys.argv[2]) if len(sys.argv) > 2 else 3500
    
    constrained_dewarp_test(image_path, f_value)
