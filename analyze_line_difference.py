#!/usr/bin/env python3
"""
Diepgaande analyse van het verschil tussen groene en blauwe lijnen.
Doel: Begrijpen waarom surface tuning zo weinig effect heeft.
"""

import cv2
import numpy as np
from rebook.dewarp import go_dewarp, kim2014, get_AH_lines
from rebook import binarize, lib
from rebook.lib import RED, GREEN, BLUE, draw_line, draw_circle

def analyze_line_generation(image_path, f_value=3500):
    """Analyseer stap-voor-stap hoe beide lijn-types worden gegenereerd."""
    
    print("=== DIEPGAANDE LIJN ANALYSE ===")
    
    # Load image
    im = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    ctr = np.array([im.shape[1] / 2, im.shape[0] / 2])
    
    # Direct dewarp uitvoeren voor volledige analyse
    print("\n1. VOLLEDIGE DEWARP ANALYSE")
    print("-" * 50)
    
    # Voer dewarp uit en onderschep debug info
    surface_tuning = {'y_offset': 0.0, 'curvature_adjust': 1.0, 'threshold_mult': 1.0}
    
    # Monkey patch debug_images voor extra info
    def enhanced_debug_images(self, R, g, align, l_m):
        print(f"\n=== TEXT DETECTION RESULTATEN ===")
        print(f"Letters gedetecteerd: {len(self.all_letters)}")
        print(f"Gefilterde lijnen (blauw): {len(self.lines)}")
        print(f"AH (Average Height): {self.AH}")
        
        # Analyseer lijn eigenschappen
        for i, line in enumerate(self.lines[:5]):  # Eerste 5 lijnen
            base_points = line.base_points()
            print(f"  Lijn {i}: {len(line)} letters, y-range: {base_points[:, 1].min():.1f}-{base_points[:, 1].max():.1f}")
        
        print(f"\n=== SURFACE PROJECTION RESULTATEN ===")
        print(f"Surface parameters - l_m: {len(l_m)} values")
        print(f"l_m waarden: {l_m[:5]}...")  # Eerste 5 waarden
        
        print(f"g(x) polynomial coëfficiënten: {g.coef[:5]}...")  # Eerste 5
        
        # Analyseer surface projectie
        from rebook.dewarp import E_str_project
        ts_surface = E_str_project(R, g, self.base_points, 0)
        
        print(f"Surface projecties: {len(ts_surface)}")
        for i, (ts, (Xs, Ys, Zs)) in enumerate(ts_surface[:5]):
            print(f"  Surface {i}: X-range: {Xs.min():.1f}-{Xs.max():.1f}, Y-mean: {Ys.mean():.1f}")
        
        # Extra analyse: vergelijk Y-posities
        print("\n3. Y-POSITIE VERGELIJKING")
        print("-" * 30)
        
        # Blauwe lijn Y-posities
        blue_y_positions = []
        for line in self.lines:
            base_points = line.base_points()
            blue_y_positions.append(base_points[:, 1].mean())
        
        # Groene lijn Y-posities (van l_m + surface projection)
        green_y_positions = []
        for Y, (_, (_, Ys, _)) in zip(l_m, ts_surface):
            # De groene lijn Y-positie komt van Y (l_m parameter) plus surface offset
            surface_y_offset = getattr(self, 'surface_y_offset', 0.0)
            green_y_positions.append(Y + surface_y_offset)
        
        print(f"Blauwe Y-posities (eerste 5): {blue_y_positions[:5]}")
        print(f"Groene Y-posities (eerste 5): {green_y_positions[:5]}")
        
        # Bereken verschillen
        min_len = min(len(blue_y_positions), len(green_y_positions))
        y_differences = [abs(b - g) for b, g in zip(blue_y_positions[:min_len], green_y_positions[:min_len])]
        print(f"Y-verschil gemiddeld: {np.mean(y_differences):.1f} pixels")
        print(f"Y-verschil spreiding: {np.std(y_differences):.1f} pixels")
    
    # Monkey patch temporeel
    from rebook.dewarp import Kim2014
    original_debug_images = Kim2014.debug_images
    Kim2014.debug_images = enhanced_debug_images
    
    try:
        result = go_dewarp(im, ctr, debug=True, focal_length=f_value, surface_tuning=surface_tuning)
        print("\n✓ Analyse compleet")
    finally:
        # Restore original
        Kim2014.debug_images = original_debug_images
    
    print("\n4. CONCLUSIES EN AANBEVELINGEN")
    print("-" * 40)
    print("Bekijk de output hierboven voor:")
    print("- Verschillen in Y-posities tussen blauw/groen")
    print("- Surface parameter waarden (l_m)")
    print("- Polynomial coëfficiënten (g)")
    print("- Letter detectie statistieken")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python analyze_line_difference.py <image_path> [f_value]")
        sys.exit(1)
        
    image_path = sys.argv[1]
    f_value = int(sys.argv[2]) if len(sys.argv) > 2 else 3500
    
    analyze_line_generation(image_path, f_value)
