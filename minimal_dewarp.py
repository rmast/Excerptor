#!/usr/bin/env python3
"""
Minimal dewarp - alleen surface polynomial, geen perspective/rotation.
"""

import cv2
import numpy as np
from rebook.dewarp import go_dewarp, Kim2014

def minimal_dewarp_test(image_path, f_value=3500):
    """Test minimal dewarping - fix alleen surface shape."""
    
    print("=== MINIMAL DEWARP TEST ===")
    print("Aanpak: Forceer identity perspective, pas alleen surface polynomial aan")
    print()
    
    im = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    ctr = np.array([im.shape[1] / 2, im.shape[0] / 2])
    
    # Force identity rotation matrix
    def identity_R_theta(theta):
        """Always return identity matrix - no rotation."""
        return np.eye(3, dtype=np.float64)
    
    # Monkey patch
    import rebook.dewarp as dewarp_module
    original_R_theta = dewarp_module.R_theta
    dewarp_module.R_theta = identity_R_theta
    
    try:
        print("1. IDENTITY ROTATION + SURFACE TUNING")
        print("-" * 45)
        
        # Test verschillende surface aanpassingen zonder rotation
        test_configs = [
            {"name": "baseline", "curvature_adjust": 1.0},
            {"name": "flatten_05", "curvature_adjust": 0.95},
            {"name": "flatten_10", "curvature_adjust": 0.9},
            {"name": "flatten_15", "curvature_adjust": 0.85},
            {"name": "enhance_05", "curvature_adjust": 1.05},
            {"name": "enhance_10", "curvature_adjust": 1.1},
        ]
        
        for config in test_configs:
            print(f"Testing {config['name']} (curve={config['curvature_adjust']})...")
            
            surface_tuning = {
                'y_offset': 0.0,
                'curvature_adjust': config['curvature_adjust'],
                'threshold_mult': 1.0
            }
            
            try:
                result = go_dewarp(im, ctr, debug=False, 
                                 focal_length=f_value, surface_tuning=surface_tuning)
                
                if result and len(result) > 0:
                    output = result[0][0]
                    cv2.imwrite(f'dewarp/minimal_{config["name"]}.png', output)
                    print(f"  ✓ Saved: minimal_{config['name']}.png")
                
            except Exception as e:
                print(f"  ✗ Failed: {e}")
    
    finally:
        # Restore original
        dewarp_module.R_theta = original_R_theta
    
    print(f"\n2. RESULTAAT ANALYSE")
    print("-" * 25)
    print("🎯 Minimal dewarp zou moeten tonen:")
    print("   • Geen rotation/perspective changes")
    print("   • Alleen surface curvature effecten")
    print("   • Tekst blijft in correcte orientatie")
    print("   • Effect van polynomial shape op lokale 'deuk'")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python minimal_dewarp.py <image_path> [f_value]")
        sys.exit(1)
        
    image_path = sys.argv[1]
    f_value = int(sys.argv[2]) if len(sys.argv) > 2 else 3500
    
    minimal_dewarp_test(image_path, f_value)
