#!/usr/bin/env python3
"""
Simple curve correction - gebruik OpenCV transforms in plaats van Kim2014.
"""

import cv2
import numpy as np

def simple_curve_test(image_path):
    """Test simpele curve correctie zonder complex algoritme."""
    
    print("=== SIMPLE CURVE CORRECTION ===")
    print("Aanpak: Gebruik OpenCV barrel/pincushion distortion correctie")
    print("        voor lokale 'deuk' zonder perspective/rotation")
    print()
    
    im = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    h, w = im.shape[:2]
    
    # Camera matrix (simplified)
    camera_matrix = np.array([
        [w/2, 0, w/2],
        [0, h/2, h/2], 
        [0, 0, 1]
    ], dtype=np.float32)
    
    # Test verschillende distortion parameters
    test_configs = [
        {"name": "baseline", "k1": 0.0, "k2": 0.0},
        {"name": "barrel_weak", "k1": 0.1, "k2": 0.0},
        {"name": "barrel_medium", "k1": 0.2, "k2": 0.0},
        {"name": "barrel_strong", "k1": 0.3, "k2": 0.0},
        {"name": "pincushion_weak", "k1": -0.1, "k2": 0.0},
        {"name": "pincushion_medium", "k1": -0.2, "k2": 0.0},
        {"name": "complex_1", "k1": 0.1, "k2": -0.05},
        {"name": "complex_2", "k1": -0.1, "k2": 0.05},
    ]
    
    print("1. DISTORTION CORRECTION TESTS")
    print("-" * 35)
    
    for config in test_configs:
        print(f"Testing {config['name']} (k1={config['k1']}, k2={config['k2']})...")
        
        # Distortion coefficients: [k1, k2, p1, p2, k3]
        dist_coeffs = np.array([config['k1'], config['k2'], 0, 0, 0], dtype=np.float32)
        
        try:
            # Apply distortion correction
            undistorted = cv2.undistort(im, camera_matrix, dist_coeffs)
            
            cv2.imwrite(f'dewarp/simple_curve_{config["name"]}.png', undistorted)
            print(f"  ✓ Saved: simple_curve_{config['name']}.png")
            
        except Exception as e:
            print(f"  ✗ Failed: {e}")
    
    print(f"\n2. LOKALE WARP TEST")
    print("-" * 25)
    
    # Test lokale warp voor alleen bovenste deel (waar 'deuk' zit)
    crop_height = h // 3  # Bovenste derde
    top_crop = im[:crop_height, :]
    
    print(f"Testing lokale warp op bovenste {crop_height} pixels...")
    
    # Kleinere distortion voor lokaal effect
    local_configs = [
        {"name": "local_barrel", "k1": 0.05, "k2": 0.0},
        {"name": "local_pincushion", "k1": -0.05, "k2": 0.0},
    ]
    
    for config in local_configs:
        dist_coeffs = np.array([config['k1'], config['k2'], 0, 0, 0], dtype=np.float32)
        
        # Camera matrix voor crop
        crop_camera_matrix = np.array([
            [w/2, 0, w/2],
            [0, crop_height/2, crop_height/2], 
            [0, 0, 1]
        ], dtype=np.float32)
        
        try:
            undistorted_crop = cv2.undistort(top_crop, crop_camera_matrix, dist_coeffs)
            
            # Reconstructeer volledige image
            result = im.copy()
            result[:crop_height, :] = undistorted_crop
            
            cv2.imwrite(f'dewarp/simple_local_{config["name"]}.png', result)
            print(f"  ✓ Saved: simple_local_{config['name']}.png")
            
        except Exception as e:
            print(f"  ✗ Failed: {e}")
    
    print(f"\n3. EVALUATIE")
    print("-" * 15)
    print("🎯 Simple curve correction voordelen:")
    print("   • Geen extreme perspective/rotation")
    print("   • Alleen lokale distortion correctie")
    print("   • Snelle OpenCV implementatie")
    print("   • Makkelijk te controleren parameters")
    print()
    print("📊 Test resultaten voor beste 'deuk' correctie:")
    print("   • Barrel distortion (k1 > 0) = uitpuilen correctie")
    print("   • Pincushion distortion (k1 < 0) = inpuilen correctie")
    print("   • Lokale toepassing alleen op bovenste deel")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python simple_curve_correction.py <image_path>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    simple_curve_test(image_path)
