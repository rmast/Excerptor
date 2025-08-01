#!/usr/bin/env python3
"""
Bridge tussen Python text detection en ScanTailor Deviant C++ interface.
Exporteert detected baselines en textblocks voor import in MultiBlockDistortionModel.
"""

import cv2
import numpy as np
import json
import xml.etree.ElementTree as ET
from rebook.dewarp import get_AH_lines
from rebook import binarize, lib
from pathlib import Path

def export_for_scantailor(image_path, output_dir="scantailor_export"):
    """Export detected baselines en textblocks voor ScanTailor Deviant."""
    
    print("=== SCANTAILOR DEVIANT BRIDGE ===")
    print("Export Python detection results naar C++ compatible format")
    print()
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Load and process image
    im = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    h, w = im.shape[:2]
    
    print(f"Processing image: {w}x{h} pixels")
    
    # Detect text lines
    lib.debug = False  # Quiet mode voor export
    bw = binarize.binarize(im, algorithm=lambda im: binarize.sauvola_noisy(im, k=0.1))
    
    import rebook.dewarp as dewarp_module
    dewarp_module.bw = bw
    
    AH, lines, all_lines, letters = get_AH_lines(bw)
    
    print(f"Detected {len(lines)} text lines")
    
    if len(lines) < 2:
        print("❌ Insufficient lines for export")
        return
    
    # Import our smart textblock detection
    from spline_based_dewarp import identify_textblocks_smart
    
    lines_sorted = sorted(lines, key=lambda l: l.base_points()[:, 1].mean())
    textblocks = identify_textblocks_smart(lines_sorted, AH)
    
    print(f"Identified {len(textblocks)} textblocks")
    
    # EXPORT 1: Baseline data compatible met BaselineDetector.cpp
    baseline_data = export_baseline_data(lines_sorted, w, h)
    
    # EXPORT 2: TextBlock data met CORRECTE baseline mapping
    textblock_data = export_textblock_data(textblocks, w, h, lines_sorted)
    
    # EXPORT 3: Combined XML voor ScanTailor project integration
    combined_xml = create_scantailor_xml(baseline_data, textblock_data, image_path, w, h)
    
    # EXPORT 4: C++ header file template
    create_cpp_interface(baseline_data, textblock_data, output_path)
    
    # Save exports
    baseline_file = output_path / "baselines.json" 
    textblock_file = output_path / "textblocks.json"
    xml_file = output_path / "dewarping_data.xml"
    
    with open(baseline_file, 'w') as f:
        json.dump(baseline_data, f, indent=2)
    
    with open(textblock_file, 'w') as f:
        json.dump(textblock_data, f, indent=2)
    
    with open(xml_file, 'w') as f:
        f.write(ET.tostring(combined_xml, encoding='unicode'))
    
    # ENHANCED ANALYSIS: Show mapping
    print(f"\n🔗 BASELINE-TO-TEXTBLOCK MAPPING:")
    for model in textblock_data["distortion_models"]:
        block_id = model["block_id"]
        baseline_ids = model["baseline_ids"]
        confidence_data = model["confidence_data"]
        
        print(f"   Block {block_id}: baselines {baseline_ids}")
        print(f"     Curvature: {confidence_data['metrics']['curvature_category']} ({confidence_data['metrics']['curvature_estimate']:.1f})")
        print(f"     Deuk probability: {confidence_data['metrics']['deuk_probability']:.1f}")
        print(f"     Overall confidence: {confidence_data['overall_confidence']:.2f}")
        
        if confidence_data['metrics']['curvature_category'] in ['HIGH_CURVATURE_DEUK', 'MODERATE_CURVATURE']:
            print(f"     ⚠️  POTENTIAL DEUK BLOCK!")
    
    # ENHANCED ANALYSIS: Show geographic super block mapping
    print(f"\n🗺️ GEOGRAPHIC SUPER BLOCK CLASSIFICATION (CURVATURE BOUNDARIES):")
    
    super_block_info = textblock_data["geographic_super_blocks"]
    print(f"   Strategy: {super_block_info['strategy']}")
    print(f"   Requested max blocks: {super_block_info['max_blocks_requested']}")
    print(f"   Created {super_block_info['total_blocks']} super blocks")
    
    for super_block in super_block_info["blocks"]:
        super_id = super_block["super_block_id"]
        y_range = super_block["y_range"]
        curvature_info = super_block["curvature_info"]
        baseline_ids = super_block["baseline_ids"]
        
        print(f"\n   📍 SUPER BLOCK {super_id}:")
        print(f"     Description: {super_block['description']}")
        print(f"     Detailed blocks: {super_block['block_ids']}")
        print(f"     Baseline IDs: {baseline_ids}")
        print(f"     Total baselines: {super_block['num_baselines']}")
        print(f"     Y-range: {y_range['top']:.0f} to {y_range['bottom']:.0f}")
        print(f"     Curvature: {curvature_info['category']}")
        print(f"     Max curvature: {curvature_info['max_curvature']:.1f}")
        
        if curvature_info.get('has_distortion', False):
            print(f"     ⚠️  Needs correction ({curvature_info['distorted_count']}/{curvature_info['total_count']} blocks distorted)")
        else:
            print(f"     ✅ Minimal correction needed")
    
    print(f"\n🎯 RESULT FOR SCANTAILOR:")
    print(f"   User gets up to {super_block_info['max_blocks_requested']} geographic text blocks")
    print(f"   Actual blocks created: {super_block_info['total_blocks']}")
    print(f"   Each block shows baseline IDs for individual selection")
    print(f"   Curvature info guides correction priority")
    
    return baseline_data, textblock_data

