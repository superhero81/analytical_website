# Employee engagement survey – előkészítési riport

## Eredmény

- Hullámok száma: 50
- Időszak: 2001-H2 – 2026-H1
- Válaszok száma: 31,548
- Egyedi válaszadók: 2,866
- Átlagos hullámonkénti válaszadási arány: 74.8%
- Legalacsonyabb–legmagasabb hullámonkénti válaszadási arány: 70.2%–79.6%
- Átlagpontszámok: engagement 4.12; satisfaction 4.14; work–life balance 3.85

## Beépített összefüggések

- Satisfaction átlag PayZone szerint: {'Zone A': 4.25, 'Zone B': 4.12, 'Zone C': 3.94}
- Work–life balance átlag EmployeeType szerint: {'Contract': 3.76, 'Full-Time': 3.84, 'Part-Time': 4.17}
- A három mutató pozitívan, de nem tökéletesen korrelál:

```
                      EngagementScore  SatisfactionScore  WorkLifeBalanceScore
EngagementScore                  1.00               0.33                  0.19
SatisfactionScore                0.33               1.00                  0.19
WorkLifeBalanceScore             0.19               0.19                  1.00
```

## Generálási szabályok

1. Féléves survey-hullámok márciusban és szeptemberben, 2001-H2 és 2026-H1 között.
2. Hullámonként az induláskor foglalkoztatottak 70–80%-a válaszol.
3. A kitöltés a hullámindítástól számított 0–13. napon történik.
4. Egy munkavállaló hullámonként legfeljebb egyszer válaszolhat.
5. Belépés előtt és kilépés után nincs válasz.
6. Az egyéni alapszint és az autoregresszív hullámzás biztosítja a személyen belüli stabilitást és változást.
7. A magasabb bérzóna mérsékelten magasabb elégedettséggel jár.
8. A részmunkaidő mérsékelten magasabb work–life balance értékkel jár.
9. A szerződéses foglalkoztatás átlagosan kissé alacsonyabb engagementtel és satisfactionnel jár.
10. Az önkéntes és munkáltatói kilépések előtti évben egyes pontszámok fokozatosan csökkennek.

## Automatikus ellenőrzések

- `rows`: 31548
- `unique_response_id`: 31548
- `unknown_employee_id`: 0
- `response_before_start_or_after_exit`: 0
- `response_before_launch`: 0
- `response_more_than_13_days_after_launch`: 0
- `duplicate_employee_within_wave`: 0
- `score_outside_1_5`: 0
