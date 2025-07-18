#!/usr/bin/env python3
"""
Focus op curvature adjustment - de parameter die daadwerkelijk effect heeft.
"""

import cv2
import numpy as np
from rebook.dewarp import go_dewarp

def test_curvature_range(image_path, f_value=3500):
    """Test systematisch curvature_adjust waarden."""
    
    im = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    ctr = np.array([im.shape[1] / 2, im.shape[0] / 2])
    
    print("=== CURVATURE ADJUSTMENT FOCUS ===")
    print("⚠️  WAARSCHUWING: Extreme curvature kan alignment verslechteren!")
    print("Doel: Groene lijnen parallel houden aan blauwe lijnen")
    print()
    
    # Meer conservatieve curvature testing
    test_configs = [
        {"name": "baseline", "curvature_adjust": 1.0},
        {"name": "minor_flatten", "curvature_adjust": 0.95},
        {"name": "slight_flatten", "curvature_adjust": 0.9},
        {"name": "moderate_flatten", "curvature_adjust": 0.85},
        {"name": "careful_flatten", "curvature_adjust": 0.8},
        {"name": "minor_curve", "curvature_adjust": 1.05},
        {"name": "slight_curve", "curvature_adjust": 1.1},
        {"name": "moderate_curve", "curvature_adjust": 1.15},
        {"name": "careful_curve", "curvature_adjust": 1.2},
    ]
    
    print("🎯 EVALUATIE CRITERIA:")
    print("1. Groene lijnen blijven parallel aan blauwe lijnen")
    print("2. Groene lijnen komen dichter bij blauwe lijnen")
    print("3. Geen extreme kromming/scheefstand")
    print()
    
    results = []
    
    for config in test_configs:
        print(f"\n=== Testing curvature_adjust={config['curvature_adjust']} ===")
        surface_tuning = {
            'y_offset': 0.0,  # Keep constant - has no effect
            'curvature_adjust': config['curvature_adjust'],
            'threshold_mult': 1.0
        }
        
        try:
            result = go_dewarp(im, ctr, debug=False, focal_length=f_value, surface_tuning=surface_tuning)
            print(f"✓ {config['name']} completed")
            
            import os
            if os.path.exists('dewarp/surface_lines.png'):
                os.rename('dewarp/surface_lines.png', f'dewarp/curvature_{config["name"]}.png')
            
            results.append((config['name'], config['curvature_adjust'], 'SUCCESS'))
                
        except Exception as e:
            print(f"✗ {config['name']} failed: {e}")
            results.append((config['name'], config['curvature_adjust'], f'FAILED: {e}'))
    
    print("\n" + "="*60)
    print("CURVATURE TUNING RESULTATEN:")
    print("="*60)
    for name, value, status in results:
        print(f"{name:15s} (curve={value:3.1f}): {status}")
    
    print("\n🎯 AANBEVELING:")
    print("Bekijk de curvature_*.png files om te zien welke waarde")
    print("de groene lijnen het best op de blauwe lijnen laat aansluiten!")
    print("Curvature adjust lijkt de primary tuning parameter te zijn.")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python focus_on_curvature.py <image_path> [f_value]")
        sys.exit(1)
        
    image_path = sys.argv[1] 
    f_value = int(sys.argv[2]) if len(sys.argv) > 2 else 3500
    
    test_curvature_range(image_path, f_value)
