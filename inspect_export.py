#!/usr/bin/env python3
"""
Inspect de gegenereerde ScanTailor export files.
"""

import json
from pathlib import Path

def inspect_textblocks():
    """Bekijk de textblocks.json export - UPDATED voor nieuwe structure."""
    
    textblock_file = Path("scantailor_export/textblocks.json")
    
    if not textblock_file.exists():
        print("❌ textblocks.json niet gevonden!")
        return
    
    with open(textblock_file, 'r') as f:
        data = json.load(f)
    
    print("=== TEXTBLOCKS.JSON INSPECTION ===")
    print(f"Format version: {data['format_version']}")
    print(f"Image dimensions: {data['image_dimensions']['width']}x{data['image_dimensions']['height']}")
    print(f"Number of distortion models: {len(data['distortion_models'])}")
    print()
    
    print("📦 DISTORTION MODELS:")
    for i, model in enumerate(data['distortion_models']):
        print(f"\n  Model {i+1} (Block ID {model['block_id']}):")
        print(f"    Baselines: {model['num_baselines']} lines")
        print(f"    Baseline IDs: {model.get('baseline_ids', 'N/A')}")
        print(f"    Bounds: {model['bounds']['left']:.0f},{model['bounds']['top']:.0f} to {model['bounds']['right']:.0f},{model['bounds']['bottom']:.0f}")
        print(f"    Distortion type: {model['distortion_type']}")
        
        # Handle nieuwe confidence_data structure
        confidence_data = model.get('confidence_data', {})
        if confidence_data:
            overall_confidence = confidence_data.get('overall_confidence', 0.0)
            metrics = confidence_data.get('metrics', {})
            
            print(f"    Overall confidence: {overall_confidence:.2f}")
            print(f"    Curvature category: {metrics.get('curvature_category', 'UNKNOWN')}")
            print(f"    Curvature estimate: {metrics.get('curvature_estimate', 0.0):.1f}")
            print(f"    Deuk probability: {metrics.get('deuk_probability', 0.0):.2f}")
        else:
            # Fallback voor oude structure
            confidence = model.get('confidence', 0.0)
            print(f"    Confidence: {confidence:.2f}")
        
        # Spline info
        spline_params = model.get('spline_params', {})
        top_spline = spline_params.get('top_spline', {})
        bottom_spline = spline_params.get('bottom_spline', {})
        
        if top_spline and bottom_spline:
            print(f"    Top spline: {len(top_spline.get('control_points', []))} control points")
            print(f"    Bottom spline: {len(bottom_spline.get('control_points', []))} control points")
            
            # Show first/last control points
            top_points = top_spline.get('control_points', [])
            bottom_points = bottom_spline.get('control_points', [])
            
            if top_points:
                first_top = top_points[0]
                last_top = top_points[-1]
                print(f"      Top range: ({first_top['x']:.0f},{first_top['y']:.0f}) to ({last_top['x']:.0f},{last_top['y']:.0f})")
            
            if bottom_points:
                first_bottom = bottom_points[0]
                last_bottom = bottom_points[-1]
                print(f"      Bottom range: ({first_bottom['x']:.0f},{first_bottom['y']:.0f}) to ({last_bottom['x']:.0f},{last_bottom['y']:.0f})")

def inspect_baselines():
    """Bekijk de baselines.json export."""
    
    baseline_file = Path("scantailor_export/baselines.json")
    
    if not baseline_file.exists():
        print("❌ baselines.json niet gevonden!")
        return
    
    with open(baseline_file, 'r') as f:
        data = json.load(f)
    
    print("\n=== BASELINES.JSON INSPECTION ===")
    print(f"Format version: {data['format_version']}")
    print(f"Image dimensions: {data['image_dimensions']['width']}x{data['image_dimensions']['height']}")
    print(f"Number of baselines: {len(data['baselines'])}")
    print()
    
    print("📏 BASELINES:")
    for i, baseline in enumerate(data['baselines'][:5]):  # Show first 5
        print(f"\n  Baseline {i+1} (ID {baseline['id']}):")
        print(f"    Points: {baseline['num_points']}")
        print(f"    Bounds: {baseline['bounds']['left']:.0f},{baseline['bounds']['top']:.0f} to {baseline['bounds']['right']:.0f},{baseline['bounds']['bottom']:.0f}")
        print(f"    Curvature: {baseline['curvature_estimate']:.1f}")
        print(f"    Confidence: {baseline['confidence']:.2f}")
        
        # Show first few points
        points = baseline['points'][:3]
        point_str = ", ".join([f"({p['x']:.0f},{p['y']:.0f})" for p in points])
        print(f"    First points: {point_str}...")
    
    if len(data['baselines']) > 5:
        print(f"\n  ... and {len(data['baselines']) - 5} more baselines")

