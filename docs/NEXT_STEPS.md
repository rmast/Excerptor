# Next Steps - Prioritized Actions

## Current Session (Completed)
**Model**: GitHub Copilot (Edit Mode)
**Task**: Implement TODO Point 3 - Graceful fine_dewarp degradation
**Status**: ✅ Completed

### Completed:
1. ✅ Wrapped fine_dewarp call in try/except
2. ✅ Return coarse remap (out_0) on ValueError
3. ✅ Tested successfully - no crashes
4. ⚠️ Visual issue discovered: textlines coordinates mismatch

### Visual Issue Found:
- `*_textlines.tif`: Purple boxes on original image (left position, complete text visible)
- `*_dewarped.tif`: Missing text bottom-left, different margins
- **Problem**: Textline coordinates seem mapped to original, not dewarped image
- **Impact**: Textlines visualization doesn't align with dewarped content

## Immediate (Next Model)
1. **Fix textlines coordinate mapping** (newly discovered issue)
2. **Implement TODO Point 4**: THRESHOLD_MULT scaling
3. **Implement TODO Point 5**: Debug pipeline consistency

## Parameter Tuning Schedule
- **Phase 1**: Stabilize at f=3230 (current) ← **COMPLETED**
- **Phase 2**: Test incremental f increases (3500, 4000, 5000) ← **NEXT**
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
