#!/usr/bin/env python3
"""
Spline-based dewarp - gebruik detected text lines als top/bottom splines voor cylindrical correction.
Gebaseerd op ScanTailor Deviant aanpak.
"""

import cv2
import numpy as np
from rebook.dewarp import get_AH_lines
from rebook import binarize, lib
from rebook.geometry import Crop
from scipy import interpolate

def spline_based_dewarp(image_path, f_value=3500):
    """Extract text lines en gebruik als splines voor cylindrical dewarp."""
    
    print("=== SPLINE-BASED DEWARP ===")
    print("Aanpak: ScanTailor Deviant-style cylindrical correction")
    print("Gebruik detected text lines als top/bottom splines")
    print()
    
    im = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    
    # Stap 1: Extract text lines (de blauwe lijnen uit all_lines.png)
    print("1. TEXT LINE DETECTION")
    print("-" * 25)
    
    # Binarize en detect lines zoals in dewarp
    lib.debug = True
    lib.debug_prefix = ['spline']
    bw = binarize.binarize(im, algorithm=lambda im: binarize.sauvola_noisy(im, k=0.1))
    
    # Set global bw for dewarp functions
    import rebook.dewarp as dewarp_module
    dewarp_module.bw = bw
    
    AH, lines, all_lines, letters = get_AH_lines(bw)
    
    print(f"   Detected lines: {len(lines)}")
    print(f"   All lines (raw): {len(all_lines)}")
    print(f"   Average Height: {AH}")
    
    if len(lines) < 2:
        print("   ❌ Te weinig lijnen gedetecteerd voor spline creation")
        return
    
    # Stap 2: ENHANCED SPLINE SELECTION
    print(f"\n2. ENHANCED SPLINE SELECTION")
    print("-" * 35)
    
    lines_sorted = sorted(lines, key=lambda l: l.base_points()[:, 1].mean())
    
    # Show all available blocks first with ENHANCED analysis
    textblocks = identify_textblocks_smart(lines_sorted, AH)
    
    print(f"\n   🔍 TEXTBLOCK SELECTION STRATEGY:")
    print(f"   Available blocks: {len(textblocks)}")
    
    # Find blocks with high curvature (potential "deuk" areas)
    curvature_blocks = []
    for i, block in enumerate(textblocks):
        if len(block) >= 2:  # Need at least 2 lines
            first_line = block[0]
            points = first_line.base_points()
            if len(points) >= 3:
                curvature_estimate = np.std(points[:, 1])
                if curvature_estimate > 3.0:  # Threshold for "deuk"
                    curvature_blocks.append((i, block, curvature_estimate))
                    print(f"     Block {i+1}: DEUK CANDIDATE (curvature={curvature_estimate:.1f})")
    
    # ENHANCED SPLINE OPTIONS based on detected blocks
    spline_options = []
    
    # Always include full page
    spline_options.append({
        "name": "full_page",
        "description": "Volledige pagina: eerste tot laatste lijn",
        "top_line": lines_sorted[0],
        "bottom_line": lines_sorted[-1]
    })
    
    # Add curvature-based options
    for i, (block_idx, block, curvature) in enumerate(curvature_blocks[:2]):  # Max 2 deuk blocks
        spline_options.append({
            "name": f"deuk_block_{block_idx+1}",
            "description": f"Deuk Block {block_idx+1}: {len(block)} lijnen (curvature={curvature:.1f})",
            "top_line": block[0],
            "bottom_line": block[-1]
        })
    
    # Add largest block
    if textblocks:
        largest_block = max(textblocks, key=len)
        spline_options.append({
            "name": "largest_block",
            "description": f"Grootste tekstblok: {len(largest_block)} lijnen",
            "top_line": largest_block[0],
            "bottom_line": largest_block[-1]
        })
    
    print(f"\n   📋 SELECTED TEST CONFIGURATIONS:")
    for opt in spline_options:
        print(f"     • {opt['name']}: {opt['description']}")
    
    # Test with curvature analysis
    for i, option in enumerate(spline_options):
        print(f"\n   → Testing {option['name']}: {option['description']}")
        
        top_line = option['top_line']
        bottom_line = option['bottom_line']
        
        print(f"     Top line Y: {top_line.base_points()[:, 1].mean():.1f}")
        print(f"     Bottom line Y: {bottom_line.base_points()[:, 1].mean():.1f}")
        
        # Analyze curvature of the lines themselves
        analyze_line_curvature(top_line, option['name'])
        
        # Create splines with page boundary constraints
        top_spline, bottom_spline = create_splines_with_boundaries(
            top_line, bottom_line, im.shape[1], im.shape[0]
        )
        
        # Visualize
        visualize_splines_enhanced(im, top_spline, bottom_spline, lines_sorted, 
                                 [top_line, bottom_line], option['name'])
        
        # Quick test
        scale_factor = 0.3  # Smaller for speed
        small_im = cv2.resize(im, None, fx=scale_factor, fy=scale_factor)
        small_w = small_im.shape[1]
        
        small_top = np.interp(np.linspace(0, len(top_spline)-1, small_w), 
                             np.arange(len(top_spline)), top_spline) * scale_factor
        small_bottom = np.interp(np.linspace(0, len(bottom_spline)-1, small_w),
                                np.arange(len(bottom_spline)), bottom_spline) * scale_factor
        
        try:
            corrected_small = apply_cylindrical_correction(small_im, small_top, small_bottom, option['name'])
            cv2.imwrite(f'dewarp/spline_test_{option["name"]}.png', corrected_small)
            print(f"     ✓ Test saved: spline_test_{option['name']}.png")
            
        except Exception as e:
            print(f"     ✗ Test failed: {e}")

    # SIMPLIFIED TEST - focus on realistic corrections
    spline_options = [
        {
            "name": "deuk_focus",
            "description": "Focus op deuk: eerste 3 lijnen met realistische correctie",
            "top_line": lines_sorted[0],
            "bottom_line": lines_sorted[2] if len(lines_sorted) > 2 else lines_sorted[-1]
        }
    ]
    
    # Test with REALISTIC strength values
    for i, option in enumerate(spline_options):
        print(f"\n   → Testing {option['name']}: {option['description']}")
        
        top_line = option['top_line']
        bottom_line = option['bottom_line']
        
        print(f"     Top line Y: {top_line.base_points()[:, 1].mean():.1f}")
        print(f"     Bottom line Y: {bottom_line.base_points()[:, 1].mean():.1f}")
        
        # Analyze curvature of the lines themselves
        analyze_line_curvature(top_line, option['name'])
        
        # Create splines with page boundary constraints
        top_spline, bottom_spline = create_splines_with_boundaries(
            top_line, bottom_line, im.shape[1], im.shape[0]
        )
        
        # Visualize
        visualize_splines_enhanced(im, top_spline, bottom_spline, lines_sorted, 
                                 [top_line, bottom_line], option['name'])
        
        # Test different correction strengths with REALISTIC values
        test_strengths = [0.3, 0.5, 0.8, 1.0, 1.5]  # More realistic range
        
        for strength in test_strengths:
            print(f"\n     → Testing realistic strength {strength}...")
            
            # Test on better resolution for visibility
            scale_factor = 0.6  # Larger for better visual assessment
            small_im = cv2.resize(im, None, fx=scale_factor, fy=scale_factor)
            small_w = small_im.shape[1]
            
            small_top = np.interp(np.linspace(0, len(top_spline)-1, small_w), 
                                 np.arange(len(top_spline)), top_spline) * scale_factor
            small_bottom = np.interp(np.linspace(0, len(bottom_spline)-1, small_w),
                                    np.arange(len(bottom_spline)), bottom_spline) * scale_factor
            
            try:
                # Apply realistic correction
                corrected_small = apply_gentle_correction(small_im, small_top, small_bottom, strength)
                cv2.imwrite(f'dewarp/realistic_strength_{strength:.1f}.png', corrected_small)
                print(f"       ✓ Strength {strength}: realistic_strength_{strength:.1f}.png")
                
            except Exception as e:
                print(f"       ✗ Strength {strength} failed: {e}")
        
        # Also test full-size on best strength
        print(f"\n     → Testing full-size with optimal strength...")
        try:
            optimal_strength = 1.0  # Choose based on small tests
            full_corrected = apply_gentle_correction(im, top_spline, bottom_spline, optimal_strength)
            cv2.imwrite('dewarp/full_size_deuk_correction.png', full_corrected)
            print(f"       ✓ Full size: full_size_deuk_correction.png")
        except Exception as e:
            print(f"       ✗ Full size failed: {e}")

