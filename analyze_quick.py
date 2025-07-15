#!/usr/bin/env python3
"""
Quick experiment result analyzer
"""

import os
import cv2
import numpy as np
from datetime import datetime

def analyze_experiment_results():
    print("🔬 EXPERIMENT RESULTATEN ANALYSE")
    print("=" * 50)
    
    # 1. Bestandsgroottes vergelijken
    print("1. BESTANDSGROOTTES:")
    try:
        std_size = os.path.getsize("test_std/Scan_20250618 (8)_1L_L_dewarped.tif")
        exp_size = os.path.getsize("test_exp/Scan_20250618 (8)_1L_L_dewarped.tif")
        print(f"   STD: {std_size:,} bytes ({std_size/1024/1024:.1f} MB)")
        print(f"   EXP: {exp_size:,} bytes ({exp_size/1024/1024:.1f} MB)")
        print(f"   Verschil: {abs(std_size - exp_size):,} bytes")
    except FileNotFoundError as e:
        print(f"   Fout: {e}")
    
    print()
    
    # 2. Debug image timestamps
    print("2. DEBUG AFBEELDING TIMESTAMPS:")
    debug_files = ["all_lines.png", "surface_lines.png"]
    for file in debug_files:
        path = f"dewarp/{file}"
        if os.path.exists(path):
            mtime = os.path.getmtime(path)
            dt = datetime.fromtimestamp(mtime)
            print(f"   {file}: {dt.strftime('%H:%M:%S')}")
    
    print()
    
    # 3. Afbeelding dimensies vergelijken
    print("3. AFBEELDING EIGENSCHAPPEN:")
    try:
        std_img = cv2.imread("test_std/Scan_20250618 (8)_1L_L_dewarped.tif", cv2.IMREAD_UNCHANGED)
        exp_img = cv2.imread("test_exp/Scan_20250618 (8)_1L_L_dewarped.tif", cv2.IMREAD_UNCHANGED)
        
        if std_img is not None and exp_img is not None:
            print(f"   STD dimensies: {std_img.shape}")
            print(f"   EXP dimensies: {exp_img.shape}")
            print(f"   STD dtype: {std_img.dtype}")
            print(f"   EXP dtype: {exp_img.dtype}")
            
            # Bereken gemiddelde helderheid (als proxy voor kwaliteit)
            if len(std_img.shape) == 3:
                std_bright = np.mean(cv2.cvtColor(std_img, cv2.COLOR_BGR2GRAY))
                exp_bright = np.mean(cv2.cvtColor(exp_img, cv2.COLOR_BGR2GRAY))
            else:
                std_bright = np.mean(std_img)
                exp_bright = np.mean(exp_img)
            
            print(f"   STD gemiddelde helderheid: {std_bright:.1f}")
            print(f"   EXP gemiddelde helderheid: {exp_bright:.1f}")
        else:
            print("   Fout: Kon afbeeldingen niet laden")
    except Exception as e:
        print(f"   Fout bij afbeelding analyse: {e}")
    
    print()
    
    # 4. Terminal output analyseren
    print("4. KWALITEITSSCORES UIT TERMINAL:")
    print("   STD: [niet getoond in output]")
    print("   EXP: 0.000 (zeer slecht!)")
    print("   -> Dit wijst op een probleem met de experimentele filters")
    
    print()
    
    # 5. Conclusies
    print("5. VOORLOPIGE CONCLUSIES:")
    print("   ⚠️  EXP score van 0.000 is verdacht")
    print("   📊 Debug afbeeldingen zijn van STD run (13:39)")
    print("   📁 Beide bestanden hebben vergelijkbare grootte")
    print("   🔍 We hebben nu STD vs EXP resultaten om te vergelijken")
    
    print("\n6. VOLGENDE STAPPEN:")
    print("   1. Bekijk all_lines.png voor lijnverschillen")
    print("   2. Vergelijk visueel de dewarped bestanden")
    print("   3. Analyseer waarom EXP score 0.000 is")
    print("   4. Check of experimentele filters wel actief waren")

if __name__ == "__main__":
    analyze_experiment_results()
