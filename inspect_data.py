from pathlib import Path

import pandas as pd


data_folder = Path("data/raw")
csv_files = sorted(data_folder.glob("*.csv"))

for file_path in csv_files:
    data = pd.read_csv(file_path)

    print()
    print("=" * 60)
    print(f"Fájl: {file_path.name}")
    print(f"Sorok száma: {data.shape[0]}")
    print(f"Oszlopok száma: {data.shape[1]}")
    print("Oszlopnevek:")

    for column in data.columns:
        print(f"  - {column}")

        missing_values = data.isna().sum()
    missing_values = missing_values[missing_values > 0]

    print("Hiányzó értékek:")

    if missing_values.empty:
        print("  Nincs hiányzó érték.")
    else:
        for column, count in missing_values.items():
            percentage = count / len(data) * 100
            print(f"  - {column}: {count} db ({percentage:.1f}%)")

employees = pd.read_csv(data_folder / "employee_data.csv")
engagement = pd.read_csv(
    data_folder / "employee_engagement_survey_data.csv"
)
training = pd.read_csv(
    data_folder / "training_and_development_data.csv"
)

employee_ids = set(employees["EmpID"])
engagement_ids = set(engagement["Employee ID"])
training_ids = set(training["Employee ID"])

print()
print("=" * 60)
print("AZONOSÍTÓK ELLENŐRZÉSE")
print(f"Egyedi munkavállalók: {employees['EmpID'].nunique()}")
print(f"Duplikált EmpID-k: {employees['EmpID'].duplicated().sum()}")
print(
    "Engagementből hiányzó munkavállalók: "
    f"{len(employee_ids - engagement_ids)}"
)
print(
    "Képzésből hiányzó munkavállalók: "
    f"{len(employee_ids - training_ids)}"
)
print(
    "Ismeretlen azonosítók az engagement táblában: "
    f"{len(engagement_ids - employee_ids)}"
)
print(
    "Ismeretlen azonosítók a képzési táblában: "
    f"{len(training_ids - employee_ids)}"
)


print()
print("=" * 60)
print("MUNKAVÁLLALÓI STÁTUSZOK")
print(employees["EmployeeStatus"].value_counts(dropna=False))

print()
print("KILÉPÉSI TÍPUSOK")
print(employees["TerminationType"].value_counts(dropna=False))

employees["HasExitDate"] = employees["ExitDate"].notna()

print()
print("=" * 60)
print("STÁTUSZ ÉS KILÉPÉSI DÁTUM KAPCSOLATA")
print(
    pd.crosstab(
        employees["EmployeeStatus"],
        employees["HasExitDate"],
        margins=True
    )
)

print()
print("KILÉPÉSI TÍPUS ÉS KILÉPÉSI DÁTUM KAPCSOLATA")
print(
    pd.crosstab(
        employees["TerminationType"],
        employees["HasExitDate"],
        margins=True
    )
)


start_dates = pd.to_datetime(
    employees["StartDate"],
    errors="coerce",
    format="mixed"
)
exit_dates = pd.to_datetime(
    employees["ExitDate"],
    errors="coerce",
    format="mixed"
)

print()
print("=" * 60)
print("DÁTUMOK ELLENŐRZÉSE")
print(f"Legkorábbi belépés: {start_dates.min()}")
print(f"Legkésőbbi belépés: {start_dates.max()}")
print(f"Legkorábbi kilépés: {exit_dates.min()}")
print(f"Legkésőbbi kilépés: {exit_dates.max()}")
print(f"Hibás belépési dátumok: {start_dates.isna().sum()}")
print(
    "Hibás, nem üres kilépési dátumok: "
    f"{(employees['ExitDate'].notna() & exit_dates.isna()).sum()}"
)
print(
    "Belépés előtti kilépések: "
    f"{((exit_dates < start_dates) & exit_dates.notna()).sum()}"
)
