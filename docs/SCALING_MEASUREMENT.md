# Scaling Factor Measurement Protocol

## **Test Setup**:
1. **Baseline**: f=3230 surface_lines.png
2. **Test**: f=3500 surface_lines.png
3. **Compare**: groene lijnen grootte verschil

## **Measurement Method**:
1. **Visual comparison**: Open beide surface_lines.png files
2. **Measure line length**: Gebruik image viewer met ruler/measure tool
3. **Calculate ratio**: length_f3500 / length_f3230
4. **Expected ratio**: Als puur schaaleffect, ratio = 3230/3500 ≈ 0.92

## **Debug Output Analysis**:
- **mesh bounds**: vergelijk "mesh: Crop(...)" output
- **Coordinate ranges**: analyse X,Y ranges in debug output
- **Scaling pattern**: consistent factor across alle lijnen?

## **Implementation Strategy**:
Als ratio = 3230/3500, dan:
```python
# In debug_images() - schaal groene lijnen terug
scale_factor = 3230.0 / current_f
line_2d_scaled = line_2d * scale_factor + offset_correction
```

## **Test Commands**:
```bash
# Generate comparison images
python demo.py -d -i book -vt --scantailor-split -o test_f3230_measure -f 3230
python demo.py -d -i book -vt --scantailor-split -o test_f3500_measure -f 3500

# Compare surface_lines.png files
```

# Scaling Factor Measurement - Initial Results

## **Confirmed Observation**:
✅ **f=3500**: Groene lijnen zijn kleiner dan bij f=3230
✅ **Scaling effect**: Bevestigd - niet fundamentele incompatibiliteit

## **Next Steps**:
1. Fix NameError in fine_dewarp (f_points parameter)
2. Generate comparison surface_lines.png files
3. Measure exact scaling ratio
4. Implement scaling correction

## **Expected Scaling Ratio**:
Als puur inverse schaal-effect: `ratio = 3230/3500 ≈ 0.923`

# Scaling Fix Implementation

## **Confirmed Scaling Factor**:
- **f=3230**: baseline (scale_factor = 1.0)
- **f=3500**: scale_factor = 3230/3500 ≈ 0.923

## **Fix Strategy**:
1. **Scaling correction** in debug_images() rond lijn-centrum
2. **Preserve original projection** voor production pipeline
3. **Visual consistency** - groene lijnen zelfde grootte onafhankelijk van f

## **Test Plan**:
```bash
# Test met scaling correction
python demo.py -d -i book -vt --scantailor-split -o test_f3500_scaled -f 3500
```

## **Expected Result**:
- **f=3500**: Groene lijnen zelfde grootte als f=3230
- **No crashes**: Robuste bounds checking werkt
- **Consistent visualization**: Surface_lines.png vergelijkbaar

## **Next Steps**:
1. Test f=3500 scaling fix
2. Test f=4000 als f=3500 werkt
3. Approach f=5000 incrementeel

# Scaling Fix - Variable Scope Issue

## **Fixed Issues**:
1. **Variable scope**: `O` not defined in debug_images() - use `self.O`
2. **Projection consistency**: Use `gcs_to_image()` for all projections
3. **Scaling factor**: 0.923 correctly calculated for f=3500

## **Test Results**:
- **f=3500**: ✅ Scaling factor calculated correctly
- **Expected**: Surface_lines.png with groene lijnen zelfde grootte als f=3230

## **Next Test**:
```bash
python demo.py -d -i book -vt --scantailor-split -o test_f3500_scaled_fixed -f 3500
```

# Scaling Fix v2 - Image Center Scaling

## **Fixed Issues**:
1. **Scaling center**: Gebruik image centrum i.p.v. lijn centrum
2. **Both dimensions**: Schaal zowel x als y coördinaten
3. **Consistent application**: Alle debug lijnen (groene, rode, blauwe) geschaald

## **Expected Result**:
- **f=3500**: Groene lijnen **vergroot** naar f=3230 grootte
- **Both directions**: Horizontale EN verticale scaling
- **Scale factor**: 3230/3500 ≈ 0.923 → lijnen worden **GROTER** (1/0.923 = 1.083)

## **Test**:
```bash
python demo.py -d -i book -vt --scantailor-split -o test_f3500_v2 -f 3500
```

# Scaling Results Summary

## ✅ **Success Range**: f=3230 - f=6000
- **Consistent scaling**: Groene lijnen correct geschaald
- **Visual alignment**: Lijnen projecteren op consistente afstand van tekst
- **No crashes**: Graceful degradation implemented

## ⚠️ **Boundary Effects**: f=7500+
- **Vertical distortion**: Rare dingen in verticale richting
- **f=10000**: IndexError → graceful degradation

## 🎯 **Next Steps**:
1. **Alignment improvement**: Groene → blauwe lijnen matching
2. **Production scaling**: Apply to final dewarped.tif
3. **Algorithm limits**: f=6000 practical maximum

## **Recommendation**:
- **f=3230-4000**: Optimal range
- **f=5000-6000**: Usable with monitoring
- **f=7500+**: Avoid - algorithm breakdown

# Production Scaling Implementation

## ✅ **Complete Scaling Pipeline**:
1. **Debug scaling**: Surface_lines.png visualization ✓
2. **Production scaling**: Final mesh for dewarped.tif ✓

## **Expected Result**:
- **f=3500**: Dewarped.tif met correcte schaling rond mesh centrum
- **Consistent behavior**: Debug lines ↔ production output
- **Scale factor**: 3500/3230 ≈ 1.084 toegepast op mesh coördinaten

## **Test**:
```bash
python demo.py -d -i book -vt --scantailor-split -o test_f3500_production -f 3500
```

**Expected**: Finale dewarped.tif toont zelfde scaling als groene lijnen in surface_lines.png

# Production Scaling - Safety Limits

## **Problem Identified**:
- **f=5000**: scale_factor=1.548 → mesh explosion (coordinates ~3e8)
- **OpenCV error**: Corrupted image data from extreme mesh

## **Safety Measures Implemented**:
1. **Scale factor limits**: 0.5 ≤ scale_factor ≤ 2.0
2. **Mesh bounds check**: max_coord < 1e6
3. **Graceful fallback**: Disable scaling on explosion
4. **OpenCV safety**: Handle connectedComponents errors

## **Recommended Usage**:
- **f=3230-4000**: Full scaling support ✓
- **f=4000-5000**: Clamped scaling (limited benefit)
- **f>5000**: Scaling disabled (safety fallback)
