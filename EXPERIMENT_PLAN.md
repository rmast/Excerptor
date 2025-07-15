# Experimenteel Plan: Optimalisatie van Lijnfiltering voor Dewarping

## Onderzoeksvraag
Hoe kunnen we de lijnfiltering optimaliseren zodat meer van de perfecte blauwe baselines (uit all_lines.png) behouden blijven voor betere dewarping-resultaten?

## Hypothese
De huidige filter-parameters zijn te restrictief en verwijderen goede tekstlijnen die zouden leiden tot betere dewarping. Door de parameters aan te passen kunnen we:
1. Meer accurate baselines behouden
2. Betere 3D oppervlak-modellering krijgen  
3. Rechter gedewarpieerde tekst produceren

## Methodologie

### Fase 1: Baseline meting (huidige situatie)
- [x] Implementeer kwaliteitsmeting (rechtheid van tekstlijnen)
- [x] Voeg debug-output toe voor lijnstatistieken
- [x] Run standaard test: `python demo.py -d -i book -vt --scantailor-split -o test_std`

### Fase 2: Experimentele variant
- [x] Implementeer experimentele filters met minder agressieve outlier-verwijdering
- [x] Run experimentele test: `python demo.py -d -i book -vt --scantailor-split -o test_exp -ef`

### Fase 3: Vergelijking en meting
Parameters om te meten:
1. **Lijnretentie**: Hoeveel lijnen behouden (rood -> blauw in all_lines.png)
2. **Kwaliteitsscore**: Rechtheid van gedewarpieerde tekstlijnen (0-1)
3. **Visuele beoordeling**: Welke resultaten zien er beter uit (1-5 schaal)
4. **3D-model kwaliteit**: Hoe goed sluiten surface_lines aan bij tekst

### Fase 4: Iteratie (indien nodig)
Gebaseerd op resultaten van Fase 3:
- Als experimenteel beter: verder verlagen van outlier-thresholds
- Als standaard beter: andere parameters tunen (stroke_outliers k-waarde)
- Als mixed resultaten: implementeer adaptieve filtering

## Verwachte Outcomes

### Scenario A: Experimentele filters zijn beter
- **Observatie**: Meer lijnen behouden, hogere kwaliteitsscores, rechter tekst
- **Conclusie**: Huidige filters zijn te restrictief
- **Actie**: Adopteer nieuwe parameters, test op meer beelden

### Scenario B: Standaard filters zijn beter  
- **Observatie**: Lagere kwaliteitsscores met experimentele filters
- **Conclusie**: Huidige filters zijn adequaat, probleem ligt elders
- **Actie**: Onderzoek andere componenten (3D-modellering, surface fitting)

### Scenario C: Mixed resultaten
- **Observatie**: Beide hebben voor- en nadelen
- **Conclusie**: Need voor adaptieve/intelligente filtering
- **Actie**: Ontwikkel context-afhankelijke filtering

## Uitvoering

1. **Run experimenten**: `./run_experiments.sh`
2. **Analyseer resultaten**: `python analyze_results.py`
3. **Documenteer bevindingen** in dit bestand
4. **Herhaal met variaties** indien nodig

## Resultaten

### Test 1: [Datum]
- Standaard filters: 
  - Lijnen behouden: X% 
  - Kwaliteitsscore: Y
  - Visuele beoordeling: Z/5
- Experimentele filters:
  - Lijnen behouden: X%
  - Kwaliteitsscore: Y  
  - Visuele beoordeling: Z/5
- **Conclusie**: [In te vullen na test]

### Test 2: [Datum] (indien nodig)
- [Resultaten vervolgtest]

## Finale Conclusie en Aanbevelingen
[In te vullen na voltooiing experimenten]

## Generaliseerbare Inzichten
[Te ontwikkelen parameters/regels die toepasbaar zijn op andere documenten]
