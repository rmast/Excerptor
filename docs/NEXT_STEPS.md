# Next Steps - Prioritized Actions

## Current Session (Completed)
**Model**: GitHub Copilot (Edit Mode)
**Task**: Implement TODO Point 2 - Anchor-point fallback in correct_geometry()
**Status**: ✅ Completed (with manual syntax fix)

## Immediate (Next Model)
1. **Implement TODO Point 3**: Graceful fine_dewarp degradation
   - Wrap fine_dewarp call in try/except
   - Return coarse remap (out_0) on ValueError
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
- TODO Point 1 & 2 successfully implemented with robustness checks
- Note: AI generated syntax error fixed manually by user
- Ready for next model to implement TODO Point 3 or parameter tuning
- TODO Point 1 successfully implemented with robustness checks
- Ready for next model to implement TODO Point 2 or parameter tuning