def identify_textblocks(lines_sorted, AH):
    """Identificeer tekstblokken op basis van gaps tussen lijnen."""
    if len(lines_sorted) < 2:
        return [lines_sorted]
    
    # Bereken Y-posities
    y_positions = [line.base_points()[:, 1].mean() for line in lines_sorted]
    
    # Detecteer grote gaps (>2x gemiddelde regel afstand)
    gaps = np.diff(y_positions)
    median_gap = np.median(gaps)
    large_gap_threshold = 2.0 * median_gap
    
    # Split op grote gaps
    blocks = []
    current_block = [lines_sorted[0]]
    
    for i, gap in enumerate(gaps):
        if gap > large_gap_threshold:
            blocks.append(current_block)
            current_block = [lines_sorted[i + 1]]
        else:
            current_block.append(lines_sorted[i + 1])
    
    if current_block:
        blocks.append(current_block)
    
    return blocks

def create_splines_from_lines(top_line, bottom_line, image_width):
    """Converteer text lines naar interpolated splines - ROBUST VERSION."""
    
    # Extract points van beide lijnen
    top_points = top_line.base_points()
    bottom_points = bottom_line.base_points()
    
    print(f"      Top line: {len(top_points)} points")
    print(f"      Bottom line: {len(bottom_points)} points")
    
    # Sorteer op X-coordinate en remove duplicates
    top_points = top_points[np.argsort(top_points[:, 0])]
    bottom_points = bottom_points[np.argsort(bottom_points[:, 0])]
    
    # Remove duplicate X values (causes interpolation issues)
    _, unique_top_idx = np.unique(top_points[:, 0], return_index=True)
    _, unique_bottom_idx = np.unique(bottom_points[:, 0], return_index=True)
    top_points = top_points[unique_top_idx]
    bottom_points = bottom_points[unique_bottom_idx]
    
    print(f"      After deduplication: top={len(top_points)}, bottom={len(bottom_points)}")
    
    # Create dense point arrays voor volledige image breedte
    x_dense = np.linspace(0, image_width - 1, image_width)
    
    # Robust interpolation met fallback naar linear fit
    try:
        # Try interpolation first
        if len(top_points) > 1:
            top_interp = interpolate.interp1d(
                top_points[:, 0], top_points[:, 1], 
                kind='linear', bounds_error=False, fill_value='extrapolate'
            )
            top_spline = top_interp(x_dense)
        else:
            top_spline = np.full(image_width, top_points[0, 1])
            
        # Check for invalid values
        if np.any(~np.isfinite(top_spline)):
            print(f"      WARNING: Invalid top spline values, using linear fallback")
            top_spline = linear_fallback(top_points, x_dense)
            
    except Exception as e:
        print(f"      ERROR in top interpolation: {e}, using linear fallback")
        top_spline = linear_fallback(top_points, x_dense)
    
    try:
        # Same for bottom spline
        if len(bottom_points) > 1:
            bottom_interp = interpolate.interp1d(
                bottom_points[:, 0], bottom_points[:, 1],
                kind='linear', bounds_error=False, fill_value='extrapolate'
            )
            bottom_spline = bottom_interp(x_dense)
        else:
            bottom_spline = np.full(image_width, bottom_points[0, 1])
            
        # Check for invalid values
        if np.any(~np.isfinite(bottom_spline)):
            print(f"      WARNING: Invalid bottom spline values, using linear fallback")
            bottom_spline = linear_fallback(bottom_points, x_dense)
            
    except Exception as e:
        print(f"      ERROR in bottom interpolation: {e}, using linear fallback")
        bottom_spline = linear_fallback(bottom_points, x_dense)
    
    print(f"      Spline ranges: top={top_spline.min():.1f}-{top_spline.max():.1f}, bottom={bottom_spline.min():.1f}-{bottom_spline.max():.1f}")
    
    return top_spline, bottom_spline

def linear_fallback(points, x_dense):
    """Fallback linear interpolation voor problematic point sets."""
    if len(points) < 2:
        return np.full(len(x_dense), points[0, 1])
    
    # Simple linear fit
    x_min, x_max = points[:, 0].min(), points[:, 0].max()
    y_min, y_max = points[points[:, 0] == x_min, 1][0], points[points[:, 0] == x_max, 1][0]
    
    # Linear interpolation
    slope = (y_max - y_min) / (x_max - x_min) if x_max != x_min else 0
    spline = y_min + slope * (x_dense - x_min)
    
    return spline

