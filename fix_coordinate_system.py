#!/usr/bin/env python3
"""
Fix het fundamentele coördinaat systeem probleem tussen blauwe en groene lijnen.
"""

import cv2
import numpy as np
from rebook.dewarp import go_dewarp

def test_coordinate_fixes(image_path, f_value=3500):
    """Test verschillende coordinate system fixes."""
    
    im = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    ctr = np.array([im.shape[1] / 2, im.shape[0] / 2])
    
    print("=== VERBETERDE COÖRDINAAT SYSTEEM CORRECTIE ===")
    print("Bevindingen:")
    print("✓ Y-offset correctie werkt - groene lijnen dichter bij blauw")
    print("✗ Surface shape matching faalt - geen 'deuk' volgen")
    print("✗ Gradient error - onderin ~1 x-height afwijking")
    print()
    print("Nieuwe aanpak: Surface polynomial aanpassing")
    
    # Betere test configuraties gebaseerd op observaties
    test_configs = [
        # Basisline met Y-correctie
        {"name": "y_corrected", "y_offset": -3000.0, "curvature_adjust": 1.0, "description": "Y-positie gecorrigeerd"},
        
        # Surface shape experimenten
        {"name": "surface_adaptive", "y_offset": -3000.0, "curvature_adjust": 0.85, "description": "Minder extreme curvature"},
        {"name": "surface_gentle", "y_offset": -3000.0, "curvature_adjust": 0.9, "description": "Gentle curvature aanpassing"},
        {"name": "surface_fine", "y_offset": -3000.0, "curvature_adjust": 0.95, "description": "Fijne curvature tuning"},
        
        # Gradient correctie experimenten  
        {"name": "gradient_test1", "y_offset": -2800.0, "curvature_adjust": 1.0, "description": "Minder Y-correctie boven"},
        {"name": "gradient_test2", "y_offset": -3200.0, "curvature_adjust": 1.0, "description": "Meer Y-correctie onder"},
    ]
    
    results = []
    
    for config in test_configs:
        print(f"\n=== Testing {config['name']}: {config['description']} ===")
        surface_tuning = {
            'y_offset': config['y_offset'],
            'curvature_adjust': config['curvature_adjust'],
            'threshold_mult': 1.0
        }
        
        try:
            result = go_dewarp(im, ctr, debug=True, focal_length=f_value, surface_tuning=surface_tuning)
            print(f"✓ {config['name']} completed")
            
            import os
            if os.path.exists('dewarp/surface_lines.png'):
                os.rename('dewarp/surface_lines.png', f'dewarp/surface_match_{config["name"]}.png')
            
            results.append((config['name'], config['description'], 'SUCCESS'))
                
        except Exception as e:
            print(f"✗ {config['name']} failed: {e}")
            results.append((config['name'], config['description'], 'FAILED'))
    
    print("\n" + "="*80)
    print("SURFACE MATCHING RESULTATEN:")
    print("="*80)
    for name, desc, status in results:
        print(f"{name:15s}: {desc:30s} - {status}")
    
    print("\n🎯 EVALUATIE CRITERIA:")
    print("1. Volgen groene lijnen de 'deuk' in tekstregels? (cruciale test)")
    print("2. Blijft Y-afwijking constant over hele pagina?")
    print("3. Parallelliteit behouden tussen groen/blauw?")
    print("4. Scheve blauwe lijn links - is dit een indicator?")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python fix_coordinate_system.py <image_path> [f_value]")
        sys.exit(1)
        
    image_path = sys.argv[1] 
    f_value = int(sys.argv[2]) if len(sys.argv) > 2 else 3500
    
    test_coordinate_fixes(image_path, f_value)
