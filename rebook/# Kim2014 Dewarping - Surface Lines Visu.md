# Kim2014 Dewarping - Surface Lines Visualisatie Fix

## Context
Ik werk aan een Kim2014 dewarping algoritme in Python. De core functionaliteit werkt perfect, maar er is een specifiek visualisatie probleem in de debug output.

## Werkende Staat
- **Flatbed optimalisaties volledig functioneel**: focal length 3230→10000, agressieve filtering (threshold=25), geometrisch centrum focus
- **Dewarping pipeline werkt correct**: produceert juiste output images met kwaliteitscore 0.128
- **Alle functionaliteit intact**: `--flatbed-optimized` flag werkt volledig

## Probleem
**Kernprobleem**: `surface_lines.png` debug visualisatie toont groene lijnen 3x te klein door focal length wijziging (3230→10000)

De groene lijnen zijn nu 1/3 grootte, centraal gepositioneerd, en hebben boogjes aan de rechterkant. Dit is puur een visualisatie probleem - de dewarping zelf werkt perfect.

## Uitgeprobeerde Oplossingen (ALLE GEFAALD)
1. ✗ Schaalfactor 3.10 met centrum-schaling
2. ✗ Parameter switching (tijdelijk originele focal length voor visualisatie)
3. ✗ Platte lijnen Z=0 (veroorzaakte lege mesh)
4. ✗ Gescheiden projectie voor flatbed/normale mode
5. ✗ Uitgebreide Y-range in plaats van echte tekstregels

## Technische Details
- **Projectie formule**: `projected = (points * FOCAL_PLANE_Z / points[2])[0:2]`
- **Schaalfactor**: 10000/3230 = 3.10x
- **Debug functie**: `debug_images()` in `rebook/dewarp.py` regel ~1380-1460

## Gewenste Oplossing
**Doel**: Fix `surface_lines.png` visualisatie zonder dewarping functionaliteit te beïnvloeden

**Strategie**: Isoleer debug visualisatie volledig van productie code:
1. Maak separate `debug_focal_length = 3230` constant voor visualisatie
2. Gebruik originele projectie parameters alleen voor `surface_lines.png`
3. Laat alle andere functionaliteit ongewijzigd op `focal_length = 10000`

**Kritiek**: Vermijd complexe schaling/parameter switching die geometrische distorsies veroorzaakt

## Test Commando
```bash
python demo.py -d -i book -vt --flatbed-optimized --scantailor-split -o test_output -a test_archive -n test_note.md