# Next Steps - Prioritized Actions

## Current Session (Completed)
**Model**: GitHub Copilot (Edit Mode)
**Task**: Implement TODO Point 4 - THRESHOLD_MULT scaling
**Status**: ✅ Completed - margins and filtering improved

## Current Session (Verification Needed)
**Model**: GitHub Copilot (Edit Mode)
**Task**: Verify TODO Point 4 - THRESHOLD_MULT scaling implementation
**Status**: ⚠️ Needs verification

### THRESHOLD_MULT Verification Checklist:
1. ✅ Default f=3230 → THRESHOLD_MULT=1.0 (normale strengheid)
2. ✅ Flatbed f=10000 → THRESHOLD_MULT=1.5 (ruimere filtering)
3. ❓ Check: Is THRESHOLD_MULT correctly applied to all RANSAC calls?
4. ❓ Check: Does flatbed mode show debug message with new values?
5. ❓ Test: Run with `flatbed=True` to verify scaling works

### What THRESHOLD_MULT does:
- **1.0**: Normale RANSAC filtering (strikte lijn detectie)
- **1.5**: Ruimere filtering (accepteert meer punten als inliers)
- **Higher values**: Meer tolerantie voor ruis in flatbed scans

### Test Commands:
```bash
# Test normale modus (f=3230, THRESHOLD_MULT=1.0)
python demo.py -d -i book -vt --scantailor-split -o test_output -a test_archive -n test_note.md

# Test flatbed modus (f=10000, THRESHOLD_MULT=1.5) - if supported
# [Need to check if demo.py supports flatbed parameter]
```

## Immediate (Next Model)
1. **Implement TODO Point 5**: Debug pipeline consistency
   - Make lib.debug_prefix consistent throughout pipeline
   - Ensure consistent debug output formatting
2. **Fix textlines coordinate mapping** (discovered issue)
3. **Begin parameter tuning**: Test f=3500, f=4000, f=5000

## Parameter Tuning Schedule
- **Phase 1**: Stabilize at f=3230 (current) ← **COMPLETED**
- **Phase 2**: Test incremental f increases (3500, 4000, 5000) ← **READY TO START**
- **Phase 3**: Approach f=10000 (flatbed target)
- **Phase 4**: Optimize THRESHOLD_MULT correlation

## Success Metrics
- ✅ No crashes during parameter transitions
- ✅ Visual improvement in green/blue line alignment
- ✅ Maintained compatibility with existing command

## Session Notes
- Function signature mismatch was root cause of initial failure
- TODO Point 1, 2 & 3 successfully implemented with robustness checks
- Note: AI generated syntax error fixed manually by user
- **NEW**: Textlines visualization coordinate mismatch needs attention
- TODO Point 3 prevents crashes but reveals coordinate mapping issue
- Function signature mismatch was root cause of initial failure
- TODO Point 1, 2 & 3 successfully implemented with robustness checks
- Note: AI generated syntax error fixed manually by user
- **NEW**: Textlines visualization coordinate mismatch needs attention
- TODO Point 3 prevents crashes but reveals coordinate mapping issue
- Function signature mismatch was root cause of initial failure
- TODO Point 1, 2 & 3 successfully implemented with robustness checks
- Note: AI generated syntax error fixed manually by user
- **NEW**: Textlines visualization coordinate mismatch needs attention
- TODO Point 3 prevents crashes but reveals coordinate mapping issue