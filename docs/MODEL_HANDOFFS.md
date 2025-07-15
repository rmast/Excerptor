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

## GitHub Copilot (Edit Mode) → o3 (Preview) Handoff

**Context**: Parameter tuning onthulde projectie-probleem, niet focal length probleem
**Contribution**: 
- Implementeerde alle 5 TODO points (robustness, fallbacks, scaling)
- Voegde focal_length parameter toe aan go_dewarp() en demo.py
- Systematisch getest f=3230,3500,4000,5000 - hogere f trekt naar centrum
- Ontdekte dat "optimale f=3230" misleidend is - projectie-logica hardcoded

**Handoff Notes**:
- Alle TODO points voltooid, systeem stabiel
- **Hoofdprobleem**: Projectie-algoritme niet generiek voor verschillende f-waarden
- **Symptomen**: f>3230 veroorzaakt "centrum-trek" effect
- **Visual evidence**: surface_lines.png toont progressieve degradatie

## o3 (Preview) Instructions
**Primary Task**: Analyseer en fix projectie-logica voor generieke focal length support

**Key Focus Areas**:
1. `project_to_image()`, `gcs_to_image()` - camera transformations
2. `image_to_focal_plane()` - coordinate mapping
3. `make_mesh_2d_indiv()` - mesh generation logic
4. Principal point (O) berekeningen - mogelijk hardcoded voor f=3230

**Success Criteria**:
- f=5000 should generate proper surface_lines.png (not centrum-only)
- Green lines should align with blue lines at higher f values
- No "centrum-trek" effect at f>3230

**Test Command**: 
```bash
python demo.py -d -i book -vt --scantailor-split -o test_f5000 -a archive_f5000 -n note_f5000.md -f 5000
```

**Context Files**: PROJECT_STATE.md, NEXT_STEPS.md, MODEL_HANDOFFS.md

## GitHub.com Copilot Chat Analysis

**Model**: GitHub.com Copilot (mogelijk o3 Preview)
**Task**: Analyseer projectie-logica centrum-trek effect
**Status**: ✅ **Excellent root cause analysis + concrete fix**

### **Key Findings**:
1. **Direct verantwoordelijk voor centrum-trek**:
   - `project_to_image(points, O)` - formule: `projected = (points * FOCAL_PLANE_Z / points[2])[0:2]`
   - `gcs_to_image(points, O, R)` - gebruikt project_to_image
   - `image_to_focal_plane(points, O)` - gebruikt FOCAL_PLANE_Z
   - `make_mesh_2d_indiv()` - mesh wordt gecomprimeerd naar centrum

2. **Root Cause**: Projectie-formules schalen niet correct met verschillende f-waarden
3. **Effect**: Hogere f → alle punten dichter bij centrum → "centrum-trek"

### **Concrete Fix Procedure**:
1. **CameraParams class** - expliciete parameters i.p.v. globale variabelen
2. **Update project_to_image()** - gebruik camera.FOCAL_PLANE_Z/camera.O
3. **Update gcs_to_image()** - gebruik camera.Of 
4. **Update alle aanroepen** - geef CameraParams door
5. **Debug visualisatie** - eigen camera config voor consistente surface_lines.png

### **Implementation Strategy**:
```python
class CameraParams:
    def __init__(self, f, O):
        self.f = float(f)
        self.O = np.asarray(O)
        self.FOCAL_PLANE_Z = -self.f
        self.Of = np.array([0, 0, self.f], dtype=np.float64)

def project_to_image(points, camera: CameraParams):
    projected = (points * camera.FOCAL_PLANE_Z / points[2])[0:2]
    return (projected.T + camera.O).T
```

### **Next Action**:
**Implementeer deze fix in VS Code** - GitHub.com Copilot heeft de perfecte oplossing gegeven!