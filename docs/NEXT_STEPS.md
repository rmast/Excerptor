# Next Steps - Prioritized Actions

## Current Session (Handoff Ready)
**Model**: GitHub Copilot (Edit Mode)
**Task**: Parameter tuning analysis completed
**Status**: ✅ **Ready for o3 handoff**

### **HANDOFF STRATEGIEËN** (VS Code limiteert meerdere Copilot-sessies):

#### **Optie 1: Browser-gebaseerd** (Aanbevolen)
1. **Huidige VS Code**: Blijf hier voor context
2. **GitHub.com**: Open project in browser voor o3 chat
3. **File-based handoff**: Gebruik docs/ bestanden voor communicatie

#### **Optie 2: Cursor IDE** 
- Download Cursor IDE (heeft multi-model support)
- Open zelfde projectmap in Cursor
- Gebruik o3 daar terwijl VS Code open blijft

#### **Optie 3: Command-line handoff**
```bash
# Commit huidige staat
git commit -m "Handoff to o3: projectie-logica analysis needed"

# o3 werkt met committed code
# Resultaat wordt terug-gecommit
```

#### **Optie 4: Manual copy-paste session**
- Kopieer relevante code naar o3 chat
- Implementeer fixes handmatig terug in VS Code
- Gebruik docs/ voor context-sharing

### **AANBEVELING**: 
**Optie 1 (Browser)** - Meest praktisch, geen extra software

**Start o3 met**: "Analyseer projectie-logica in dewarp.py die centrum-trek veroorzaakt bij f>3230"

## Current Session (Active)
**Model**: GitHub Copilot (Edit Mode)
**Task**: Implement CameraParams fix for centrum-trek effect
**Status**: 🔄 **Implementing GitHub.com Copilot's solution**

### Implementation Progress:
1. ✅ **CameraParams class** - Added with f, O, FOCAL_PLANE_Z, Of
2. ✅ **Updated project_to_image()** - Support both CameraParams and legacy O
3. ✅ **Updated gcs_to_image()** - Support both CameraParams and legacy O  
4. ✅ **Updated image_to_focal_plane()** - Optional f parameter
5. ✅ **Updated make_mesh_2d_indiv()** - Uses CameraParams for consistent projection
6. ❓ **Test centrum-trek fix** - Ready for testing

### **Test Command**:
```bash
python demo.py -d -i book -vt --scantailor-split -o test_f5000_fixed -a archive_f5000_fixed -n note_f5000_fixed.md -f 5000
```

### **Expected Result**:
- f=5000 should generate proper surface_lines.png (not centrum-only)
- Green lines should align with blue lines
- No "centrum-trek" effect

### Implementation Plan:
1. ✅ Add focal_length parameter to go_dewarp()
2. ✅ Create test_focal_sweep.py script  
3. ✅ Modify demo.py to accept focal_length parameter
4. 🔄 **TESTING IN PROGRESS** - Run systematic test: f=3230,3500,4000,5000,7000,10000
5. ❓ Visual comparison: green lines → blue lines alignment

### Test Results So Far:
- **f=3230** (baseline): ✅ surface_lines.png generated, **OPTIMAL** alignment
- **f=3500**: ✅ surface_lines.png generated, **WORSE** alignment (groene lijnen meer naar midden)
- **f=4000**: ✅ surface_lines.png generated, **MUCH WORSE** - groene lijnen trekken naar centrum
- **f=5000**: ✅ surface_lines.png generated, **SEVERELY DEGRADED** - projectie alleen van centrum
- **f=10000**: ❓ Not tested yet (expect complete failure)

### Key Findings:
- **f=3230**: ✅ **OPTIMAL** - groene lijnen volgen tekst correct
- **f=3500+**: ❌ **PROGRESSIVE DEGRADATION** - groene lijnen trekken naar centrum
- **Higher f**: ❌ **OVERCORRECTION** - alleen centrum zichtbaar, letters te groot
- **THRESHOLD_MULT scaling**: Werkt maar compenseert niet voor fundamenteel probleem

### **CONCLUSIE**: 
🎯 **f=3230 is already optimal for this camera/document combination**
- Originele Samsung S22U kalibratie was correct
- Hogere f waarden veroorzaken **overcorrectie** naar centrum
- Flatbed emulatie (f=10000) is **niet geschikt** voor mobile camera images

### **RECOMMENDATION**: 
✅ **Stop parameter tuning - f=3230 is optimal**
✅ **Focus on other improvements** (textlines mapping, multi-page processing)

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

### **NIEUWE ANALYSE**: 
❌ **Conclusie "f=3230 is optimal" is VOORBARIG**
🔍 **Werkelijk probleem**: Projectie-logica aangepast aan f=3230, niet generiek

### Root Cause Analysis:
- **f=3230**: Werkt omdat **projectie-parameters** daarop afgestemd zijn
- **f>3230**: Projectie trekt naar centrum → **niet focal length probleem, maar projectie-algoritme**
- **o3 Preview identificeerde** meerdere plekken waar projectie plaatsvindt

### **NIEUWE STRATEGIE**:
1. 🎯 **Identificeer projectie-logica** die hardcoded is voor f=3230
2. 🔧 **Maak projectie generiek** voor verschillende brandpuntsafstanden
3. 📊 **Hertest parameter sweep** na projectie-fix
4. 🎨 **Valideer groene → blauwe lijn alignment** opnieuw

### **VRAAG VOOR o3 (Edit Mode)**:
- Analyseer code-verschillen sinds baseline commit
- Zoek projectie-logica die mogelijk hardcoded f=3230 aanneemt
- Identificeer waar "centrum-trek" effect ontstaat bij hogere f-waarden

### **FOCUS AREAS** voor o3:
- `project_to_image()`, `gcs_to_image()` functies
- `image_to_focal_plane()` transformaties  
- `make_mesh_2d_indiv()` mesh generatie
- Camera matrix / principal point berekeningen