def apply_cylindrical_correction(image, top_spline, bottom_spline, debug_name):
    """Apply GENTLE ScanTailor Deviant-style cylindrical correction."""
    
    h, w = image.shape[:2]
    print(f"      Creating GENTLE remap for {w}x{h} image...")
    
    # Create coordinate arrays
    x_coords, y_coords = np.meshgrid(np.arange(w, dtype=np.float32), 
                                    np.arange(h, dtype=np.float32))
    
    # Ensure splines are correct length and type
    if len(top_spline) != w:
        x_dense = np.linspace(0, len(top_spline)-1, w)
        top_spline = np.interp(x_dense, np.arange(len(top_spline)), top_spline)
        bottom_spline = np.interp(x_dense, np.arange(len(bottom_spline)), bottom_spline)
    
    top_spline = top_spline.astype(np.float32)
    bottom_spline = bottom_spline.astype(np.float32)
    
    # Calculate spline curvature (second derivative)
    top_curvature = calculate_curvature(top_spline)
    bottom_curvature = calculate_curvature(bottom_spline)
    
    print(f"      Top curvature range: {top_curvature.min():.6f} to {top_curvature.max():.6f}")
    print(f"      Bottom curvature range: {bottom_curvature.min():.6f} to {bottom_curvature.max():.6f}")
    
    # Initialize output coordinates
    map_x = x_coords.copy()
    map_y = y_coords.copy()
    
    # MUCH GENTLER approach - test different strengths
    strength_options = [0.5, 1.0, 2.0, 5.0]  # Much smaller values
    selected_strength = strength_options[0]  # Start with weakest
    
    print(f"      Using gentle curvature strength: {selected_strength}")
    
    # For each column, apply GENTLE curvature-based correction
    correction_count = 0
    for x in range(0, w, 10):  # Sample every 10th column for speed
        top_y = top_spline[x]
        bottom_y = bottom_spline[x] 
        text_height = bottom_y - top_y
        
        if text_height <= 1:
            continue
            
        # Get curvature at this X position
        top_curve = top_curvature[x]
        bottom_curve = bottom_curvature[x]
        
        # Find pixels in this column that are within text region
        col_mask = (y_coords[:, x] >= top_y) & (y_coords[:, x] <= bottom_y)
        col_y = y_coords[col_mask, x]
        
        if len(col_y) == 0:
            continue
            
        # Relative position within text (0=top, 1=bottom)
        t = (col_y - top_y) / text_height
        
        # GENTLE CORRECTION - much smaller values
        curve_at_t = top_curve * (1 - t) + bottom_curve * t
        
        # Much smaller curvature strength
        curvature_strength = selected_strength
        
        # Y correction: gentle counter to curvature
        y_correction = -curve_at_t * curvature_strength * np.sin(t * np.pi)
        
        # Apply gentle corrections
        corrected_y = col_y + y_correction
        
        # Clamp to valid coordinates
        corrected_y = np.clip(corrected_y, 0, h - 1)
        
        # Update mapping for this column and nearby columns
        for x_offset in range(-5, 6):  # Apply to nearby columns
            x_target = x + x_offset
            if 0 <= x_target < w:
                map_y[col_mask, x_target] = corrected_y
        
        correction_count += len(col_y)
    
    print(f"      Applied gentle corrections to {correction_count} pixels")
    
    # Apply remap
    corrected = cv2.remap(image, map_x, map_y, cv2.INTER_LINEAR)
    
    return corrected

def calculate_curvature(spline):
    """Calculate curvature (second derivative) of spline."""
    
    # Smooth the spline first to reduce noise
    from scipy import ndimage
    smoothed = ndimage.gaussian_filter1d(spline, sigma=2.0)
    
    # Calculate first and second derivatives
    dy_dx = np.gradient(smoothed)
    d2y_dx2 = np.gradient(dy_dx)
    
    # Curvature formula: k = |d2y/dx2| / (1 + (dy/dx)^2)^(3/2)
    # Simplified version for small slopes: k ≈ |d2y/dx2|
    curvature = d2y_dx2
    
    return curvature

def visualize_splines(image, top_spline, bottom_spline, all_lines):
    """Visualiseer splines over originele image."""
    
    vis = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if len(image.shape) == 2 else image.copy()
    
    # Draw original detected lines in blue
    for line in all_lines:
        points = line.base_points().astype(int)
        for i in range(len(points) - 1):
            cv2.line(vis, tuple(points[i]), tuple(points[i + 1]), (255, 0, 0), 2)
    
    # Draw splines in green
    w = image.shape[1]
    for x in range(w - 1):
        # Top spline
        pt1 = (x, int(top_spline[x]))
        pt2 = (x + 1, int(top_spline[x + 1]))
        cv2.line(vis, pt1, pt2, (0, 255, 0), 3)
        
        # Bottom spline  
        pt1 = (x, int(bottom_spline[x]))
        pt2 = (x + 1, int(bottom_spline[x + 1]))
        cv2.line(vis, pt1, pt2, (0, 255, 0), 3)
    
    cv2.imwrite('dewarp/spline_visualization.png', vis)
    print("   📊 Spline visualization saved: spline_visualization.png")

def identify_textblocks_smart(lines_sorted, AH):
    """Slimme tekstblok identificatie voor inhoudsopgave met variabele inspringing."""
    
    if len(lines_sorted) < 3:
        return [lines_sorted]
    
    # Analyseer X-posities van lijnen (inspringing)
    line_info = []
    for line in lines_sorted:
        points = line.base_points()
        y_avg = points[:, 1].mean()
        x_left = points[:, 0].min()  # Linkerkant van lijn
        x_right = points[:, 0].max()  # Rechterkant van lijn
        line_info.append({
            'line': line,
            'y': y_avg,
            'x_left': x_left,
            'x_right': x_right,
            'width': x_right - x_left
        })
    
    # Detecteer hoofdgroepen op basis van Y-gaps EN X-alignment
    y_positions = [info['y'] for info in line_info]
    gaps = np.diff(y_positions)
    median_gap = np.median(gaps)
    large_gap_threshold = 1.8 * median_gap  # Wat minder streng
    
    # Detecteer X-alignment patterns
    x_lefts = [info['x_left'] for info in line_info]
    x_left_clusters = detect_alignment_clusters(x_lefts, threshold=50)  # 50 pixel tolerance
    
    print(f"   Y-gap analysis: median={median_gap:.1f}, threshold={large_gap_threshold:.1f}")
    print(f"   X-alignment clusters: {len(x_left_clusters)} groups")
    
    # ENHANCED: Show detailed block analysis
    print(f"\n   📋 DETAILED TEXTBLOCK ANALYSIS:")
    
    # Combineer Y-gaps en X-alignment voor slimme blok detectie
    blocks = []
    current_block = [line_info[0]]
    
    for i, gap in enumerate(gaps):
        current_info = line_info[i + 1]
        prev_info = line_info[i]
        
        # Check of er een blok break moet komen
        y_break = gap > large_gap_threshold
        x_break = abs(current_info['x_left'] - prev_info['x_left']) > 100  # Grote X-shift
        
        print(f"      Line {i+1}→{i+2}: Y-gap={gap:.1f}, X-shift={abs(current_info['x_left'] - prev_info['x_left']):.1f}")
        
        if y_break:
            # Definitief nieuwe blok door grote Y-gap
            print(f"        → NEW BLOCK (Y-gap: {gap:.1f} > {large_gap_threshold:.1f})")
            blocks.append([info['line'] for info in current_block])
            current_block = [current_info]
        elif x_break and len(current_block) > 2:
            # Nieuwe blok door X-alignment change (maar alleen als huidige blok groot genoeg)
            print(f"        → NEW BLOCK (X-shift: {abs(current_info['x_left'] - prev_info['x_left']):.1f} > 100)")
            blocks.append([info['line'] for info in current_block])
            current_block = [current_info]
        else:
            # Continue huidige blok
            print(f"        → Continue current block")
            current_block.append(current_info)
    
    if current_block:
        blocks.append([info['line'] for info in current_block])
    
    # ENHANCED: Show final block summary with curvature analysis
    print(f"\n   🎯 FINAL TEXTBLOCK SUMMARY:")
    for i, block in enumerate(blocks):
        y_positions = [line.base_points()[:, 1].mean() for line in block]
        y_min, y_max = min(y_positions), max(y_positions)
        
        # Analyze curvature of first line in each block
        if len(block) > 0:
            first_line = block[0]
            points = first_line.base_points()
            if len(points) >= 3:
                # Quick curvature estimate
                y_coords = points[:, 1]
                curvature_estimate = np.std(y_coords)
                
                print(f"     Block {i+1}: {len(block)} lines, Y {y_min:.0f}-{y_max:.0f}, curvature≈{curvature_estimate:.1f}")
                
                if curvature_estimate > 5.0:  # Significant curvature
                    print(f"               ⚠️  HIGH CURVATURE - mogelijk 'deuk' gebied!")
            else:
                print(f"     Block {i+1}: {len(block)} lines, Y {y_min:.0f}-{y_max:.0f}")
    
    return blocks

