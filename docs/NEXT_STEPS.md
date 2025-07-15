# Next Steps - Prioritized Actions

## Current Session (Active)
**Model**: GitHub Copilot (Edit Mode)
**Task**: Begin Phase 2 - Parameter Tuning
**Status**: 🔄 In Progress

### Implementation Plan:
1. ✅ Add focal_length parameter to go_dewarp()
2. ✅ Create test_focal_sweep.py script  
3. ✅ Modify demo.py to accept focal_length parameter
4. 🔄 **TESTING IN PROGRESS** - Run systematic test: f=3230,3500,4000,5000,7000,10000
5. ❓ Visual comparison: green lines → blue lines alignment

### Test Results So Far:
- **f=3230** (baseline): ✅ surface_lines.png generated, good alignment
- **f=3500**: ✅ surface_lines.png generated, **WORSE** alignment (groene lijnen meer naar midden)
- **f=4000**: ❌ **NO surface_lines.png generated** - optimization issues
- **f=5000**: ❓ Not tested yet
- **f=10000**: ❓ Not tested yet

### Key Findings:
- **f=3230 → f=3500**: Alignment **degrades** (groene lijnen minder bij tekst)
- **f=4000**: Optimization problems, "**** BAD RUN. ****" messages
- **THRESHOLD_MULT=1.5**: Activated at f=4000 as expected

### Hypothesis:
- **f=3230** might already be **optimal** for this camera/document combination
- Higher f values cause optimization instability
- The original mobile camera focal length was well-calibrated

### Test Commands Ready:
```bash
# Test verschillende focal lengths
python demo.py -d -i book -vt --scantailor-split -o test_f3230 -a archive_f3230 -n note_f3230.md -f 3230
python demo.py -d -i book -vt --scantailor-split -o test_f3500 -a archive_f3500 -n note_f3500.md -f 3500
python demo.py -d -i book -vt --scantailor-split -o test_f4000 -a archive_f4000 -n note_f4000.md -f 4000
python demo.py -d -i book -vt --scantailor-split -o test_f5000 -a archive_f5000 -n note_f5000.md -f 5000
python demo.py -d -i book -vt --scantailor-split -o test_f10000 -a archive_f10000 -n note_f10000.md -f 10000
```

### Visual Success Criteria:
- **surface_lines.png**: Green lines should progressively align with blue baseline
- **all_lines.png**: Blue lines = ground truth text detection
- **Goal**: Find optimal f where green ≈ blue (best dewarp quality)

## **ALL TODO POINTS COMPLETED** 🎉

### Implementation Summary:
1. ✅ **TODO Point 1**: Robustness in make_mesh_2d_indiv (total_arc fallback)
2. ✅ **TODO Point 2**: Anchor-point fallback for fine_dewarp
3. ✅ **TODO Point 3**: Graceful fine_dewarp degradation (try/catch)
4. ✅ **TODO Point 4**: THRESHOLD_MULT scaling for flatbed mode
5. ✅ **TODO Point 5**: Debug pipeline consistency (auto-implemented)

## Ready for Next Phase

### Parameter Tuning Schedule:
- **Phase 1**: Stabilize at f=3230 (current) ← **✅ COMPLETED**
- **Phase 2**: Test incremental f increases (3500, 4000, 5000) ← **🎯 START HERE**
- **Phase 3**: Approach f=10000 (flatbed target)
- **Phase 4**: Visual validation (green lines → blue lines alignment)

### Outstanding Issues:
1. **Fix textlines coordinate mapping** (paarse vakjes niet gegenereerd - mogelijk opgelost)
2. **Multiple page processing** (note.md shows multiple entries for same file)