def find_deuk_blocks():
    """Zoek specifiek naar de 'deuk' blokken uit ECHTE JSON data - UPDATED."""
    
    textblock_file = Path("scantailor_export/textblocks.json")
    
    if not textblock_file.exists():
        print("❌ textblocks.json niet gevonden!")
        return
    
    with open(textblock_file, 'r') as f:
        data = json.load(f)
    
    print("\n=== ENHANCED DEUK BLOCK ANALYSIS ===")
    
    # Analyseer ALLE blocks op basis van confidence_data
    deuk_candidates = []
    normal_blocks = []
    
    for model in data['distortion_models']:
        confidence_data = model.get('confidence_data', {})
        metrics = confidence_data.get('metrics', {})
        
        # Gebruik ECHTE curvature data uit JSON
        curvature_category = metrics.get('curvature_category', 'UNKNOWN')
        deuk_probability = metrics.get('deuk_probability', 0.5)
        curvature_estimate = metrics.get('curvature_estimate', 0.0)
        baseline_ids = model.get('baseline_ids', [])
        
        block_info = {
            'model': model,
            'curvature_category': curvature_category,
            'deuk_probability': deuk_probability,
            'curvature_estimate': curvature_estimate,
            'baseline_ids': baseline_ids,
            'overall_confidence': confidence_data.get('overall_confidence', 0.0)
        }
        
        # Categoriseer op basis van ECHTE data
        if curvature_category in ['HIGH_CURVATURE_DEUK', 'MODERATE_CURVATURE']:
            deuk_candidates.append(block_info)
        else:
            normal_blocks.append(block_info)
    
    # Sort by deuk probability
    deuk_candidates.sort(key=lambda x: x['deuk_probability'], reverse=True)
    normal_blocks.sort(key=lambda x: x['overall_confidence'], reverse=True)
    
    print(f"🎯 Found {len(deuk_candidates)} potential DEUK blocks:")
    for i, candidate in enumerate(deuk_candidates):
        model = candidate['model']
        bounds = model['bounds']
        
        print(f"\n  🔍 DEUK Candidate {i+1} (Block ID {model['block_id']}):")
        print(f"    Y-range: {bounds['top']:.0f} - {bounds['bottom']:.0f}")
        print(f"    Baseline IDs: {candidate['baseline_ids']}")
        print(f"    Curvature: {candidate['curvature_category']} ({candidate['curvature_estimate']:.1f})")
        print(f"    Deuk probability: {candidate['deuk_probability']:.2f}")
        print(f"    Overall confidence: {candidate['overall_confidence']:.2f}")
        print(f"    Lines: {model['num_baselines']}")
        
        # Check if this matches expected deuk pattern
        if bounds['top'] < 1000 and candidate['curvature_estimate'] > 20:
            print(f"    ⚠️  STRONG DEUK CANDIDATE (top region + high curvature)")
    
    print(f"\n📝 Found {len(normal_blocks)} normal (non-deuk) blocks:")
    for i, block_info in enumerate(normal_blocks[:5]):  # Show top 5
        model = block_info['model']
        bounds = model['bounds']
        
        print(f"\n  ✅ Normal Block {i+1} (Block ID {model['block_id']}):")
        print(f"    Y-range: {bounds['top']:.0f} - {bounds['bottom']:.0f}")
        print(f"    Baseline IDs: {block_info['baseline_ids']}")
        print(f"    Curvature: {block_info['curvature_category']} ({block_info['curvature_estimate']:.1f})")
        print(f"    Overall confidence: {block_info['overall_confidence']:.2f}")
        print(f"    Lines: {model['num_baselines']}")
    
    if len(normal_blocks) > 5:
        print(f"\n  ... and {len(normal_blocks) - 5} more normal blocks")

if __name__ == '__main__':
    inspect_textblocks()
    inspect_baselines() 
    find_deuk_blocks()