def export_baseline_data(lines, image_width, image_height):
    """Export baseline data compatible met ScanTailor BaselineDetector format."""
    
    baseline_data = {
        "format_version": "1.0",
        "image_dimensions": {"width": image_width, "height": image_height},
        "baselines": []
    }
    
    for i, line in enumerate(lines):
        points = line.base_points()
        
        # Convert naar ScanTailor coordinate system (top-left origin)
        baseline_points = []
        for point in points:
            baseline_points.append({
                "x": float(point[0]),
                "y": float(point[1])
            })
        
        # Calculate baseline properties zoals ScanTailor verwacht
        y_coords = points[:, 1]
        baseline_info = {
            "id": i,
            "points": baseline_points,
            "num_points": len(baseline_points),
            "bounds": {
                "left": float(points[:, 0].min()),
                "right": float(points[:, 0].max()),
                "top": float(y_coords.min()),
                "bottom": float(y_coords.max())
            },
            "curvature_estimate": float(np.std(y_coords)),  # Simple curvature metric
            "confidence": 1.0,  # Hoge confidence voor onze detection
            "baseline_type": "detected"  # vs "manual" in ScanTailor
        }
        
        baseline_data["baselines"].append(baseline_info)
    
    return baseline_data

def classify_geographic_blocks(models, max_blocks=5):
    """Classify detailed blocks into max_blocks geographic blocks based on PURE curvature boundaries."""
    
    # Sort ALL models by Y-position (top to bottom)
    models_by_y = sorted(models, key=lambda m: m["bounds"]["top"])
    
    print(f"   Analyzing {len(models_by_y)} detailed blocks for curvature boundaries...")
    print(f"   Target: max {max_blocks} super blocks")
    
    # Analyze curvature pattern from top to bottom
    curvature_sequence = []
    for i, model in enumerate(models_by_y):
        metrics = model["confidence_data"]["metrics"]
        curvature_estimate = metrics.get("curvature_estimate", 0.0)
        deuk_probability = metrics.get("deuk_probability", 0.0)
        
        # CLEANER curvature classification
        if deuk_probability >= 0.5:
            curvature_class = "HIGH_DISTORTION"
        elif deuk_probability >= 0.25:
            curvature_class = "MODERATE_DISTORTION"
        else:
            curvature_class = "STRAIGHT"
        
        curvature_sequence.append({
            "block_id": model["block_id"],
            "y_pos": model["bounds"]["top"],
            "curvature": curvature_estimate,
            "deuk_probability": deuk_probability,
            "curvature_class": curvature_class,
            "model": model
        })
        
        print(f"     Block {model['block_id']}: Y={model['bounds']['top']:.0f}, deuk_prob={deuk_probability:.1f}, class={curvature_class}")
    
    # Find curvature boundaries - IMPROVED ALGORITHM
    super_blocks = []
    assignments = {}
    current_super_id = 1
    current_group = []
    current_class = None
    
    for i, item in enumerate(curvature_sequence):
        # Determine if we should start a new super block
        should_start_new = False
        
        if current_class is None:
            # First item
            current_class = item["curvature_class"]
            current_group.append(item)
        elif item["curvature_class"] == current_class:
            # Same class - continue current group
            current_group.append(item)
        else:
            # Different class - finish current group and start new
            should_start_new = True
        
        # Also start new if we're at max_blocks
        if len(current_group) > 0 and (should_start_new or i == len(curvature_sequence) - 1 or current_super_id >= max_blocks):
            
            # Create super block from current group
            block_ids = [x["block_id"] for x in current_group]
            y_top = min(x["y_pos"] for x in current_group)
            y_bottom = max(x["model"]["bounds"]["bottom"] for x in current_group)
            total_baselines = sum(x["model"]["num_baselines"] for x in current_group)
            
            # Assign all models in group to this super block
            for x in current_group:
                assignments[x["block_id"]] = current_super_id
            
            # Analyze group curvature - should be HOMOGENEOUS now
            deuk_probs = [x["deuk_probability"] for x in current_group]
            avg_deuk_prob = np.mean(deuk_probs)
            max_curvature = max(x["curvature"] for x in current_group)
            
            # Group should have consistent curvature class
            dominant_class = current_class
            
            if avg_deuk_prob >= 0.5:
                group_desc = "HIGHLY_DISTORTED"
                needs_correction = True
            elif avg_deuk_prob >= 0.25:
                group_desc = "MODERATELY_DISTORTED"
                needs_correction = True
            else:
                group_desc = "STRAIGHT"
                needs_correction = False
            
            # Collect baseline IDs
            baseline_ids = []
            for x in current_group:
                baseline_ids.extend(x["model"]["baseline_ids"])
            baseline_ids.sort()
            
            super_blocks.append({
                "super_block_id": current_super_id,
                "description": f"Tekstblok {current_super_id} (Y {y_top:.0f}-{y_bottom:.0f})",
                "block_ids": block_ids,
                "baseline_ids": baseline_ids,
                "y_range": {"top": y_top, "bottom": y_bottom},
                "curvature_info": {
                    "category": group_desc,
                    "has_distortion": needs_correction,
                    "max_curvature": float(max_curvature),
                    "avg_deuk_probability": float(avg_deuk_prob),
                    "distorted_count": sum(1 for x in current_group if x["deuk_probability"] >= 0.25),
                    "total_count": len(current_group),
                    "curvature_class": dominant_class
                },
                "num_baselines": total_baselines,
                "count": len(current_group)
            })
            
            print(f"   Created Super Block {current_super_id}: {len(current_group)} blocks, class={dominant_class}, avg_deuk={avg_deuk_prob:.2f}")
            
            # Start next super block
            current_super_id += 1
            current_group = []
            current_class = None
            
            # Add current item to new group if there was a class change
            if should_start_new and current_super_id <= max_blocks:
                current_class = item["curvature_class"]
                current_group.append(item)
            
            if current_super_id > max_blocks:
                break
    
    return {
        "assignments": assignments,
        "super_blocks": super_blocks
    }

