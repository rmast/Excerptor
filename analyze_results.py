#!/usr/bin/env python3
"""
Analyse script voor filter-experiment resultaten.
Vergelijkt de kwaliteit van dewarping tussen verschillende filter-instellingen.
"""

import os
import re
import cv2
import numpy as np
from typing import Dict, List, Tuple

def extract_quality_scores(log_file: str) -> List[Tuple[str, str, float]]:
    """Extract quality scores from log file."""
    scores = []
    if not os.path.exists(log_file):
        return scores
        
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Zoek naar lijnen zoals: "Dewarping kwaliteit Scan_20250618 (8)_1L_L (STD): 0.856"
    pattern = r'Dewarping kwaliteit (\S+) \((\w+)\): ([\d.]+)'
    matches = re.findall(pattern, content)
    
    for match in matches:
        image_name, filter_type, score = match
        scores.append((image_name, filter_type, float(score)))
    
    return scores

def count_lines_from_debug_output(log_file: str) -> List[Tuple[str, int, int, float]]:
    """Extract line count information from debug output."""
    line_counts = []
    if not os.path.exists(log_file):
        return line_counts
        
    with open(log_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Zoek naar lijnen zoals: "Lijnfiltering: 45 -> 32 lijnen (behouden: 71.1%)"
    pattern = r'Lijnfiltering: (\d+) -> (\d+) lijnen \(behouden: ([\d.]+)%\)'
    matches = re.findall(pattern, content)
    
    for i, match in enumerate(matches):
        before, after, percentage = match
        line_counts.append((f"image_{i}", int(before), int(after), float(percentage)))
    
    return line_counts

def analyze_results():
    """Analyseer de experimentele resultaten."""
    print("=== ANALYSE VAN FILTER-EXPERIMENTEN ===\n")
    
    # 1. Vergelijk kwaliteitsscores
    print("1. KWALITEITSSCORES VERGELIJKING")
    print("-" * 40)
    
    # Lees terminal output voor scores (als beschikbaar)
    # In praktijk zouden we dit uit de terminal output halen
    print("Tip: Zoek in de terminal output naar lijnen met 'Dewarping kwaliteit'")
    print("Format: 'Dewarping kwaliteit <naam> (<filter>): <score>'")
    print()
    
    # 2. Vergelijk lijnfiltering
    print("2. LIJNFILTERING VERGELIJKING") 
    print("-" * 40)
    print("Tip: Zoek in de terminal output naar lijnen met 'Lijnfiltering'")
    print("Format: 'Lijnfiltering: X -> Y lijnen (behouden: Z%)'")
    print()
    
    # 3. Visuele analyse instructies
    print("3. VISUELE ANALYSE INSTRUCTIES")
    print("-" * 40)
    print("Vergelijk de volgende bestanden:")
    print()
    print("a) all_lines.png vergelijking:")
    print("   - STD: dewarp/all_lines.png (na standaard run)")
    print("   - EXP: dewarp/all_lines.png (na experimentele run)")
    print("   - Let op: meer blauwe lijnen in EXP = meer lijnen behouden")
    print()
    print("b) Dewarped resultaten:")
    print("   - STD: test_std/*_dewarped.*")
    print("   - EXP: test_exp/*_dewarped.*")
    print("   - Visueel: welke zijn rechter/meer leesbaar?")
    print()
    print("c) Surface lines vergelijking:")
    print("   - surface_lines.png toont finale 3D oppervlaklijnen")
    print("   - Groene lijnen moeten goed aansluiten bij tekstlijnen")
    print()
    
    # 4. Meetbare criteria
    print("4. MEETBARE CRITERIA")
    print("-" * 40)
    print("Voor elke test meet:")
    print("- Aantal gedetecteerde lijnen (rood in all_lines.png)")
    print("- Aantal behouden lijnen (blauw in all_lines.png)")
    print("- Percentage behouden (%)")
    print("- Rechtheid score (uit terminal)")
    print("- Visuele kwaliteit (1-5 schaal)")
    print()
    
    # 5. Aanbevelingen voor vervolgstappen
    print("5. VERVOLGSTAPPEN")
    print("-" * 40)
    print("Gebaseerd op resultaten, overweeg:")
    print("- Als EXP beter: verlaag remove_outliers threshold verder (naar 30+)")
    print("- Als STD beter: verhoog stroke_outliers k-waarde")
    print("- Als mixed: implementeer adaptieve filtering")
    print("- Test meer variaties voor robuuste conclusie")
    print()

if __name__ == "__main__":
    analyze_results()
