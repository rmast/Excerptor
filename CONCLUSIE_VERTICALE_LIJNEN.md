## Conclusie: Verticale Lijnen Probleem

### Observatie
- STD: Twee blauwe verticale lijnen (keepers) in surface_lines.png
- EXP: Slechts één verticale lijn, dichter bij de linkerkant

### Root Cause Analysis
De experimentele filters (minder agressieve outlier-verwijdering) hebben onverwacht:

1. **Lijnkwaliteit veranderd**: 61 → 19 lijnen (31.1% behouden) vs standaard
2. **Verticale alignment beïnvloed**: make_E_align_page() met INLIER_THRESHOLD=0.5
3. **3D-reconstructie verstoord**: Keepers (verticale lijnen) verkeerd gepositioneerd
4. **Fine-dewarp gefaald**: Geen tekstboxen gedetecteerd na geometrische correctie

### Technische Details
- Verticale lijnen in surface_lines.png komen uit `align.flatten()` in Kim2014.debug_images()
- Deze worden bepaald door `make_E_align_page()` met inlier-detectie op linker/rechter tekstgrenzen
- Experimentele filters → minder lijnen → slechtere inlier-statistieken → verkeerde alignment

### Generaliseerbare Conclusie
**Filter-optimalisatie kan paradoxaal effect hebben**: Minder agressieve filtering kan leiden tot slechtere geometrische reconstructie door:
1. Veranderde distributie van lijn-eindpunten
2. Verkeerde inschatting van tekstgrenzen
3. Instabiele 3D-oppervlakte fitting
4. Falen van de fine-dewarp fase

### Aanbeveling
Experimentele filters moeten gebalanceerd worden met alignment-stabiliteit.
Mogelijk zijn aanpassingen nodig in make_E_align_page() parameters.