def detect_alignment_clusters(positions, threshold=50):
    """Detecteer alignment clusters in X-posities."""
    positions = np.array(positions)
    clusters = []
    
    for pos in positions:
        # Zoek bestaande cluster
        assigned = False
        for cluster in clusters:
            if abs(pos - np.mean(cluster)) < threshold:
                cluster.append(pos)
                assigned = True
                break
        
        if not assigned:
            clusters.append([pos])
    
    return clusters

def visualize_splines_smart(image, top_spline, bottom_spline, all_lines, main_block):
    """Visualiseer splines met highlight van selected block - SAFE VERSION."""
    
    vis = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if len(image.shape) == 2 else image.copy()
    
    # Draw all lines in light blue
    for line in all_lines:
        points = line.base_points().astype(int)
        for i in range(len(points) - 1):
            cv2.line(vis, tuple(points[i]), tuple(points[i + 1]), (255, 200, 200), 1)
    
    # Draw selected main block in dark blue
    for line in main_block:
        points = line.base_points().astype(int)
        for i in range(len(points) - 1):
            cv2.line(vis, tuple(points[i]), tuple(points[i + 1]), (255, 0, 0), 3)
    
    # Draw splines in green - SAFE VERSION
    w = image.shape[1]
    
    # Ensure splines are finite and convert to valid integers
    top_spline_safe = np.clip(np.nan_to_num(top_spline, nan=0, posinf=0, neginf=0), 0, image.shape[0] - 1)
    bottom_spline_safe = np.clip(np.nan_to_num(bottom_spline, nan=0, posinf=0, neginf=0), 0, image.shape[0] - 1)
    
    for x in range(w - 1):
        try:
            # Top spline (thick) - safe integer conversion
            y1, y2 = int(top_spline_safe[x]), int(top_spline_safe[x + 1])
            cv2.line(vis, (x, y1), (x + 1, y2), (0, 255, 0), 4)
            
            # Bottom spline (thick) - safe integer conversion
            y1, y2 = int(bottom_spline_safe[x]), int(bottom_spline_safe[x + 1])
            cv2.line(vis, (x, y1), (x + 1, y2), (0, 255, 0), 4)
            
        except (ValueError, OverflowError) as e:
            # Skip problematic points
            continue
    
    cv2.imwrite('dewarp/spline_smart_visualization.png', vis)
    print("   📊 Smart visualization saved: spline_smart_visualization.png")

def create_splines_with_boundaries(top_line, bottom_line, image_width, image_height):
    """Create splines met page boundary constraints."""
    
    # Extract and clean points
    top_points = top_line.base_points()
    bottom_points = bottom_line.base_points()
    
    # Remove duplicates
    _, unique_top_idx = np.unique(top_points[:, 0], return_index=True)
    _, unique_bottom_idx = np.unique(bottom_points[:, 0], return_index=True)
    top_points = top_points[unique_top_idx]
    bottom_points = bottom_points[unique_bottom_idx]
    
    # Sort by X
    top_points = top_points[np.argsort(top_points[:, 0])]
    bottom_points = bottom_points[np.argsort(bottom_points[:, 0])]
    
    print(f"      Creating boundary-constrained splines...")
    print(f"      Top points X-range: {top_points[:, 0].min():.0f} - {top_points[:, 0].max():.0f}")
    print(f"      Bottom points X-range: {bottom_points[:, 0].min():.0f} - {bottom_points[:, 0].max():.0f}")
    
    # Extend splines to full page width using page boundaries
    x_dense = np.linspace(0, image_width - 1, image_width)
    
    # For areas outside detected text, use page boundaries (top=0, bottom=height)
    page_margin = 50  # Pixels from edge
    
    # Top spline: extend to page edges
    if top_points[:, 0].min() > page_margin:
        # Add left boundary point
        left_y = top_points[0, 1]  # Use first detected Y
        top_points = np.vstack([[0, left_y], top_points])
    
    if top_points[:, 0].max() < image_width - page_margin:
        # Add right boundary point  
        right_y = top_points[-1, 1]  # Use last detected Y
        top_points = np.vstack([top_points, [image_width - 1, right_y]])
    
    # Bottom spline: extend to page edges
    if bottom_points[:, 0].min() > page_margin:
        # Add left boundary point
        left_y = bottom_points[0, 1]
        bottom_points = np.vstack([[0, left_y], bottom_points])
    
    if bottom_points[:, 0].max() < image_width - page_margin:
        # Add right boundary point
        right_y = bottom_points[-1, 1]
        bottom_points = np.vstack([bottom_points, [image_width - 1, right_y]])
    
    # Safe interpolation
    try:
        top_interp = interpolate.interp1d(
            top_points[:, 0], top_points[:, 1], 
            kind='linear', bounds_error=False, fill_value='extrapolate'
        )
        top_spline = top_interp(x_dense)
        
        bottom_interp = interpolate.interp1d(
            bottom_points[:, 0], bottom_points[:, 1],
            kind='linear', bounds_error=False, fill_value='extrapolate' 
        )
        bottom_spline = bottom_interp(x_dense)
        
    except Exception as e:
        print(f"      Interpolation failed: {e}, using linear fallback")
        top_spline = linear_fallback(top_points, x_dense)
        bottom_spline = linear_fallback(bottom_points, x_dense)
    
    # Clamp to valid image coordinates
    top_spline = np.clip(top_spline, 0, image_height - 1)
    bottom_spline = np.clip(bottom_spline, 0, image_height - 1)
    
    print(f"      Final spline ranges: top={top_spline.min():.1f}-{top_spline.max():.1f}, bottom={bottom_spline.min():.1f}-{bottom_spline.max():.1f}")
    
    return top_spline, bottom_spline

