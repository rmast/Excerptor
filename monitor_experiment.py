#!/usr/bin/env python3
"""
Real-time monitor voor het lopende experiment.
Volgt de output en verzamelt statistieken.
"""

import re
import time
import os
from collections import defaultdict

def monitor_experiment():
    """Monitor de lopende experimenten en verzamel statistieken."""
    
    print("🔬 EXPERIMENT MONITOR")
    print("=" * 50)
    
    # Verzamel statistieken
    std_scores = []
    exp_scores = []
    line_stats = []
    
    # Monitor log bestanden
    log_files = ['test_std.md', 'test_exp.md']
    
    print("Wachtend op resultaten...")
    print("(Druk Ctrl+C om te stoppen)")
    
    try:
        while True:
            # Check of er nieuwe debug output is
            if os.path.exists('dewarp/all_lines.png'):
                print("✅ Debug afbeeldingen gegenereerd")
                
            # Monitor voor kwaliteitsscores in terminal output zou hier komen
            # (In praktijk zou je naar log files of stdout monitoring kijken)
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n📊 VOORLOPIGE ANALYSE")
        print("=" * 30)
        print("Monitor gestopt. Bekijk handmatig:")
        print("- dewarp/all_lines.png")
        print("- dewarp/surface_lines.png") 
        print("- test_std/ vs test_exp/ directories")

def extract_scores_from_terminal():
    """Helper om scores uit terminal te halen (placeholder)."""
    # Dit zou normaal gesproken de terminal output parsen
    pass

if __name__ == "__main__":
    monitor_experiment()
