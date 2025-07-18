#!/usr/bin/env python3
"""
Simple landscape dewarp - gebruik spline correction in plaats van Kim2014.
"""

import cv2
import numpy as np

def simple_landscape_dewarp(image_path):
    """Simple dewarp die wel met landscape kan omgaan."""
    
    print("=== SIMPLE LANDSCAPE DEWARP ===")
    print("Aanpak: Gebruik onze spline correction i.p.v. Kim2014")
    print()
    
    im = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    h, w = im.shape[:2]
    
    print(f"Input: {w}x{h} pixels ({'landscape' if w > h else 'portrait'})")
    
    # Import our working spline functions
    from spline_based_dewarp import (
        get_AH_lines, identify_textblocks_smart, 
        create_splines_with_boundaries, apply_gentle_correction
    )
    
    # Text line detection (werkt op elke orientatie)
    from rebook import binarize, lib
    lib.debug = False  # Quiet mode
    
    bw = binarize.binarize(im, algorithm=lambda im: binarize.sauvola_noisy(im, k=0.1))
    
    import rebook.dewarp as dewarp_module
    dewarp_module.bw = bw
    
    AH, lines, all_lines, letters = get_AH_lines(bw)
    
    if len(lines) < 2:
        print("❌ Te weinig tekst lijnen gedetecteerd")
        return
    
    print(f"✓ Detected {len(lines)} text lines")
    
    # Sorteer en selecteer tekstblok voor "deuk"
    lines_sorted = sorted(lines, key=lambda l: l.base_points()[:, 1].mean())
    
    # Focus op bovenste paar lijnen (waar "deuk" meestal zit)
    top_line = lines_sorted[0]
    bottom_line = lines_sorted[min(2, len(lines_sorted)-1)]  # Max 3de lijn
    
    print(f"Selected correction region: line 1 to line {min(3, len(lines_sorted))}")
    
    # Create splines
    top_spline, bottom_spline = create_splines_with_boundaries(
        top_line, bottom_line, w, h
    )
    
    # Apply gentle correction (werkt op elke orientatie)
    strength = 1.0  # Moderate correction
    corrected = apply_gentle_correction(im, top_spline, bottom_spline, strength)
    
    # Save result
    cv2.imwrite('dewarp/simple_landscape_corrected.png', corrected)
    
    print("✓ Simple correction applied")
    print(f"✓ Result: simple_landscape_corrected.png")
    print(f"✓ Size preserved: {corrected.shape[1]}x{corrected.shape[0]}")
    
    # Also save spline visualization
    visualize_simple_splines(im, top_spline, bottom_spline, [top_line, bottom_line])

def visualize_simple_splines(image, top_spline, bottom_spline, selected_lines):
    """Simple spline visualization."""
    
    vis = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if len(image.shape) == 2 else image.copy()
    
    # Draw selected lines in blue
    for line in selected_lines:
        points = line.base_points().astype(int)
        for i in range(len(points) - 1):
            cv2.line(vis, tuple(points[i]), tuple(points[i + 1]), (255, 0, 0), 3)
    
    # Draw splines in green
    w = image.shape[1]
    for x in range(0, w-1, 5):  # Sample every 5 pixels
        try:
            cv2.line(vis, (x, int(top_spline[x])), (x+5, int(top_spline[x+5])), (0, 255, 0), 2)
            cv2.line(vis, (x, int(bottom_spline[x])), (x+5, int(bottom_spline[x+5])), (0, 255, 0), 2)
        except:
            continue
    
    cv2.imwrite('dewarp/simple_spline_visualization.png', vis)
    print("✓ Spline visualization: simple_spline_visualization.png")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python simple_landscape_dewarp.py <image_path>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    simple_landscape_dewarp(image_path)
