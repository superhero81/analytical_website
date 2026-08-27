# HR-adatszótár

Ez a dokumentum az elemzéshez használt változók jelentését,
forrását és alkalmazási szabályait tartalmazza.

## Munkavállalói törzsadatok

Forrás: `employee_data.csv`

| Változó | Jelentés | Felhasználás | Megjegyzés |
|---|---|---|---|
| `EmpID` | Anonim munkavállalói azonosító | Táblák összekapcsolása | 3000 egyedi érték |
| `FirstName` | Keresztnév | Nem használjuk | Személyes jellegű mező |
| `LastName` | Vezetéknév | Nem használjuk | Személyes jellegű mező |
| `ADEmail` | Munkahelyi e-mail-cím | Nem használjuk | Személyes jellegű mező |
| `DOB` | Születési dátum | Csak korcsoport képzéséhez | A pontos dátumot nem publikáljuk |
| `StartDate` | Belépés dátuma | Létszám és szolgálati idő | Dátummá alakítjuk |
| `ExitDate` | Kilépés dátuma | Kilépés és fluktuáció | Dátummá alakítjuk |
| `EmployeeStatus` | Eredeti munkavállalói státusz | Adatminőség-ellenőrzés | Közvetlen KPI-számításhoz nem használjuk |
| `TerminationType` | Kilépés típusa | Önkéntes és nem önkéntes kilépés | Az `ExitDate` mezővel következetes |
| `BusinessUnit` | Üzleti egység | Bontás és szűrés | Kategóriaváltozó |
| `DepartmentType` | Szervezeti terület | Bontás és szűrés | Kategóriaváltozó |
| `Division` | Divízió | Bontás és szűrés | Kategóriaváltozó |
| `EmployeeType` | Foglalkoztatás típusa | Bontás és szűrés | Kategóriaváltozó |
| `Title` | Munkakör megnevezése | Bontás | Kis csoportok ellenőrzése szükséges |
| `Performance Score` | Teljesítménykategória | Teljesítményelemzés | Kategóriaváltozó |
| `Current Employee Rating` | Aktuális teljesítményértékelés | Teljesítményelemzés | Skála tartományát még ellenőrizzük |

## Engagement-kutatás

Forrás: `employee_engagement_survey_data.csv`

| Változó | Jelentés | Felhasználás | Megjegyzés |
|---|---|---|---|
| `Employee ID` | Munkavállalói azonosító | Összekapcsolás az `EmpID` mezővel | Minden munkavállalóhoz tartozik rekord |
| `Survey Date` | A felmérés dátuma | Időszaki elemzés | Dátummá alakítjuk |
| `Engagement Score` | Engagement-pontszám | KPI és csoportos összehasonlítás | Skála tartományát még ellenőrizzük |
| `Satisfaction Score` | Elégedettségi pontszám | KPI és csoportos összehasonlítás | Skála tartományát még ellenőrizzük |
| `Work-Life Balance Score` | Munka–magánélet egyensúlyának pontszáma | KPI és csoportos összehasonlítás | Skála tartományát még ellenőrizzük |

## Képzési adatok

Forrás: `training_and_development_data.csv`

| Változó | Jelentés | Felhasználás | Megjegyzés |
|---|---|---|---|
| `Employee ID` | Munkavállalói azonosító | Összekapcsolás az `EmpID` mezővel | Minden munkavállalóhoz tartozik rekord |
| `Training Date` | Képzés dátuma | Időszaki elemzés | Dátummá alakítjuk |
| `Training Program Name` | Képzési program neve | Képzéstípusok elemzése | Kategóriaváltozó |
| `Training Type` | Képzés típusa | Bontás és szűrés | Kategóriaváltozó |
| `Training Outcome` | Képzés eredménye | Eredményességi mutató | Kategóriaváltozó |
| `Training Duration(Days)` | Képzés időtartama napokban | Átlagos időtartam | Numerikus változó |
| `Training Cost` | Képzés költsége | Összes és átlagos költség | Pénznemét még ellenőrizzük |

## Toborzási adatok

Forrás: `recruitment_data.csv`

| Változó | Jelentés | Felhasználás | Megjegyzés |
|---|---|---|---|
| `Applicant ID` | Jelentkező azonosítója | Egyedi jelentkezők számítása | A munkavállalói azonosítóktól különálló |
| `Application Date` | Jelentkezés dátuma | Időszaki elemzés | Dátummá alakítjuk |
| `Status` | Jelentkezés állapota | Felvételi tölcsér | Kategóriaváltozó |
| `Job Title` | Megpályázott munkakör | Bontás és szűrés | Kategóriaváltozó |
| `Education Level` | Legmagasabb végzettség | Jelentkezői összetétel | Kategóriaváltozó |
| `Years of Experience` | Szakmai tapasztalat évei | Jelentkezői összetétel | Numerikus változó |
| `Desired Salary` | Elvárt fizetés | Átlagok és összehasonlítás | Pénznemét még ellenőrizzük |
| `First Name`, `Last Name`, `Phone Number`, `Email`, `Address` | Személyes jellegű adatok | Nem használjuk | Nem kerülnek a feldolgozott adatba |