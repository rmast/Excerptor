# Next Steps - Prioritized Actions

## Current Session (Active)
**Model**: GitHub Copilot (Edit Mode)
**Task**: Implement TODO Point 4 - THRESHOLD_MULT scaling
**Status**: 🔄 In Progress

### Implementation Plan:
1. ✅ Added THRESHOLD_MULT global variable
2. ✅ Created set_focal_length() function with scaling logic
3. ✅ Applied THRESHOLD_MULT to RANSAC calls in side_lines() and remove_outliers()
4. ✅ Integrated with flatbed mode in kim2014()
5. Test with working command

## Immediate (Next Model)
1. **Implement TODO Point 5**: Debug pipeline consistency
2. **Fix textlines coordinate mapping** (discovered issue)
3. **Implement TODO Point 6**: Refine coarse remap logic

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
- Function signature mismatch was root cause of initial failure
- TODO Point 1, 2 & 3 successfully implemented with robustness checks
- Note: AI generated syntax error fixed manually by user
- **NEW**: Textlines visualization coordinate mismatch needs attention
- TODO Point 3 prevents crashes but reveals coordinate mapping issue
