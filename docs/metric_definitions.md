# HR-mutatók és számítási definíciók

Ez a dokumentum tartalmazza a dashboardban használt mutatók üzleti
jelentését, képletét és számítási szabályait.

## Aktív létszám egy adott napon

### Definíció

Azon munkavállalók száma, akik a vizsgált napon már beléptek, és még
nem léptek ki.

### Számítási szabály

Egy munkavállaló akkor aktív a vizsgált napon, ha:

- `StartDate` kisebb vagy egyenlő a vizsgált dátummal;
- és az `ExitDate` üres, vagy későbbi a vizsgált dátumnál.

### Szükséges változók

- `EmpID`
- `StartDate`
- `ExitDate`

---

## Kilépők száma egy időszakban

### Definíció

Azon munkavállalók száma, akiknek a kilépési dátuma a kiválasztott
időszakba esik.

### Számítási szabály

```text
Időszak kezdete ≤ ExitDate ≤ időszak vége
Szükséges változók
EmpID
ExitDate
Éves fluktuációs ráta
Definíció

Az adott évben kilépő munkavállalók száma az év átlagos állományi
létszámához viszonyítva.

Képlet
Éves fluktuációs ráta =
adott évben kilépők száma
/
((év eleji aktív létszám + év végi aktív létszám) / 2)
× 100
Megjegyzés

Az éves fluktuációs ráta külön számítható:

összes kilépőre;
önkéntes kilépőkre;
nem önkéntes kilépőkre;
szervezeti egységekre;
munkavállalói típusokra.
Kilépett munkavállalók aránya a teljes adatállományban
Definíció

A kilépési dátummal rendelkező rekordok aránya az adatállomány összes
munkavállalói rekordján belül.

Képlet
Kilépési dátummal rendelkező munkavállalók száma
/
összes munkavállaló száma
× 100
Korlátozás

Ez kumulált állományi arány, nem időszaki fluktuációs ráta. Nem szabad
éves fluktuációként vagy iparági benchmarkkal összehasonlítható
mutatóként értelmezni.