# Training and development – előkészítési riport

## Eredmény

- Képzési rekordok: 21,358
- Képzésben részt vevő munkavállalók: 2,999
- Időszak: 2001-01-29 – 2026-06-28
- Átlagos képzésszám résztvevőnként: 7.1
- Befejezési arány: 92.9%
- Átlagos költség megvalósítási mód szerint: {'Hybrid': 340.89, 'In-person': 451.75, 'Online': 201.42}

## Delivery mode részlegenként

```
DeliveryMode          Hybrid  In-person  Online
DepartmentType                                 
Admin Offices          0.157      0.247   0.596
Executive Office       0.262      0.333   0.404
IT/IS                  0.169      0.242   0.590
Production             0.113      0.835   0.052
Sales                  0.181      0.296   0.523
Software Engineering   0.173      0.229   0.598
```

## Generálási szabályok

1. Minden képzés teljes időtartama a belépés és a kilépés, illetve 2026-07-01 közé esik.
2. A dolgozók belépés után onboarding képzést, majd évente jellemzően 0–2 szerepkörhöz illeszkedő képzést kaphatnak.
3. A Production képzései döntően jelenlétiak; az irodai területeken az online forma gyakoribb.
4. Az online képzés olcsóbb a hibridnél, a hibrid pedig átlagosan olcsóbb a jelenlétinél.
5. A külső képzés drágább a belső képzésnél; a költség a program és az időtartam szerint is változik.
6. A trénerek és szolgáltatók korlátozott, visszatérő körből kerülnek ki.
7. A `CompletionStatus` és `TrainingResult` külön mező; vizsgaeredmény csak befejezett, értékelt programnál van.

## Automatikus ellenőrzések

- `rows`: 21358
- `unique_training_record_id`: 21358
- `unknown_employee_id`: 0
- `training_outside_employment`: 0
- `duplicate_training_record_id`: 0
- `invalid_completion_result_pair`: 0
- `negative_or_zero_cost`: 0
