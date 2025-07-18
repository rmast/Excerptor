#!/usr/bin/env python3
"""
Test of Kim2014 problemen heeft met landscape vs portrait orientation.
"""

import cv2
import numpy as np
from rebook.dewarp import go_dewarp

def test_orientation_sensitivity(image_path, f_value=3500):
    """Test verschillende orientaties om Kim2014 gedrag te analyseren."""
    
    print("=== ORIENTATION SENSITIVITY TEST ===")
    print("Hypothese: Kim2014 raakt de weg kwijt bij landscape images")
    print()
    
    im = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    h, w = im.shape[:2]
    
    print(f"Original image: {w}x{h} pixels")
    print(f"Aspect ratio: {w/h:.2f} ({'landscape' if w > h else 'portrait'})")
    print()
    
    # Test verschillende orientaties
    test_cases = [
        {
            "name": "original",
            "image": im,
            "description": f"Origineel {w}x{h}"
        },
        {
            "name": "rotated_90",
            "image": cv2.rotate(im, cv2.ROTATE_90_CLOCKWISE),
            "description": f"90° gedraaid {h}x{w}"
        },
        {
            "name": "cropped_square", 
            "image": im[:min(h,w), :min(h,w)],
            "description": f"Vierkant crop {min(h,w)}x{min(h,w)}"
        }
    ]
    
    if w > h:
        # Als landscape, maak ook portrait versie
        new_h = int(w * 1.2)  # Maak hoger dan breed
        portrait_im = cv2.resize(im, (w, new_h))
        test_cases.append({
            "name": "forced_portrait",
            "image": portrait_im,
            "description": f"Forced portrait {w}x{new_h}"
        })
    
    # Test elke orientatie
    for case in test_cases:
        print(f"\n→ Testing {case['name']}: {case['description']}")
        test_im = case['image']
        test_h, test_w = test_im.shape[:2]
        test_ctr = np.array([test_w / 2, test_h / 2])
        
        print(f"  Aspect ratio: {test_w/test_h:.2f}")
        
        try:
            # Test met kleine debug output
            import rebook.lib as lib
            original_debug = lib.debug
            lib.debug = False  # Reduce noise
            
            surface_tuning = {'y_offset': 0.0, 'curvature_adjust': 1.0, 'threshold_mult': 1.0}
            result = go_dewarp(test_im, test_ctr, debug=False, 
                             focal_length=f_value, surface_tuning=surface_tuning)
            
            lib.debug = original_debug
            
            if result and len(result) > 0:
                output = result[0][0]
                out_h, out_w = output.shape[:2]
                
                # Check voor extreme transformaties
                size_change = (out_w * out_h) / (test_w * test_h)
                aspect_change = (out_w/out_h) / (test_w/test_h)
                
                print(f"  ✓ Success: output {out_w}x{out_h}")
                print(f"    Size change: {size_change:.2f}x")
                print(f"    Aspect change: {aspect_change:.2f}x")
                
                # Flag suspicious results
                if size_change > 2.0 or size_change < 0.5:
                    print(f"    ⚠️  SUSPICIOUS: Extreme size change!")
                if aspect_change > 2.0 or aspect_change < 0.5:
                    print(f"    ⚠️  SUSPICIOUS: Extreme aspect change!")
                
                cv2.imwrite(f'dewarp/orientation_test_{case["name"]}.png', output)
                print(f"    📊 Saved: orientation_test_{case['name']}.png")
            else:
                print(f"  ✗ Failed: No result returned")
                
        except Exception as e:
            print(f"  ✗ Failed: {e}")
    
    print(f"\n=== ANALYSIS ===")
    print("🔍 Compare the results:")
    print("   • Original vs rotated_90: Zijn resultaten vergelijkbaar?")
    print("   • Landscape vs portrait: Welke geeft betere resultaten?") 
    print("   • Extreme transformaties: Welke cases hebben rare output?")
    print()
    print("💡 Als landscape problematisch is:")
    print("   → Roteer image naar portrait voor dewarp")
    print("   → Roteer result terug naar landscape")
    print("   → Of: modificeer Kim2014 voor landscape support")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python orientation_test.py <image_path> [f_value]")
        sys.exit(1)
        
    image_path = sys.argv[1]
    f_value = int(sys.argv[2]) if len(sys.argv) > 2 else 3500
    
    test_orientation_sensitivity(image_path, f_value)