def export_textblock_data(textblocks, image_width, image_height, lines_sorted):
    """Export textblock data met geografische super blocks (max 5 - PARAMETERIZED)."""
    
    textblock_data = {
        "format_version": "1.0", 
        "image_dimensions": {"width": image_width, "height": image_height},
        "distortion_models": [],
        "super_blocks": {
            "deuk_blocks": [],
            "main_content_block": None,
            "minor_blocks": []
        }
    }
    
    # Create mapping van lines naar baseline IDs
    line_to_baseline_id = {}
    for baseline_id, line in enumerate(lines_sorted):
        line_to_baseline_id[id(line)] = baseline_id
    
    # Collect all distortion models first
    all_models = []
    
    for block_idx, block in enumerate(textblocks):
        if len(block) < 1:  # Skip empty blocks
            continue
        
        # Calculate block boundaries
        all_points = []
        block_baseline_ids = []
        
        for line in block:
            all_points.extend(line.base_points())
            # Find REAL baseline ID voor deze line
            baseline_id = line_to_baseline_id.get(id(line), -1)
            if baseline_id >= 0:
                block_baseline_ids.append(baseline_id)
        
        if not block_baseline_ids:
            continue  # Skip blocks zonder geldige baseline IDs
            
        all_points = np.array(all_points)
        
        # Determine top en bottom baselines voor deze block
        block_lines = sorted(block, key=lambda l: l.base_points()[:, 1].mean())
        top_line = block_lines[0]
        bottom_line = block_lines[-1]
        
        # Find baseline IDs
        top_baseline_id = line_to_baseline_id.get(id(top_line), -1)
        bottom_baseline_id = line_to_baseline_id.get(id(bottom_line), -1)
        
        # Calculate enhanced confidence including super block classification
        confidence_data = calculate_enhanced_block_confidence(block)
        
        distortion_model = {
            "block_id": block_idx,
            "num_baselines": len(block),
            "baseline_ids": sorted(block_baseline_ids),
            "top_baseline_id": top_baseline_id,
            "bottom_baseline_id": bottom_baseline_id,
            "bounds": {
                "left": float(all_points[:, 0].min()),
                "right": float(all_points[:, 0].max()),
                "top": float(all_points[:, 1].min()),
                "bottom": float(all_points[:, 1].max())
            },
            "distortion_type": "cylindrical",
            "spline_params": {
                "top_spline": extract_spline_params(top_line, image_width),
                "bottom_spline": extract_spline_params(bottom_line, image_width)
            },
            "confidence_data": confidence_data,
            "user_modified": False
        }
        
        all_models.append(distortion_model)
    # CLASSIFY INTO max_blocks GEOGRAPHIC SUPER BLOCKS based on curvature boundaries
    classification = classify_geographic_blocks(all_models, max_blocks=5)  # RESPECTS PARAMETER
    
    # Add super_block_id to each model AND sort by super_block_id for output ordering
    for model in all_models:
        block_id = model["block_id"]
        model["super_block_id"] = classification["assignments"].get(block_id, 3)  # Default to 3rd block
    
    # Sort models by super_block_id, then by Y-position within each super block
    def sort_key(model):
        super_id = model["super_block_id"]
        y_pos = model["bounds"]["top"]
        return (super_id, y_pos)
    
    all_models.sort(key=sort_key)
    
    # Add to textblock_data in proper order
    for model in all_models:
        textblock_data["distortion_models"].append(model)
    
    # Add geographic super block summary
    textblock_data["geographic_super_blocks"] = {
        "strategy": "curvature_boundaries",
        "max_blocks_requested": 5,  # SHOW REQUESTED LIMIT
        "total_blocks": len(classification["super_blocks"]),
        "blocks": classification["super_blocks"]
    }
    
    return textblock_data

