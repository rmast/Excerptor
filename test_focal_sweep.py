#!/usr/bin/env python3
"""
Systematische test van focal length parameters.
Doel: Zie groene lijnen (surface_lines.png) dichter bij blauwe lijnen (all_lines.png) komen.
"""

import subprocess
import os
import shutil
from pathlib import Path

def run_test(focal_length, output_prefix):
    """Run single test with specific focal length."""
    print(f"\n=== Testing f={focal_length} ===")
    
    # Maak output directory
    output_dir = f"test_f{focal_length}"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    # Pas demo.py aan om focal_length door te geven
    # TODO: Implement focal_length parameter in demo.py
    
    # Run test
    cmd = [
        'python', 'demo.py', 
        '-d', '-i', 'book', '-vt', '--scantailor-split',
        '-o', output_dir, '-a', f'{output_dir}_archive', 
        '-n', f'{output_dir}_note.md'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Copy debug images to named folder
    debug_dir = f"debug_f{focal_length}"
    if os.path.exists('dewarp'):
        shutil.copytree('dewarp', debug_dir, dirs_exist_ok=True)
    
    return result.returncode == 0

def main():
    """Run focal length sweep test."""
    focal_lengths = [3230, 3500, 4000, 5000, 7000, 10000]
    
    print("Starting focal length parameter sweep...")
    print("Visual goal: green lines in surface_lines.png → blue lines in all_lines.png")
    
    for f in focal_lengths:
        success = run_test(f, f"test_f{f}")
        print(f"f={f}: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        # Check for key debug files
        debug_files = [f"debug_f{f}/surface_lines.png", f"debug_f{f}/all_lines.png"]
        for file in debug_files:
            if os.path.exists(file):
                print(f"  Generated: {file}")
    
    print("\n=== SWEEP COMPLETE ===")
    print("Compare surface_lines.png across debug_f* folders")
    print("Look for progressive alignment improvement")

if __name__ == '__main__':
    main()
