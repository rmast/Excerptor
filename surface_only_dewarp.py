#!/usr/bin/env python3
"""
Surface-only dewarp - pas alleen de surface polynomial aan, skip alle transformaties.
"""

import cv2
import numpy as np
from rebook.dewarp import go_dewarp, Kim2014

def surface_only_test(image_path, f_value=3500):
    """Test alleen surface polynomial aanpassing zonder mesh/perspective."""
    
    print("=== SURFACE-ONLY DEWARP TEST ===")
    print("Aanpak: Skip alle mesh transformaties, toon alleen polynomial effect")
    print()
    
    im = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    ctr = np.array([im.shape[1] / 2, im.shape[0] / 2])
    
    # Monkey patch correct_geometry om transformatie te skippen
    from rebook.dewarp import correct_geometry
    original_correct_geometry = correct_geometry
    
    def bypass_correct_geometry(orig, mesh, **kwargs):
        """Bypass alle mesh transformaties - return origineel."""
        print("   🔥 BYPASSING all mesh transformations")
        # Return original image without any transformation
        return (orig, None)
    
    # Monkey patch de hele mesh/remap pipeline
    import rebook.dewarp as dewarp_module
    dewarp_module.correct_geometry = bypass_correct_geometry
    
    try:
        print("1. SURFACE POLYNOMIAL EXPLORATION")
        print("-" * 40)
        print("   (Alle mesh transformaties uitgeschakeld)")
        
        # Test verschillende surface parameters
        test_configs = [
            {"name": "baseline", "curvature_adjust": 1.0},
            {"name": "reduce_curve", "curvature_adjust": 0.5},
            {"name": "zero_curve", "curvature_adjust": 0.0},
            {"name": "negative_curve", "curvature_adjust": -0.5},
            {"name": "enhance_curve", "curvature_adjust": 2.0},
        ]
        
        for config in test_configs:
            print(f"Testing {config['name']} (curve={config['curvature_adjust']})...")
            
            surface_tuning = {
                'y_offset': 0.0,
                'curvature_adjust': config['curvature_adjust'],
                'threshold_mult': 1.0
            }
            
            try:
                # Dit zou nu alleen de surface polynomial testen zonder transformatie
                result = go_dewarp(im, ctr, debug=False, 
                                 focal_length=f_value, surface_tuning=surface_tuning)
                
                if result and len(result) > 0:
                    output = result[0][0]  # Should be original image
                    cv2.imwrite(f'dewarp/surface_only_{config["name"]}.png', output)
                    print(f"  ✓ Saved: surface_only_{config['name']}.png (should be original)")
                
            except Exception as e:
                print(f"  ✗ Failed: {e}")
        
        print(f"\n2. ALTERNATIVE: DIRECT SURFACE VISUALIZATION")
        print("-" * 50)
        
        # Test door direct de surface polynomial te evalueren en visualiseren
        print("   Testing surface polynomial evaluation...")
        
        # Monkey patch om polynomial info te onderscheppen
        captured_polynomials = []
        
        def capture_polynomial_info(self, R, g, align, l_m):
            nonlocal captured_polynomials
            print(f"   📊 Captured polynomial: {type(g)}")
            if hasattr(g, 'coef'):
                print(f"      Coefficients: {g.coef[:5]}...")
            captured_polynomials.append(g)
        
        original_debug_images = Kim2014.debug_images
        Kim2014.debug_images = capture_polynomial_info
        
        try:
            # Run dewarp om polynomial te vangen
            surface_tuning = {'y_offset': 0.0, 'curvature_adjust': 1.0, 'threshold_mult': 1.0}
            result = go_dewarp(im, ctr, debug=True, focal_length=f_value, surface_tuning=surface_tuning)
            
            if captured_polynomials:
                g = captured_polynomials[0]
                print(f"   🔍 Analyzing captured polynomial...")
                
                # Visualiseer polynomial over image breedte
                im_width = im.shape[1]
                x_range = np.linspace(-im_width/2, im_width/2, 100)
                
                try:
                    z_values = g(x_range)
                    print(f"      X-range: {x_range.min():.1f} to {x_range.max():.1f}")
                    print(f"      Z-range: {z_values.min():.1f} to {z_values.max():.1f}")
                    print(f"      Z-variation: {z_values.max() - z_values.min():.1f}")
                    
                    # Save polynomial plot data
                    polynomial_data = np.column_stack([x_range, z_values])
                    np.savetxt('dewarp/surface_polynomial_data.txt', polynomial_data, 
                              header='X_coord Z_value', fmt='%.3f')
                    print(f"   📊 Polynomial data saved: surface_polynomial_data.txt")
                    
                except Exception as e:
                    print(f"      ✗ Polynomial evaluation failed: {e}")
            
        finally:
            Kim2014.debug_images = original_debug_images
    
    finally:
        # Restore original
        dewarp_module.correct_geometry = original_correct_geometry
    
    print(f"\n3. CONCLUSIE")
    print("-" * 15)
    print("🎯 Als alle surface_only_*.png identiek zijn aan origineel:")
    print("   → Surface polynomial heeft geen effect zonder mesh transformatie")
    print("   → Probleem zit in mesh generation/remap pipeline")
    print()
    print("📈 Polynomial data analyse:")
    print("   → Check surface_polynomial_data.txt voor Z-variatie")
    print("   → Grote Z-variatie = sterke surface curvature")
    print("   → Kleine Z-variatie = minimale surface effect")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python surface_only_dewarp.py <image_path> [f_value]")
        sys.exit(1)
        
    image_path = sys.argv[1]
    f_value = int(sys.argv[2]) if len(sys.argv) > 2 else 3500
    
    surface_only_test(image_path, f_value)