def calculate_enhanced_block_confidence(block):
    """Calculate enhanced confidence met curvature en quality metrics."""
    
    if len(block) < 1:
        return {"overall_confidence": 0.0, "metrics": {}}
    
    # Factors die confidence beïnvloeden
    num_lines_score = min(1.0, len(block) / 5.0)  # Optimal bij 5+ lijnen
    
    # Check line spacing regularity
    y_positions = [line.base_points()[:, 1].mean() for line in block]
    y_positions = sorted(y_positions)
    
    if len(y_positions) > 2:
        gaps = np.diff(y_positions)
        gap_consistency = 1.0 - (np.std(gaps) / np.mean(gaps)) if np.mean(gaps) > 0 else 0.5
        gap_consistency = max(0.0, min(1.0, gap_consistency))
    else:
        gap_consistency = 0.8
    
    # Analyze curvature van eerste lijn (deuk indicator)
    first_line = block[0]
    points = first_line.base_points()
    
    if len(points) >= 3:
        y_coords = points[:, 1]
        curvature_estimate = float(np.std(y_coords))
        
        # Curvature category
        if curvature_estimate > 20.0:
            curvature_category = "HIGH_CURVATURE_DEUK"
            deuk_probability = 0.9
        elif curvature_estimate > 10.0:
            curvature_category = "MODERATE_CURVATURE"
            deuk_probability = 0.6
        elif curvature_estimate > 5.0:
            curvature_category = "LOW_CURVATURE"
            deuk_probability = 0.3
        else:
            curvature_category = "STRAIGHT"
            deuk_probability = 0.1
    else:
        curvature_estimate = 0.0
        curvature_category = "UNKNOWN"
        deuk_probability = 0.5
    
    # Overall confidence
    overall_confidence = 0.4 * num_lines_score + 0.3 * gap_consistency + 0.3 * (1.0 - min(deuk_probability, 0.8))
    
    return {
        "overall_confidence": float(overall_confidence),
        "metrics": {
            "num_lines_score": float(num_lines_score),
            "gap_consistency": float(gap_consistency),
            "curvature_estimate": curvature_estimate,
            "curvature_category": curvature_category,
            "deuk_probability": float(deuk_probability)
        }
    }

