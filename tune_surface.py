#!/usr/bin/env python3
"""
Experimenteel script voor surface parameter tuning.
Doel: Groene lijnen dichter naar blauwe lijnen bewegen.
"""

import cv2
import numpy as np
from rebook.dewarp import go_dewarp

def test_surface_tuning(image_path, f_value=3500):
    """Test verschillende surface tuning parameters."""
    
    # Load test image
    im = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if im is None:
        print(f"Kan image niet laden: {image_path}")
        return
        
    ctr = np.array([im.shape[1] / 2, im.shape[0] / 2])
    
    # Test configuraties - inclusief threshold experiments
    test_configs = [
        # Baseline
        {"name": "baseline", "y_offset": 0.0, "curvature_adjust": 1.0, "threshold_mult": 1.0},
        
        # Threshold experiments (meer letters detecteren)
        {"name": "loose_threshold", "y_offset": 0.0, "curvature_adjust": 1.0, "threshold_mult": 0.8},
        {"name": "very_loose", "y_offset": 0.0, "curvature_adjust": 1.0, "threshold_mult": 0.6},
        {"name": "tight_threshold", "y_offset": 0.0, "curvature_adjust": 1.0, "threshold_mult": 1.5},
        
        # Surface tuning experiments
        {"name": "y_offset_up", "y_offset": -10.0, "curvature_adjust": 1.0, "threshold_mult": 1.0},
        {"name": "y_offset_down", "y_offset": 10.0, "curvature_adjust": 1.0, "threshold_mult": 1.0},
        {"name": "less_curve", "y_offset": 0.0, "curvature_adjust": 0.8, "threshold_mult": 1.0},
        {"name": "more_curve", "y_offset": 0.0, "curvature_adjust": 1.2, "threshold_mult": 1.0},
        
        # Combined experiments (threshold + surface)
        {"name": "loose_combined", "y_offset": -5.0, "curvature_adjust": 0.9, "threshold_mult": 0.8},
        {"name": "aggressive_detect", "y_offset": 0.0, "curvature_adjust": 1.0, "threshold_mult": 0.5},
    ]
    
    for config in test_configs:
        print(f"\n=== Testing {config['name']} ===")
        surface_tuning = {
            'y_offset': config['y_offset'],
            'curvature_adjust': config['curvature_adjust'],
            'threshold_mult': config['threshold_mult']
        }
        
        try:
            result = go_dewarp(
                im, ctr, 
                debug=True, 
                focal_length=f_value,
                surface_tuning=surface_tuning
            )
            print(f"✓ {config['name']} completed")
            
            # Rename debug output
            import os
            if os.path.exists('dewarp/surface_lines.png'):
                os.rename('dewarp/surface_lines.png', f'dewarp/surface_lines_{config["name"]}.png')
                
        except Exception as e:
            print(f"✗ {config['name']} failed: {e}")
            import traceback
            traceback.print_exc()  # Print full error traceback for debugging

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python tune_surface.py <image_path> [f_value]")
        sys.exit(1)
        
    image_path = sys.argv[1]
    f_value = int(sys.argv[2]) if len(sys.argv) > 2 else 3500
    
    test_surface_tuning(image_path, f_value)
