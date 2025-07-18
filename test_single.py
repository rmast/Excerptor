#!/usr/bin/env python3
import cv2
import numpy as np
from rebook.dewarp import go_dewarp

# Test single configuration with full error info
print("Loading image...")
im = cv2.imread('book/Scan_20250618 (8)_1L.tif', cv2.IMREAD_UNCHANGED)
if im is None:
    print("ERROR: Cannot load image")
    exit(1)
    
print(f"Image shape: {im.shape}")
print(f"Image dtype: {im.dtype}")
print(f"Image channels: {'Grayscale' if len(im.shape) == 2 else im.shape[2]}")

ctr = np.array([im.shape[1] / 2, im.shape[0] / 2])

surface_tuning = {'y_offset': 0.0, 'curvature_adjust': 1.0}

print("Starting dewarp...")
try:
    result = go_dewarp(im, ctr, debug=True, focal_length=3500, surface_tuning=surface_tuning)
    print("SUCCESS! Check dewarp/surface_lines.png for results")
    print(f"Result type: {type(result)}")
    if hasattr(result, '__len__'):
        print(f"Result length: {len(result)}")
        if len(result) > 0 and hasattr(result[0], '__len__'):
            print(f"First result length: {len(result[0])}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