def default_confidence():
    """Return default confidence metrics."""
    return {
        "overall_confidence": 0.0,
        "metrics": {
            "num_lines_score": 0.0,
            "gap_consistency": 0.0,
            "curvature_estimate": 0.0,
            "curvature_category": "UNKNOWN",
            "deuk_probability": 0.0
        }
    }

def analyze_super_block_curvature(models_group):
    """Analyze curvature properties of a super block group."""
    
    all_curvatures = []
    high_curvature_count = 0
    total_lines = 0
    
    for model in models_group:
        confidence_data = model["confidence_data"]
        metrics = confidence_data["metrics"]
        
        curvature_category = metrics.get("curvature_category", "UNKNOWN")
        curvature_estimate = metrics.get("curvature_estimate", 0.0)
        
        all_curvatures.append(curvature_estimate)
        total_lines += model["num_baselines"]
        
        if curvature_category in ["HIGH_CURVATURE_DEUK", "MODERATE_CURVATURE"]:
            high_curvature_count += 1
    
    # Calculate super block curvature properties
    max_curvature = max(all_curvatures) if all_curvatures else 0.0
    avg_curvature = np.mean(all_curvatures) if all_curvatures else 0.0
    
    # Determine overall category
    distortion_ratio = high_curvature_count / len(models_group)
    
    if distortion_ratio >= 0.5:  # Majority has distortion
        category = "HIGHLY_DISTORTED"
        has_distortion = True
        severity = "HIGH"
    elif distortion_ratio > 0 and max_curvature > 15.0:  # Some distortion, high max
        category = "MODERATELY_DISTORTED" 
        has_distortion = True
        severity = "MODERATE"
    elif distortion_ratio > 0:  # Some distortion, low max
        category = "SLIGHTLY_DISTORTED"
        has_distortion = True
        severity = "LOW"
    else:  # No significant distortion
        category = "STRAIGHT"
        has_distortion = False
        severity = "NONE"
    
    return {
        "category": category,
        "has_distortion": has_distortion,
        "severity": severity,
        "max_curvature": float(max_curvature),
        "avg_curvature": float(avg_curvature),
        "distorted_blocks": high_curvature_count,
        "total_blocks": len(models_group),
        "distortion_ratio": float(distortion_ratio)
    }

def create_scantailor_xml(baseline_data, textblock_data, image_path, width, height):
    """Create XML structure compatible met ScanTailor project format."""
    
    root = ET.Element("dewarping_data")
    root.set("version", "1.0")
    
    # Image info
    image_elem = ET.SubElement(root, "image")
    image_elem.set("path", str(image_path))
    image_elem.set("width", str(width))
    image_elem.set("height", str(height))
    
    # Baselines section
    baselines_elem = ET.SubElement(root, "baselines")
    for baseline in baseline_data["baselines"]:
        baseline_elem = ET.SubElement(baselines_elem, "baseline")
        baseline_elem.set("id", str(baseline["id"]))
        baseline_elem.set("confidence", str(baseline["confidence"]))
        
        points_elem = ET.SubElement(baseline_elem, "points")
        for point in baseline["points"]:
            point_elem = ET.SubElement(points_elem, "point")
            point_elem.set("x", str(point["x"]))
            point_elem.set("y", str(point["y"]))
    
    # TextBlocks section - FIXED voor nieuwe confidence structure
    blocks_elem = ET.SubElement(root, "textblocks")
    for model in textblock_data["distortion_models"]:
        block_elem = ET.SubElement(blocks_elem, "textblock")
        block_elem.set("id", str(model["block_id"]))
        block_elem.set("type", model["distortion_type"])
        
        # Handle nieuwe confidence_data structure
        confidence_data = model.get("confidence_data", {})
        overall_confidence = confidence_data.get("overall_confidence", 0.5)
        block_elem.set("confidence", str(overall_confidence))
        
        # Add curvature metadata
        metrics = confidence_data.get("metrics", {})
        if metrics:
            block_elem.set("curvature_category", metrics.get("curvature_category", "UNKNOWN"))
            block_elem.set("curvature_estimate", str(metrics.get("curvature_estimate", 0.0)))
            block_elem.set("deuk_probability", str(metrics.get("deuk_probability", 0.5)))
        
        # Baseline mapping
        baseline_ids = model.get("baseline_ids", [])
        block_elem.set("baseline_ids", ",".join(map(str, baseline_ids)))
        block_elem.set("top_baseline_id", str(model.get("top_baseline_id", -1)))
        block_elem.set("bottom_baseline_id", str(model.get("bottom_baseline_id", -1)))
        
        # Top en bottom splines
        splines_elem = ET.SubElement(block_elem, "splines")
        
        top_elem = ET.SubElement(splines_elem, "top_spline")
        for cp in model["spline_params"]["top_spline"]["control_points"]:
            cp_elem = ET.SubElement(top_elem, "control_point")
            cp_elem.set("x", str(cp["x"]))
            cp_elem.set("y", str(cp["y"]))
        
        bottom_elem = ET.SubElement(splines_elem, "bottom_spline")
        for cp in model["spline_params"]["bottom_spline"]["control_points"]:
            cp_elem = ET.SubElement(bottom_elem, "control_point")
            cp_elem.set("x", str(cp["x"]))
            cp_elem.set("y", str(cp["y"]))
    
    return root

