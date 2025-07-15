# Iteration Log - Parameter Tuning History

## Iteration 0 (Baseline)
- **Commit**: 00ae70e08a1cba61c307476c3a3925537428cf7c
- **Parameters**: f=3230, THRESHOLD_MULT=1.0
- **Status**: ✅ Working
- **Visual**: Green/blue alignment baseline established

## Iteration 1 (Completed)
- **Model**: GitHub Copilot (Edit Mode)
- **Changes**: 
  - Added `flatbed=False` parameter to `kim2014()` and `go_dewarp()`
  - ✅ TODO Point 1: Robustness in `make_mesh_2d_indiv()` - VERIFIED IMPLEMENTED
  - Added total_arc validation with fallback to `max(abs(box_XYZ.w), 1.0)`
  - Added minimum 2 mesh rows guarantee: `n_points_h = max(n_points_h, 2)`
- **Status**: ✅ Working + Robust
- **Test**: `python demo.py -d -i book -vt --scantailor-split -o test_output -a test_archive -n test_note.md`
- **Visual**: No crashes, robustness patches active, should show WARNING if fallback used
- **Next**: Implement TODO Point 2 (Anchor-point fallback)

## Iteration 2 (Completed)
- **Model**: GitHub Copilot (Edit Mode) 
- **Changes**:
  - ✅ TODO Point 2: Anchor-point fallback in `correct_geometry()`
  - Added dummy anchor points when f_points is empty
  - Ensures np.concatenate() never fails in fine_dewarp
  - ⚠️ Minor syntax error (identifier typo) manually fixed by user
- **Status**: ✅ Working after manual fix
- **Test**: `python demo.py -d -i book -vt --scantailor-split -o test_output -a test_archive -n test_note.md`
- **Visual**: No crashes, anchor fallback active, should show WARNING if used
- **Next**: Implement TODO Point 3 (Graceful fine_dewarp degradation)

## Iteration 3 (Completed)
- **Model**: GitHub Copilot (Edit Mode)
- **Changes**:
  - ✅ TODO Point 3: Graceful degradation in `fine_dewarp()`
  - Implemented checks for empty or single-point f_points
  - Bypasses fine_dewarp if insufficient points, avoiding crashes
  - ⚠️ Minor logical error in point check manually fixed by user
- **Status**: ✅ Working after manual fix
- **Test**: `python demo.py -d -i book -vt --scantailor-split -o test_output -a test_archive -n test_note.md`
- **Visual**: No crashes on degenerate cases, warnings shown
- **Next**: Implement TODO Point 4 (THRESHOLD_MULT scaling)

## Iteration 4 (Completed)
- **Model**: GitHub Copilot (Edit Mode)
- **Changes**:
  - ✅ TODO Point 4: THRESHOLD_MULT scaling implemented
  - Added global THRESHOLD_MULT variable with scaling logic
  - Created set_focal_length() function (f=10000 → THRESHOLD_MULT=1.5)
  - Applied THRESHOLD_MULT to RANSAC calls in side_lines() and remove_outliers()
  - Integrated with flatbed mode in kim2014()
- **Status**: ✅ Working - improved filtering and margins
- **Test**: Boxes follow filtering correctly, left margin improved
- **Visual**: Text bottom-left no longer cut off
- **Next**: Implement TODO Point 5 (Debug pipeline consistency)

## Template for Future Iterations
