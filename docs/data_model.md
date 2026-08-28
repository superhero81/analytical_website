# HR Insight AI – adatmodell

## Cél

A dashboard három egymással összekapcsolható, tisztított és
demonstrációs célú HR-adatállományra épül.

A toborzási adatállomány nem része a pilotnak.

## 1. Munkavállalói törzsadatok

**Fájl:** `data/processed/employee_data_clean.csv`

**Elemzési egység:** egy sor egy munkavállaló.

**Elsődleges kulcs:** `EmpID`

**Rekordszám:** 3000 munkavállaló.

Fő tartalmak:

- belépési és kilépési dátum;
- munkavállalói státusz és foglalkoztatási típus;
- üzleti egység, divízió és szervezeti terület;
- munkakör és vezetői kapcsolat;
- fizetési zóna;
- teljesítményértékelés;
- demográfiai és földrajzi csoportváltozók.

A vezetői hierarchia a `SupervisorID` mező segítségével kapcsolható
vissza ugyanennek a táblának az `EmpID` mezőjéhez.

## 2. Engagement-felmérések

**Fájl:** `data/processed/employee_engagement_survey_data_clean.csv`

**Elemzési egység:** egy sor egy munkavállaló egy felmérési hullámban
adott válasza.

**Kapcsolókulcs:** `EmpID`

**Rekordszám:** 31 548 válasz.

**Időszak:** 2001 második félévétől 2026 első félévéig.

**Felmérési rendszer:** 50 féléves hullám.

Fő mutatók:

- `EngagementScore`;
- `SatisfactionScore`;
- `WorkLifeBalanceScore`.

A válaszok csak a munkavállaló foglalkoztatási időszakán belül
keletkezhetnek. A hullámonkénti válaszadási arány körülbelül 70–80%.

## 3. Képzési és fejlesztési adatok

**Fájl:** `data/processed/training_and_development_data_clean.csv`

**Elemzési egység:** egy sor egy képzési részvétel.

**Kapcsolókulcs:** `EmpID`

**Rekordszám:** 21 358 képzési rekord.

Fő tartalmak:

- képzés dátuma;
- program és képzési kategória;
- képzés típusa;
- online vagy jelenléti megvalósítás;
- helyszín;
- szolgáltató vagy tréner;
- időtartam és költség;
- teljesítési státusz;
- képzési eredmény.

A képzés dátuma minden esetben a munkavállaló belépése után és
kilépése előtt van. A képzések gyakorisága, formája és költsége
illeszkedik a munkavállaló szerepköréhez.

## Táblakapcsolatok

A három tábla az `EmpID` mezőn keresztül kapcsolódik:

- egy munkavállalóhoz több engagement-válasz tartozhat;
- egy munkavállalóhoz több képzési rekord tartozhat;
- egy engagement-válasz vagy képzési rekord pontosan egy
  munkavállalóhoz tartozik.

## A mutatók hivatalos adatforrása

- Létszám, belépés, kilépés és fluktuáció:
  `employee_data_clean.csv`
- Engagement, elégedettség és work–life balance:
  `employee_engagement_survey_data_clean.csv`
- Képzési részvétel, eredmény, időtartam és költség:
  `training_and_development_data_clean.csv`

## Adat-előkészítési dokumentáció

A végrehajtott tisztításokat és generálási szabályokat külön
jelentések tartalmazzák:

- `employee_data_cleaning_report.md`;
- `employee_engagement_survey_cleaning_report.md`;
- `training_and_development_cleaning_report.md`.
