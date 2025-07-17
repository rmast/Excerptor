#!/usr/bin/env python3
"""
Vergelijk surface tuning resultaten visueel.
"""

import cv2
import numpy as np
import os
import glob

def compare_surface_results():
    """Vergelijk alle surface_lines_*.png files."""
    
    # Find all surface lines images
    pattern = 'dewarp/surface_lines_*.png'
    files = sorted(glob.glob(pattern))
    
    if not files:
        print("Geen surface_lines_*.png files gevonden in dewarp/")
        return
    
    print(f"Gevonden {len(files)} resultaat files:")
    for f in files:
        print(f"  - {f}")
    
    # Load and display info about each
    for filepath in files:
        config_name = os.path.basename(filepath).replace('surface_lines_', '').replace('.png', '')
        
        img = cv2.imread(filepath)
        if img is not None:
            h, w = img.shape[:2]
            print(f"\n{config_name:15s}: {w}x{h} pixels")
            
            # Count green pixels (groene lijnen) vs blue pixels (blauwe lijnen)
            # Green lines: [0, 255, 0] in BGR
            # Blue lines: [255, 0, 0] in BGR
            
            green_mask = np.all(img == [0, 255, 0], axis=2)
            blue_mask = np.all(img == [255, 0, 0], axis=2)
            
            green_pixels = np.sum(green_mask)
            blue_pixels = np.sum(blue_mask)
            
            print(f"                Green pixels: {green_pixels:6d}")
            print(f"                Blue pixels:  {blue_pixels:6d}")
            
            # Simple alignment metric: how close are green and blue lines?
            # This is a rough approximation
            if green_pixels > 0 and blue_pixels > 0:
                ratio = green_pixels / blue_pixels
                print(f"                Green/Blue ratio: {ratio:.3f}")
        else:
            print(f"{config_name:15s}: Kan niet laden")

    print(f"\n🎯 Bekijk de files visueel in dewarp/ om te zien welke configuratie")
    print(f"   de groene lijnen het best op de blauwe lijnen laat aansluiten!")

if __name__ == '__main__':
    compare_surface_results()