def create_cpp_interface(baseline_data, textblock_data, output_path):
    """Create C++ header file template voor ScanTailor integration."""
    
    cpp_header = '''#ifndef PYTHON_DETECTION_BRIDGE_H
#define PYTHON_DETECTION_BRIDGE_H

#include <vector>
#include <string>
#include <memory>

namespace dewarping {

struct DetectedBaseline {
    int id;
    std::vector<QPointF> points;
    QRectF bounds;
    double curvature_estimate;
    double confidence;
    bool user_modified = false;
};

struct DetectedTextBlock {
    int block_id;
    std::vector<int> baseline_ids;
    int top_baseline_id;
    int bottom_baseline_id;
    QRectF bounds;
    std::string distortion_type;
    double confidence;
    bool user_modified = false;
    
    // Spline control points
    std::vector<QPointF> top_spline_points;
    std::vector<QPointF> bottom_spline_points;
};

class PythonDetectionBridge {
public:
    static bool loadDetectionResults(const std::string& baseline_file,
                                   const std::string& textblock_file);
    
    static std::vector<DetectedBaseline> getBaselines();
    static std::vector<DetectedTextBlock> getTextBlocks();
    
    // Integration met bestaande ScanTailor classes
    static void populateBaselineDetector(BaselineDetector& detector);
    static void populateMultiBlockModel(MultiBlockDistortionModel& model);
    
private:
    static std::vector<DetectedBaseline> baselines_;
    static std::vector<DetectedTextBlock> textblocks_;
};

} // namespace dewarping

#endif // PYTHON_DETECTION_BRIDGE_H'''
    
    with open(output_path / "scantailor_interface.h", 'w') as f:
        f.write(cpp_header)

def extract_spline_params(line, image_width):
    """Extract spline parameters zoals ScanTailor ze verwacht."""
    
    points = line.base_points()
    
    # Sort by X coordinate
    sorted_points = points[np.argsort(points[:, 0])]
    
    # Create control points voor spline (ScanTailor gebruikt meestal B-splines)
    control_points = []
    
    # Sample points across image width
    x_samples = np.linspace(0, image_width - 1, min(10, len(sorted_points)))
    
    for x in x_samples:
        # Interpolate Y value at this X
        if len(sorted_points) > 1:
            y = np.interp(x, sorted_points[:, 0], sorted_points[:, 1])
        else:
            y = sorted_points[0, 1]
        
        control_points.append({"x": float(x), "y": float(y)})
    
    return {
        "control_points": control_points,
        "spline_type": "linear",  # of "cubic", "bezier" etc.
        "extrapolation": "linear"
    }

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python scantailor_bridge.py <image_path> [output_dir]")
        sys.exit(1)
        
    image_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "scantailor_export"
    
    baseline_data, textblock_data = export_for_scantailor(image_path, output_dir)
    
    print(f"\n🔗 Ready for ScanTailor Deviant integration!")
    print(f"   Next: Implement PythonDetectionBridge in C++")
    print(f"   Load: {output_dir}/baselines.json + {output_dir}/textblocks.json")
