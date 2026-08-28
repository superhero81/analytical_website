# employee_data.csv – tisztítási riport

## Eredmény

- Rekordok: 3,000
- Mezők: 26 → 24 (három redundáns mező törölve, `SupervisorID` hozzáadva)
- Dátumtartomány: 2001-01-01 – 2026-07-01
- Státuszok: Active 1,467; Leave of Absence 86; Voluntarily Terminated 942; Terminated for Cause 285; Retired 220
- Egyedivé tett, korábban duplikált e-mail rekordok: 4
- Új vezetői kapcsolattal ellátott rekordok: 3000
- Életkor miatt korrigált DOB rekordok: 910

## Alkalmazott szabályok

1. A `StartDate` újraosztva 2001-01-01 és 2026-07-01 között, rögzített véletlen maggal.
2. Az `ExitDate` csak kilépett dolgozóknál maradt; mindig későbbi a belépésnél és legkésőbb 2026-07-01.
3. A státuszok: `Active`, `Leave of Absence`, `Voluntarily Terminated`, `Terminated for Cause`, `Retired`.
   A nyugdíjazás életkori szabálya: 63 éves kortól minden kilépő, 60–62 évesen 35%, 58–59 évesen 10% `Retired`.
   A fennmaradó, ismeretlen típusú kilépések 75–25%-ban kerültek az önkéntes és a munkáltatói megszüntetés kategóriájába.
4. A `TerminationType` és `TerminationDescription` mezők törölve.
5. Az `EmployeeClassificationType` az `EmployeeType` alapján egységesítve.
6. A `DepartmentType` és `Division` a munkakör alapján egységes szervezeti struktúrába került.
7. Az `EmployeeType` munkakörfüggő, életszerű arányokkal újragenerálva; a besorolási mező ehhez igazítva.
8. A `PayZone` a munkakör, senioritás és szolgálati idő alapján képzett bérsáv.
9. A teljesítményszöveg és az 1–5-ös értékelés összehangolva.
10. A `LocationCode` az államhoz kapcsolódó belső telephelykód; a félrevezető véletlen irányítószámok megszűntek.
11. A tartalmilag redundáns és ellentmondásos `JobFunctionDescription` mező törölve.
12. A duplikált e-mail-címek az `EmpID` hozzáadásával egyedivé téve.
13. A vezetői kapcsolat érvényes dolgozói azonosítóra épül; új `SupervisorID` mező készült.
14. A DOB csak akkor módosult, ha az új dátumok mellett a dolgozó belépéskor 18 év alatti, illetve a referencia-időpontban 69 év feletti lett volna.
15. A szövegmezők eleji és végi felesleges szóközök eltávolítva.

## Automatikus ellenőrzések

- `rows`: 3000
- `columns`: 24
- `unique_empid`: 3000
- `unique_email`: 3000
- `start_out_of_range`: 0
- `exit_out_of_range`: 0
- `exit_not_after_start`: 0
- `active_with_exit`: 0
- `leave_with_exit`: 0
- `terminated_without_exit`: 0
- `age_below_18_at_start`: 0
- `age_above_69_at_reference`: 0
- `invalid_supervisor_id`: 0
