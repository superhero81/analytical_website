# Háromfájlos validáció és gördülő 12 havi fluktuáció

Referencia-dátum: **2026-07-01**

## Validáció

- `employee_rows`: 3000
- `unique_empid`: 3000
- `exit_not_after_start`: 0
- `status_exitdate_mismatch`: 0
- `exit_on_2026_07_01`: 0
- `unknown_survey_empid`: 0
- `survey_outside_employment`: 0
- `unknown_training_empid`: 0
- `training_outside_employment`: 0

- Egy adott napon előforduló legtöbb kilépés: **4**
- 2026-07-01-i kilépések száma: **0**

Minden hibamutató értéke 0; a három fájl közötti azonosítók és időbeli kapcsolatok érvényesek.

## Gördülő 12 havi fluktuáció

Alkalmazott definíció:

- időszak: **(2025-07-01, 2026-07-01]**;
- kilépések: minden `ExitDate` az időszakban;
- időszak eleji létszám: **1,601 fő**;
- időszak végi létszám: **1,553 fő**;
- átlagos létszám: `(kezdő létszám + záró létszám) / 2` = **1,577.0 fő**;
- fluktuáció: `12 havi kilépések / átlagos létszám`.

Eredmény:

- 12 havi kilépések: **169 fő**;
- ebből önkéntes: **116 fő**;
- munkáltatói megszüntetés: **31 fő**;
- nyugdíjazás: **22 fő**;
- teljes gördülő 12 havi fluktuáció: **10.72%**;
- önkéntes gördülő 12 havi fluktuáció: **7.36%**.

## Havi kilépések

| Hónap | Kilépések |
|---|---:|
| 2025-02 | 3 |
| 2025-03 | 8 |
| 2025-04 | 8 |
| 2025-05 | 7 |
| 2025-06 | 8 |
| 2025-07 | 6 |
| 2025-08 | 14 |
| 2025-09 | 7 |
| 2025-10 | 8 |
| 2025-11 | 12 |
| 2025-12 | 15 |
| 2026-01 | 12 |
| 2026-02 | 10 |
| 2026-03 | 19 |
| 2026-04 | 15 |
| 2026-05 | 28 |
| 2026-06 | 24 |
