#!/usr/bin/env python3
"""
Landscape-aware dewarp - automatisch roteren voor Kim2014 compatibility.
"""

import cv2
import numpy as np
from rebook.dewarp import go_dewarp

def landscape_aware_dewarp(image_path, f_value=3500):
    """Dewarp met automatische landscape/portrait handling."""
    
    print("=== LANDSCAPE-AWARE DEWARP ===")
    print("Automatische orientatie correctie voor Kim2014")
    print()
    
    im = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    h, w = im.shape[:2]
    
    print(f"Input image: {w}x{h} pixels")
    print(f"Aspect ratio: {w/h:.2f}")
    
    # Bepaal of we moeten roteren
    is_landscape = w > h
    needs_rotation = is_landscape and (w/h > 1.2)  # Duidelijk landscape
    
    if needs_rotation:
        print("🔄 Landscape detected - rotating to portrait for dewarp...")
        
        # Roteer naar portrait
        rotated_im = cv2.rotate(im, cv2.ROTATE_90_CLOCKWISE)
        rot_h, rot_w = rotated_im.shape[:2]
        rot_ctr = np.array([rot_w / 2, rot_h / 2])
        
        print(f"Rotated to: {rot_w}x{rot_h} pixels")
        
        # FORCE FULL PAGE PRESERVATION
        surface_tuning = {
            'y_offset': 0.0, 
            'curvature_adjust': 1.0, 
            'threshold_mult': 1.0,
            'preserve_full_page': True  # Custom flag
        }
        
        try:
            # Monkey patch om full page te behouden
            result = full_page_dewarp(rotated_im, rot_ctr, f_value, surface_tuning)
            
            if result and len(result) > 0:
                dewarped_portrait = result[0][0]
                
                # Check of result preserves original size
                dp_h, dp_w = dewarped_portrait.shape[:2]
                print(f"Dewarped size: {dp_w}x{dp_h} (expected: {rot_w}x{rot_h})")
                
                if dp_w < rot_w * 0.8 or dp_h < rot_h * 0.8:
                    print("⚠️  WARNING: Significant cropping detected!")
                    print("    Attempting size restoration...")
                    
                    # Pad back to original size
                    dewarped_portrait = restore_original_size(dewarped_portrait, rotated_im)
                
                # Roteer result terug naar landscape
                print("🔄 Rotating result back to landscape...")
                final_result = cv2.rotate(dewarped_portrait, cv2.ROTATE_90_COUNTERCLOCKWISE)
                
                cv2.imwrite('dewarp/landscape_fixed_full_page.png', final_result)
                print("✓ Full page result: landscape_fixed_full_page.png")
                
                # Debug comparison
                print(f"Final size: {final_result.shape[1]}x{final_result.shape[0]}")
                print(f"Original size: {w}x{h}")
                
            else:
                print("✗ Dewarp failed even na rotatie")
                
        except Exception as e:
            print(f"✗ Dewarp failed: {e}")
    
    else:
        print("📏 Portrait/square detected - standard dewarp...")
        ctr = np.array([w / 2, h / 2])
        
        surface_tuning = {'y_offset': 0.0, 'curvature_adjust': 1.0, 'threshold_mult': 1.0}
        
        try:
            result = go_dewarp(im, ctr, debug=True, 
                             focal_length=f_value, surface_tuning=surface_tuning)
            
            if result and len(result) > 0:
                output = result[0][0]
                cv2.imwrite('dewarp/standard_dewarp_result.png', output)
                print("✓ Standard result: standard_dewarp_result.png")
            else:
                print("✗ Standard dewarp failed")
                
        except Exception as e:
            print(f"✗ Standard dewarp failed: {e}")

def full_page_dewarp(image, center, f_value, surface_tuning):
    """Dewarp with full page preservation."""
    
    print("    🔧 Applying full page preservation...")
    
    # Store original dimensions
    orig_h, orig_w = image.shape[:2]
    
    # Monkey patch Kim2014 om cropping te voorkomen
    from rebook.dewarp import Kim2014
    original_get_crop = Kim2014.get_crop
    
    def preserve_full_page_crop(self):
        """Force full page crop instead of text-only crop."""
        h, w = self.image.shape[:2]
        # Return full image bounds instead of detected text bounds
        return (0, 0, w, h)
    
    # Apply monkey patch
    Kim2014.get_crop = preserve_full_page_crop
    
    try:
        # Call normal dewarp with modified behavior
        result = go_dewarp(image, center, debug=False, 
                         focal_length=f_value, surface_tuning=surface_tuning)
        
        return result
        
    finally:
        # Restore original behavior
        Kim2014.get_crop = original_get_crop

def restore_original_size(cropped_result, original_image):
    """Restore cropped result to original image size."""
    
    orig_h, orig_w = original_image.shape[:2]
    crop_h, crop_w = cropped_result.shape[:2]
    
    print(f"    Restoring size: {crop_w}x{crop_h} → {orig_w}x{orig_h}")
    
    # Calculate padding needed
    pad_top = (orig_h - crop_h) // 2
    pad_bottom = orig_h - crop_h - pad_top
    pad_left = (orig_w - crop_w) // 2
    pad_right = orig_w - crop_w - pad_left
    
    # Create padded result
    if len(cropped_result.shape) == 2:
        # Grayscale
        restored = np.pad(cropped_result, 
                         ((pad_top, pad_bottom), (pad_left, pad_right)),
                         mode='constant', constant_values=255)  # White padding
    else:
        # Color
        restored = np.pad(cropped_result,
                         ((pad_top, pad_bottom), (pad_left, pad_right), (0, 0)),
                         mode='constant', constant_values=255)
    
    return restored

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python landscape_fixed_dewarp.py <image_path> [f_value]")
        sys.exit(1)
        
    image_path = sys.argv[1]
    f_value = int(sys.argv[2]) if len(sys.argv) > 2 else 3500
    
    landscape_aware_dewarp(image_path, f_value)