def visualize_splines_enhanced(image, top_spline, bottom_spline, all_lines, selected_lines, config_name):
    """Enhanced visualization met config name."""
    
    vis = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if len(image.shape) == 2 else image.copy()
    
    # Draw all lines in light gray
    for line in all_lines:
        points = line.base_points().astype(int)
        for i in range(len(points) - 1):
            cv2.line(vis, tuple(points[i]), tuple(points[i + 1]), (200, 200, 200), 1)
    
    # Draw selected lines in bright blue
    for line in selected_lines:
        points = line.base_points().astype(int)
        for i in range(len(points) - 1):
            cv2.line(vis, tuple(points[i]), tuple(points[i + 1]), (255, 100, 0), 3)
    
    # Draw enhanced splines
    w = image.shape[1]
    top_spline_safe = np.clip(np.nan_to_num(top_spline), 0, image.shape[0] - 1)
    bottom_spline_safe = np.clip(np.nan_to_num(bottom_spline), 0, image.shape[0] - 1)
    
    for x in range(w - 1):
        try:
            # Top spline in bright green
            cv2.line(vis, (x, int(top_spline_safe[x])), (x + 1, int(top_spline_safe[x + 1])), (0, 255, 0), 5)
            # Bottom spline in bright green
            cv2.line(vis, (x, int(bottom_spline_safe[x])), (x + 1, int(bottom_spline_safe[x + 1])), (0, 255, 0), 5)
        except:
            continue
    
    # Add text label
    cv2.putText(vis, config_name.upper(), (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 3)
    
    cv2.imwrite(f'dewarp/spline_viz_{config_name}.png', vis)
    print(f"     📊 Visualization: spline_viz_{config_name}.png")

def analyze_line_curvature(line, config_name):
    """Analyze the curvature of a detected text line."""
    
    points = line.base_points()
    if len(points) < 5:
        print(f"     Line curvature: insufficient points ({len(points)})")
        return
        
    # Sort by X and calculate Y curvature
    sorted_points = points[np.argsort(points[:, 0])]
    x_coords = sorted_points[:, 0]
    y_coords = sorted_points[:, 1]
    
    # Fit spline and calculate curvature
    from scipy.interpolate import UnivariateSpline
    
    try:
        # Fit spline through points
        spline_fit = UnivariateSpline(x_coords, y_coords, s=len(points))  # Smoothing
        
        # Evaluate at dense points
        x_dense = np.linspace(x_coords.min(), x_coords.max(), 100)
        y_dense = spline_fit(x_dense)
        
        # Calculate curvature
        curvature = calculate_curvature(y_dense)
        max_curvature = np.abs(curvature).max()
        
        print(f"     Line curvature analysis:")
        print(f"       Max curvature: {max_curvature:.6f}")
        print(f"       Curvature std: {np.std(curvature):.6f}")
        
        # Detect "deuk" pattern (negative curvature in middle)
        mid_idx = len(curvature) // 2
        mid_curvature = curvature[mid_idx-10:mid_idx+10].mean()
        
        if mid_curvature < -0.001:  # Significant downward curve
            print(f"       🔍 DEUK DETECTED: middle curvature = {mid_curvature:.6f}")
        elif mid_curvature > 0.001:  # Upward curve
            print(f"       📈 Upward curve: middle curvature = {mid_curvature:.6f}")
        else:
            print(f"       ➡️  Relatively straight: middle curvature = {mid_curvature:.6f}")
            
    except Exception as e:
        print(f"     Line curvature analysis failed: {e}")

def apply_gentle_correction(image, top_spline, bottom_spline, strength):
    """Apply more aggressive but controlled correction with specified strength."""
    
    h, w = image.shape[:2]
    print(f"      Applying stronger correction (strength={strength}) to {w}x{h} image...")
    
    # Calculate actual "deuk" depth from splines
    spline_variation = np.abs(top_spline - np.mean(top_spline)).max()
    print(f"      Detected spline variation: {spline_variation:.1f} pixels")
    
    # Dynamic correction based on actual curvature
    max_correction = min(spline_variation * 0.8, 50.0)  # Max 80% of variation or 50 pixels
    print(f"      Max correction will be: {max_correction:.1f} pixels")
    
    # Simple Y-correction with realistic values
    x_coords, y_coords = np.meshgrid(np.arange(w, dtype=np.float32), 
                                    np.arange(h, dtype=np.float32))
    
    map_x = x_coords.copy()
    map_y = y_coords.copy()
    
    # Apply realistic Y-correction based on spline deviation
    for x in range(w):
        top_y = top_spline[x] if x < len(top_spline) else top_spline[-1]
        bottom_y = bottom_spline[x] if x < len(bottom_spline) else bottom_spline[-1]
        
        text_height = bottom_y - top_y
        if text_height <= 1:
            continue
            
        # Find pixels in text region
        col_mask = (y_coords[:, x] >= top_y) & (y_coords[:, x] <= bottom_y)
        col_y = y_coords[col_mask, x]
        
        if len(col_y) == 0:
            continue
            
        # Calculate how much this spline deviates from straight line
        straight_top = np.interp(x, [0, w-1], [top_spline[0], top_spline[-1]])
        spline_deviation = top_y - straight_top
        
        # Relative position within text (0=top, 1=bottom)
        t = (col_y - top_y) / text_height
        
        # REALISTIC Y adjustment based on actual spline curvature
        # Use sine wave to distribute correction smoothly across text height
        correction_factor = strength * np.sin(t * np.pi)
        y_adjustment = spline_deviation * correction_factor
        
        # Clamp to reasonable bounds
        y_adjustment = np.clip(y_adjustment, -max_correction, max_correction)
        
        corrected_y = col_y - y_adjustment
        corrected_y = np.clip(corrected_y, 0, h - 1)
        
        map_y[col_mask, x] = corrected_y
    
    # Apply remap
    corrected = cv2.remap(image, map_x, map_y, cv2.INTER_LINEAR)
    return corrected

def apply_cylindrical_correction(image, top_spline, bottom_spline, debug_name):
    """Apply GENTLE ScanTailor Deviant-style cylindrical correction."""
    
    h, w = image.shape[:2]
    print(f"      Creating GENTLE remap for {w}x{h} image...")
    
    # Create coordinate arrays
    x_coords, y_coords = np.meshgrid(np.arange(w, dtype=np.float32), 
                                    np.arange(h, dtype=np.float32))
    
    # Ensure splines are correct length and type
    if len(top_spline) != w:
        x_dense = np.linspace(0, len(top_spline)-1, w)
        top_spline = np.interp(x_dense, np.arange(len(top_spline)), top_spline)
        bottom_spline = np.interp(x_dense, np.arange(len(bottom_spline)), bottom_spline)
    
    top_spline = top_spline.astype(np.float32)
    bottom_spline = bottom_spline.astype(np.float32)
    
    # Calculate spline curvature (second derivative)
    top_curvature = calculate_curvature(top_spline)
    bottom_curvature = calculate_curvature(bottom_spline)
    
    print(f"      Top curvature range: {top_curvature.min():.6f} to {top_curvature.max():.6f}")
    print(f"      Bottom curvature range: {bottom_curvature.min():.6f} to {bottom_curvature.max():.6f}")
    
    # Initialize output coordinates
    map_x = x_coords.copy()
    map_y = y_coords.copy()
    
    # MUCH GENTLER approach - test different strengths
    strength_options = [0.5, 1.0, 2.0, 5.0]  # Much smaller values
    selected_strength = strength_options[0]  # Start with weakest
    
    print(f"      Using gentle curvature strength: {selected_strength}")
    
    # For each column, apply GENTLE curvature-based correction
    correction_count = 0
    for x in range(0, w, 10):  # Sample every 10th column for speed
        top_y = top_spline[x]
        bottom_y = bottom_spline[x] 
        text_height = bottom_y - top_y
        
        if text_height <= 1:
            continue
            
        # Get curvature at this X position
        top_curve = top_curvature[x]
        bottom_curve = bottom_curvature[x]
        
        # Find pixels in this column that are within text region
        col_mask = (y_coords[:, x] >= top_y) & (y_coords[:, x] <= bottom_y)
        col_y = y_coords[col_mask, x]
        
        if len(col_y) == 0:
            continue
            
        # Relative position within text (0=top, 1=bottom)
        t = (col_y - top_y) / text_height
        
        # GENTLE CORRECTION - much smaller values
        curve_at_t = top_curve * (1 - t) + bottom_curve * t
        
        # Much smaller curvature strength
        curvature_strength = selected_strength
        
        # Y correction: gentle counter to curvature
        y_correction = -curve_at_t * curvature_strength * np.sin(t * np.pi)
        
        # Apply gentle corrections
        corrected_y = col_y + y_correction
        
        # Clamp to valid coordinates
        corrected_y = np.clip(corrected_y, 0, h - 1)
        
        # Update mapping for this column and nearby columns
        for x_offset in range(-5, 6):  # Apply to nearby columns
            x_target = x + x_offset
            if 0 <= x_target < w:
                map_y[col_mask, x_target] = corrected_y
        
        correction_count += len(col_y)
    
    print(f"      Applied gentle corrections to {correction_count} pixels")
    
    # Apply remap
    corrected = cv2.remap(image, map_x, map_y, cv2.INTER_LINEAR)
    
    return corrected

def calculate_curvature(spline):
    """Calculate curvature (second derivative) of spline."""
    
    # Smooth the spline first to reduce noise
    from scipy import ndimage
    smoothed = ndimage.gaussian_filter1d(spline, sigma=2.0)
    
    # Calculate first and second derivatives
    dy_dx = np.gradient(smoothed)
    d2y_dx2 = np.gradient(dy_dx)
    
    # Curvature formula: k = |d2y/dx2| / (1 + (dy/dx)^2)^(3/2)
    # Simplified version for small slopes: k ≈ |d2y/dx2|
    curvature = d2y_dx2
    
    return curvature

def visualize_splines(image, top_spline, bottom_spline, all_lines):
    """Visualiseer splines over originele image."""
    
    vis = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if len(image.shape) == 2 else image.copy()
    
    # Draw original detected lines in blue
    for line in all_lines:
        points = line.base_points().astype(int)
        for i in range(len(points) - 1):
            cv2.line(vis, tuple(points[i]), tuple(points[i + 1]), (255, 0, 0), 2)
    
    # Draw splines in green
    w = image.shape[1]
    for x in range(w - 1):
        # Top spline
        pt1 = (x, int(top_spline[x]))
        pt2 = (x + 1, int(top_spline[x + 1]))
        cv2.line(vis, pt1, pt2, (0, 255, 0), 3)
        
        # Bottom spline  
        pt1 = (x, int(bottom_spline[x]))
        pt2 = (x + 1, int(bottom_spline[x + 1]))
        cv2.line(vis, pt1, pt2, (0, 255, 0), 3)
    
    cv2.imwrite('dewarp/spline_visualization.png', vis)
    print("   📊 Spline visualization saved: spline_visualization.png")

def identify_textblocks_smart(lines_sorted, AH):
    """Slimme tekstblok identificatie voor inhoudsopgave met variabele inspringing."""
    
    if len(lines_sorted) < 3:
        return [lines_sorted]
    
    # Analyseer X-posities van lijnen (inspringing)
    line_info = []
    for line in lines_sorted:
        points = line.base_points()
        y_avg = points[:, 1].mean()
        x_left = points[:, 0].min()  # Linkerkant van lijn
        x_right = points[:, 0].max()  # Rechterkant van lijn
        line_info.append({
            'line': line,
            'y': y_avg,
            'x_left': x_left,
            'x_right': x_right,
            'width': x_right - x_left
        })
    
    # Detecteer hoofdgroepen op basis van Y-gaps EN X-alignment
    y_positions = [info['y'] for info in line_info]
    gaps = np.diff(y_positions)
    median_gap = np.median(gaps)
    large_gap_threshold = 1.8 * median_gap  # Wat minder streng
    
    # Detecteer X-alignment patterns
    x_lefts = [info['x_left'] for info in line_info]
    x_left_clusters = detect_alignment_clusters(x_lefts, threshold=50)  # 50 pixel tolerance
    
    print(f"   Y-gap analysis: median={median_gap:.1f}, threshold={large_gap_threshold:.1f}")
    print(f"   X-alignment clusters: {len(x_left_clusters)} groups")
    
    # ENHANCED: Show detailed block analysis
    print(f"\n   📋 DETAILED TEXTBLOCK ANALYSIS:")
    
    # Combineer Y-gaps en X-alignment voor slimme blok detectie
    blocks = []
    current_block = [line_info[0]]
    
    for i, gap in enumerate(gaps):
        current_info = line_info[i + 1]
        prev_info = line_info[i]
        
        # Check of er een blok break moet komen
        y_break = gap > large_gap_threshold
        x_break = abs(current_info['x_left'] - prev_info['x_left']) > 100  # Grote X-shift
        
        print(f"      Line {i+1}→{i+2}: Y-gap={gap:.1f}, X-shift={abs(current_info['x_left'] - prev_info['x_left']):.1f}")
        
        if y_break:
            # Definitief nieuwe blok door grote Y-gap
            print(f"        → NEW BLOCK (Y-gap: {gap:.1f} > {large_gap_threshold:.1f})")
            blocks.append([info['line'] for info in current_block])
            current_block = [current_info]
        elif x_break and len(current_block) > 2:
            # Nieuwe blok door X-alignment change (maar alleen als huidige blok groot genoeg)
            print(f"        → NEW BLOCK (X-shift: {abs(current_info['x_left'] - prev_info['x_left']):.1f} > 100)")
            blocks.append([info['line'] for info in current_block])
            current_block = [current_info]
        else:
            # Continue huidige blok
            print(f"        → Continue current block")
            current_block.append(current_info)
    
    if current_block:
        blocks.append([info['line'] for info in current_block])
    
    # ENHANCED: Show final block summary with curvature analysis
    print(f"\n   🎯 FINAL TEXTBLOCK SUMMARY:")
    for i, block in enumerate(blocks):
        y_positions = [line.base_points()[:, 1].mean() for line in block]
        y_min, y_max = min(y_positions), max(y_positions)
        
        # Analyze curvature of first line in each block
        if len(block) > 0:
            first_line = block[0]
            points = first_line.base_points()
            if len(points) >= 3:
                # Quick curvature estimate
                y_coords = points[:, 1]
                curvature_estimate = np.std(y_coords)
                
                print(f"     Block {i+1}: {len(block)} lines, Y {y_min:.0f}-{y_max:.0f}, curvature≈{curvature_estimate:.1f}")
                
                if curvature_estimate > 5.0:  # Significant curvature
                    print(f"               ⚠️  HIGH CURVATURE - mogelijk 'deuk' gebied!")
            else:
                print(f"     Block {i+1}: {len(block)} lines, Y {y_min:.0f}-{y_max:.0f}")
    
    return blocks

def detect_alignment_clusters(positions, threshold=50):
    """Detecteer alignment clusters in X-posities."""
    positions = np.array(positions)
    clusters = []
    
    for pos in positions:
        # Zoek bestaande cluster
        assigned = False
        for cluster in clusters:
            if abs(pos - np.mean(cluster)) < threshold:
                cluster.append(pos)
                assigned = True
                break
        
        if not assigned:
            clusters.append([pos])
    
    return clusters

def visualize_splines_smart(image, top_spline, bottom_spline, all_lines, main_block):
    """Visualiseer splines met highlight van selected block - SAFE VERSION."""
    
    vis = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if len(image.shape) == 2 else image.copy()
    
    # Draw all lines in light blue
    for line in all_lines:
        points = line.base_points().astype(int)
        for i in range(len(points) - 1):
            cv2.line(vis, tuple(points[i]), tuple(points[i + 1]), (255, 200, 200), 1)
    
    # Draw selected main block in dark blue
    for line in main_block:
        points = line.base_points().astype(int)
        for i in range(len(points) - 1):
            cv2.line(vis, tuple(points[i]), tuple(points[i + 1]), (255, 0, 0), 3)
    
    # Draw splines in green - SAFE VERSION
    w = image.shape[1]
    
    # Ensure splines are finite and convert to valid integers
    top_spline_safe = np.clip(np.nan_to_num(top_spline, nan=0, posinf=0, neginf=0), 0, image.shape[0] - 1)
    bottom_spline_safe = np.clip(np.nan_to_num(bottom_spline, nan=0, posinf=0, neginf=0), 0, image.shape[0] - 1)
    
    for x in range(w - 1):
        try:
            # Top spline (thick) - safe integer conversion
            y1, y2 = int(top_spline_safe[x]), int(top_spline_safe[x + 1])
            cv2.line(vis, (x, y1), (x + 1, y2), (0, 255, 0), 4)
            
            # Bottom spline (thick) - safe integer conversion
            y1, y2 = int(bottom_spline_safe[x]), int(bottom_spline_safe[x + 1])
            cv2.line(vis, (x, y1), (x + 1, y2), (0, 255, 0), 4)
            
        except (ValueError, OverflowError) as e:
            # Skip problematic points
            continue
    
    cv2.imwrite('dewarp/spline_smart_visualization.png', vis)
    print("   📊 Smart visualization saved: spline_smart_visualization.png")

def create_splines_with_boundaries(top_line, bottom_line, image_width, image_height):
    """Create splines met page boundary constraints."""
    
    # Extract and clean points
    top_points = top_line.base_points()
    bottom_points = bottom_line.base_points()
    
    # Remove duplicates
    _, unique_top_idx = np.unique(top_points[:, 0], return_index=True)
    _, unique_bottom_idx = np.unique(bottom_points[:, 0], return_index=True)
    top_points = top_points[unique_top_idx]
    bottom_points = bottom_points[unique_bottom_idx]
    
    # Sort by X
    top_points = top_points[np.argsort(top_points[:, 0])]
    bottom_points = bottom_points[np.argsort(bottom_points[:, 0])]
    
    print(f"      Creating boundary-constrained splines...")
    print(f"      Top points X-range: {top_points[:, 0].min():.0f} - {top_points[:, 0].max():.0f}")
    print(f"      Bottom points X-range: {bottom_points[:, 0].min():.0f} - {bottom_points[:, 0].max():.0f}")
    
    # Extend splines to full page width using page boundaries
    x_dense = np.linspace(0, image_width - 1, image_width)
    
    # For areas outside detected text, use page boundaries (top=0, bottom=height)
    page_margin = 50  # Pixels from edge
    
    # Top spline: extend to page edges
    if top_points[:, 0].min() > page_margin:
        # Add left boundary point
        left_y = top_points[0, 1]  # Use first detected Y
        top_points = np.vstack([[0, left_y], top_points])
    
    if top_points[:, 0].max() < image_width - page_margin:
        # Add right boundary point  
        right_y = top_points[-1, 1]  # Use last detected Y
        top_points = np.vstack([top_points, [image_width - 1, right_y]])
    
    # Bottom spline: extend to page edges
    if bottom_points[:, 0].min() > page_margin:
        # Add left boundary point
        left_y = bottom_points[0, 1]
        bottom_points = np.vstack([[0, left_y], bottom_points])
    
    if bottom_points[:, 0].max() < image_width - page_margin:
        # Add right boundary point
        right_y = bottom_points[-1, 1]
        bottom_points = np.vstack([bottom_points, [image_width - 1, right_y]])
    
    # Safe interpolation
    try:
        top_interp = interpolate.interp1d(
            top_points[:, 0], top_points[:, 1], 
            kind='linear', bounds_error=False, fill_value='extrapolate'
        )
        top_spline = top_interp(x_dense)
        
        bottom_interp = interpolate.interp1d(
            bottom_points[:, 0], bottom_points[:, 1],
            kind='linear', bounds_error=False, fill_value='extrapolate' 
        )
        bottom_spline = bottom_interp(x_dense)
        
    except Exception as e:
        print(f"      Interpolation failed: {e}, using linear fallback")
        top_spline = linear_fallback(top_points, x_dense)
        bottom_spline = linear_fallback(bottom_points, x_dense)
    
    # Clamp to valid image coordinates
    top_spline = np.clip(top_spline, 0, image_height - 1)
    bottom_spline = np.clip(bottom_spline, 0, image_height - 1)
    
    print(f"      Final spline ranges: top={top_spline.min():.1f}-{top_spline.max():.1f}, bottom={bottom_spline.min():.1f}-{bottom_spline.max():.1f}")
    
    return top_spline, bottom_spline

def visualize_splines_enhanced(image, top_spline, bottom_spline, all_lines, selected_lines, config_name):
    """Enhanced visualization met config name."""
    
    vis = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if len(image.shape) == 2 else image.copy()
    
    # Draw all lines in light gray
    for line in all_lines:
        points = line.base_points().astype(int)
        for i in range(len(points) - 1):
            cv2.line(vis, tuple(points[i]), tuple(points[i + 1]), (200, 200, 200), 1)
    
    # Draw selected lines in bright blue
    for line in selected_lines:
        points = line.base_points().astype(int)
        for i in range(len(points) - 1):
            cv2.line(vis, tuple(points[i]), tuple(points[i + 1]), (255, 100, 0), 3)
    
    # Draw enhanced splines
    w = image.shape[1]
    top_spline_safe = np.clip(np.nan_to_num(top_spline), 0, image.shape[0] - 1)
    bottom_spline_safe = np.clip(np.nan_to_num(bottom_spline), 0, image.shape[0] - 1)
    
    for x in range(w - 1):
        try:
            # Top spline in bright green
            cv2.line(vis, (x, int(top_spline_safe[x])), (x + 1, int(top_spline_safe[x + 1])), (0, 255, 0), 5)
            # Bottom spline in bright green
            cv2.line(vis, (x, int(bottom_spline_safe[x])), (x + 1, int(bottom_spline_safe[x + 1])), (0, 255, 0), 5)
        except:
            continue
    
    # Add text label
    cv2.putText(vis, config_name.upper(), (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 3)
    
    cv2.imwrite(f'dewarp/spline_viz_{config_name}.png', vis)
    print(f"     📊 Visualization: spline_viz_{config_name}.png")

def analyze_line_curvature(line, config_name):
    """Analyze the curvature of a detected text line."""
    
    points = line.base_points()
    if len(points) < 5:
        print(f"     Line curvature: insufficient points ({len(points)})")
        return
        
    # Sort by X and calculate Y curvature
    sorted_points = points[np.argsort(points[:, 0])]
    x_coords = sorted_points[:, 0]
    y_coords = sorted_points[:, 1]
    
    # Fit spline and calculate curvature
    from scipy.interpolate import UnivariateSpline
    
    try:
        # Fit spline through points
        spline_fit = UnivariateSpline(x_coords, y_coords, s=len(points))  # Smoothing
        
        # Evaluate at dense points
        x_dense = np.linspace(x_coords.min(), x_coords.max(), 100)
        y_dense = spline_fit(x_dense)
        
        # Calculate curvature
        curvature = calculate_curvature(y_dense)
        max_curvature = np.abs(curvature).max()
        
        print(f"     Line curvature analysis:")
        print(f"       Max curvature: {max_curvature:.6f}")
        print(f"       Curvature std: {np.std(curvature):.6f}")
        
        # Detect "deuk" pattern (negative curvature in middle)
        mid_idx = len(curvature) // 2
        mid_curvature = curvature[mid_idx-10:mid_idx+10].mean()
        
        if mid_curvature < -0.001:  # Significant downward curve
            print(f"       🔍 DEUK DETECTED: middle curvature = {mid_curvature:.6f}")
        elif mid_curvature > 0.001:  # Upward curve
            print(f"       📈 Upward curve: middle curvature = {mid_curvature:.6f}")
        else:
            print(f"       ➡️  Relatively straight: middle curvature = {mid_curvature:.6f}")
            
    except Exception as e:
        print(f"     Line curvature analysis failed: {e}")

def apply_gentle_correction(image, top_spline, bottom_spline, strength):
    """Apply more aggressive but controlled correction with specified strength."""
    
    h, w = image.shape[:2]
    print(f"      Applying stronger correction (strength={strength}) to {w}x{h} image...")
    
    # Calculate actual "deuk" depth from splines
    spline_variation = np.abs(top_spline - np.mean(top_spline)).max()
    print(f"      Detected spline variation: {spline_variation:.1f} pixels")
    
    # Dynamic correction based on actual curvature
    max_correction = min(spline_variation * 0.8, 50.0)  # Max 80% of variation or 50 pixels
    print(f"      Max correction will be: {max_correction:.1f} pixels")
    
    # Simple Y-correction with realistic values
    x_coords, y_coords = np.meshgrid(np.arange(w, dtype=np.float32), 
                                    np.arange(h, dtype=np.float32))
    
    map_x = x_coords.copy()
    map_y = y_coords.copy()
    
    # Apply realistic Y-correction based on spline deviation
    for x in range(w):
        top_y = top_spline[x] if x < len(top_spline) else top_spline[-1]
        bottom_y = bottom_spline[x] if x < len(bottom_spline) else bottom_spline[-1]
        
        text_height = bottom_y - top_y
        if text_height <= 1:
            continue
            
        # Find pixels in text region
        col_mask = (y_coords[:, x] >= top_y) & (y_coords[:, x] <= bottom_y)
        col_y = y_coords[col_mask, x]
        
        if len(col_y) == 0:
            continue
            
        # Calculate how much this spline deviates from straight line
        straight_top = np.interp(x, [0, w-1], [top_spline[0], top_spline[-1]])
        spline_deviation = top_y - straight_top
        
        # Relative position within text (0=top, 1=bottom)
        t = (col_y - top_y) / text_height
        
        # REALISTIC Y adjustment based on actual spline curvature
        # Use sine wave to distribute correction smoothly across text height
        correction_factor = strength * np.sin(t * np.pi)
        y_adjustment = spline_deviation * correction_factor
        
        # Clamp to reasonable bounds
        y_adjustment = np.clip(y_adjustment, -max_correction, max_correction)
        
        corrected_y = col_y - y_adjustment
        corrected_y = np.clip(corrected_y, 0, h - 1)
        
        map_y[col_mask, x] = corrected_y
    
    # Apply remap
    corrected = cv2.remap(image, map_x, map_y, cv2.INTER_LINEAR)
    return corrected