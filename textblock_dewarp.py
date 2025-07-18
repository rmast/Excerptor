#!/usr/bin/env python3
"""
Tekstblok-gebaseerde dewarping - los lokale deformaties op zonder globale verstoring.
"""

import cv2
import numpy as np
from rebook.dewarp import go_dewarp, Kim2014
from rebook import binarize, lib
from rebook.geometry import Crop

def analyze_textblock_approach(image_path, f_value=3500):
    """Analyseer tekstblok-gebaseerde dewarping mogelijkheden."""
    
    print("=== TEKSTBLOK-GEBASEERDE DEWARPING ===")
    print("Probleem: Globale polynomial kan lokale deformaties niet oplossen")
    print("Oplossing: Per tekstblok aparte surface fitting")
    print()
    
    im = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    ctr = np.array([im.shape[1] / 2, im.shape[0] / 2])
    
    # Stap 1: Identificeer tekstblokken
    print("1. TEKSTBLOK IDENTIFICATIE")
    print("-" * 30)
    
    # Voer eerste pass dewarp uit om tekstregels te krijgen
    lib.debug = True
    lib.debug_prefix = ['textblock']
    
    # Monkey patch om tekstregels te onderscheppen
    detected_lines = []
    
    def capture_lines(self, R, g, align, l_m):
        nonlocal detected_lines
        detected_lines = self.lines.copy()
        print(f"📋 Gedetecteerde lijnen: {len(detected_lines)}")
        
        # Analyseer tekstblok verdeling
        y_positions = []
        for line in detected_lines:
            base_points = line.base_points()
            y_positions.append(base_points[:, 1].mean())
        
        y_positions = np.array(y_positions)
        print(f"   Y-bereik: {y_positions.min():.0f} - {y_positions.max():.0f}")
        
        # Detecteer gaps tussen tekstblokken (>2x normale regelafstand)
        y_sorted = np.sort(y_positions)
        gaps = np.diff(y_sorted)
        normal_gap = np.median(gaps)
        large_gaps = gaps > 2 * normal_gap
        
        if np.any(large_gaps):
            gap_positions = y_sorted[:-1][large_gaps]
            print(f"   Tekstblok scheiding op Y: {gap_positions}")
            
            # Verdeel lijnen in blokken
            blocks = []
            current_block = []
            
            for line, y_pos in zip(detected_lines, y_positions):
                # Check of deze lijn na een grote gap komt
                if current_block and np.any(gap_positions < y_pos) and np.any(gap_positions > current_block[-1][1]):
                    blocks.append(current_block)
                    current_block = []
                current_block.append((line, y_pos))
            
            if current_block:
                blocks.append(current_block)
            
            print(f"   Gedetecteerde tekstblokken: {len(blocks)}")
            for i, block in enumerate(blocks):
                y_min = min(line_y for _, line_y in block)
                y_max = max(line_y for _, line_y in block)
                print(f"     Blok {i+1}: {len(block)} lijnen, Y {y_min:.0f}-{y_max:.0f}")
        else:
            print("   Geen duidelijke tekstblok scheiding gevonden")
    
    # Apply monkey patch
    original_debug_images = Kim2014.debug_images
    Kim2014.debug_images = capture_lines
    
    try:
        # Voer dewarp uit om lijnen te detecteren
        surface_tuning = {'y_offset': 0.0, 'curvature_adjust': 1.0, 'threshold_mult': 1.0}
        result = go_dewarp(im, ctr, debug=True, focal_length=f_value, surface_tuning=surface_tuning)
        
    finally:
        Kim2014.debug_images = original_debug_images
    
    print(f"\n2. LOKALE DEFORMATIE ANALYSE")
    print("-" * 35)
    
    if detected_lines:
        # Analyseer lokale deformaties per tekstgebied
        print("🔍 Analyseer deformatie patronen...")
        
        # Focus op bovenste gebied waar "deuk" zit
        top_lines = [line for line in detected_lines[:8]]  # Eerste 8 lijnen
        
        if top_lines:
            print(f"   Bovenste tekstgebied: {len(top_lines)} lijnen")
            
            # Bereken lokale curvature per lijn
            for i, line in enumerate(top_lines[:3]):
                base_points = line.base_points()
                if len(base_points) > 5:
                    # Fit polynomial door lijn punten
                    x_coords = base_points[:, 0]
                    y_coords = base_points[:, 1]
                    
                    # 2nd degree polynomial fit
                    poly_coeffs = np.polyfit(x_coords, y_coords, 2)
                    curvature = abs(poly_coeffs[0])  # 2nd order coefficient
                    
                    print(f"     Lijn {i+1}: curvature = {curvature:.6f}")
    
    print(f"\n3. AANBEVELINGEN")
    print("-" * 20)
    print("🎯 Gebaseerd op analyse:")
    print("   1. Implementeer piecewise surface modeling")
    print("   2. Gebruik tekstblok boundaries voor segmentatie") 
    print("   3. Aparte polynomial per tekstblok")
    print("   4. Smooth transitions tussen blokken")
    print()
    print("📐 Implementatie opties:")
    print("   A. Modify Kim2014 voor multi-segment surfaces")
    print("   B. Pre-process: crop → dewarp → stitch")
    print("   C. Post-process: blend multiple dewarp results")
    
    print(f"\n4. PROOF OF CONCEPT - CROP & DEWARP")
    print("-" * 40)
    
    if detected_lines and len(detected_lines) >= 8:
        print("🚀 Testing optie B: crop → dewarp → stitch")
        
        # Focus op bovenste tekstblok (waar deuk zit)
        top_8_lines = detected_lines[:8]
        
        # Bereken crop gebied voor bovenste blok
        y_positions = []
        x_positions = []
        for line in top_8_lines:
            base_points = line.base_points()
            y_positions.extend(base_points[:, 1])
            x_positions.extend(base_points[:, 0])
        
        # Add margin
        margin = 100
        crop_x0 = max(0, int(min(x_positions)) - margin)
        crop_y0 = max(0, int(min(y_positions)) - margin)
        crop_x1 = min(im.shape[1], int(max(x_positions)) + margin)
        crop_y1 = min(im.shape[0], int(max(y_positions)) + margin)
        
        print(f"   Top blok crop: ({crop_x0}, {crop_y0}) → ({crop_x1}, {crop_y1})")
        print(f"   Crop grootte: {crop_x1-crop_x0} x {crop_y1-crop_y0}")
        
        # Crop de image
        cropped_im = im[crop_y0:crop_y1, crop_x0:crop_x1]
        cropped_ctr = np.array([(crop_x1-crop_x0)/2, (crop_y1-crop_y0)/2])
        
        print(f"   Gecropte center: {cropped_ctr}")
        
        # Test met verschillende constraints voor meer stabiele dewarp
        print("   Voer dewarp uit met stabiliteitsfocus...")
        
        try:
            # Test met meer conservatieve settings
            original_debug = lib.debug
            lib.debug = False
            
            # Probeer verschillende configuraties
            test_configs = [
                {"name": "conservative", "y_offset": 0.0, "curvature_adjust": 0.8, "threshold_mult": 1.5},
                {"name": "minimal", "y_offset": 0.0, "curvature_adjust": 0.9, "threshold_mult": 1.2},
                {"name": "baseline", "y_offset": 0.0, "curvature_adjust": 1.0, "threshold_mult": 1.0},
            ]
            
            for config in test_configs:
                print(f"      Testing {config['name']} config...")
                surface_tuning = {
                    'y_offset': config['y_offset'],
                    'curvature_adjust': config['curvature_adjust'], 
                    'threshold_mult': config['threshold_mult']
                }
                
                try:
                    crop_result = go_dewarp(cropped_im, cropped_ctr, debug=False, 
                                          focal_length=f_value, surface_tuning=surface_tuning)
                    
                    if crop_result and len(crop_result) > 0:
                        crop_output = crop_result[0][0]
                        
                        # Save with config name
                        cv2.imwrite(f'dewarp/textblock_crop_{config["name"]}.png', crop_output)
                        print(f"      ✓ Saved: textblock_crop_{config['name']}.png")
                        
                except Exception as e:
                    print(f"      ✗ {config['name']} failed: {e}")
            
            lib.debug = original_debug
            
            # Save original crop for reference
            cv2.imwrite('dewarp/textblock_original_crop.png', cropped_im)
            
            print(f"\n   🔍 ANALYSE VAN EXTREME TRANSFORMATIE:")
            print(f"      • Spiegeling + rotatie suggereert surface misinterpretatie")  
            print(f"      • Mogelijk: algoritme denkt dat crop 'ondersteboven' is")
            print(f"      • Of: lokale curvature wordt verkeerd geëxtrapoleerd")
            print(f"      • Test verschillende configs om stabiliteit te vinden")
            
        except Exception as e:
            print(f"   ✗ Alle crop dewarps failed: {e}")
            lib.debug = original_debug
    
    print(f"\n5. DIAGNOSE: WAAROM EXTREME TRANSFORMATIE?")
    print("-" * 50)
    print("🔬 Mogelijke oorzaken spiegeling/rotatie:")
    print("   1. Algoritme interpreteert lokale 'deuk' als volledige page flip")
    print("   2. Te weinig tekstlijnen voor stabiele surface fitting")
    print("   3. Vanishing point berekening fout bij kleine crop")  
    print("   4. Surface polynomial krijgt verkeerde initiële parameters")
    print()
    print("🛠️  VERBETERINGEN:")
    print("   • Grotere crop met meer context")
    print("   • Geforceerde surface constraints")
    print("   • Pre-rotation correctie") 
    print("   • Hybride aanpak: globale orientation + lokale curvature")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python textblock_dewarp.py <image_path> [f_value]")
        sys.exit(1)
        
    image_path = sys.argv[1]
    f_value = int(sys.argv[2]) if len(sys.argv) > 2 else 3500
    
    analyze_textblock_approach(image_path, f_value)
