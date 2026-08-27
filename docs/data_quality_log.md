# Adatminőségi és elemzési döntési napló

Ez a dokumentum tartalmazza az adatok ellenőrzése során feltárt
problémákat, az ezekkel kapcsolatos döntéseket és azok indoklását.

## DQ-001 – Az eredeti munkavállalói státusz és a kilépési dátum ellentmondása

**Dátum:** 2026-08-27

### Megállapítás

Az `employee_data.csv` összesen 3000 munkavállalói rekordot tartalmaz.

- 1533 rekordhoz tartozik `ExitDate`.
- 1467 rekordnál az `ExitDate` üres.
- 2458 rekord `EmployeeStatus` értéke `Active`.
- 991 `Active` státuszú rekordhoz mégis tartozik kilépési dátum.

A `TerminationType` és az `ExitDate` mezők egymással következetesek:
minden ismert kilépési típushoz tartozik kilépési dátum, az `Unk`
kategóriához pedig nem tartozik kilépési dátum.

### Döntés

Az eredeti `EmployeeStatus` mezőt nem használjuk közvetlenül az aktív
létszám és a kilépések meghatározásához.

Új, számított státuszt hozunk létre:

- ha az `ExitDate` üres, a számított státusz `Active`;
- ha az `ExitDate` kitöltött, a számított státusz `Exited`.

Az eredeti `EmployeeStatus` értéket változatlanul megőrizzük.

### Időpontra vonatkozó aktív státusz szabálya

Egy munkavállaló egy adott vizsgálati napon akkor számít aktívnak, ha:

1. `StartDate` kisebb vagy egyenlő a vizsgálati dátummal;
2. és az `ExitDate` üres, vagy későbbi a vizsgálati dátumnál.

### Indoklás

Az `ExitDate` és a `TerminationType` egymással következetes, míg az
`EmployeeStatus` 991 esetben ellentmond a kilépési dátumnak.

### Hatás az elemzésre

- A létszám- és fluktuációszámítások a belépési és kilépési dátumokra épülnek.
- Az eredeti státusz külön adatminőségi változóként megmarad.
- Létrehozunk egy `StatusConflict` jelzőváltozót az ellentmondó rekordokhoz.
- Az 1533 kilépett munkavállaló teljes állományon belüli arányát nem nevezzük
  fluktuációs rátának.