from pathlib import Path

import pandas as pd


DATA_FOLDER = Path("data/processed")

employee_file = DATA_FOLDER / "employee_data_clean.csv"
engagement_file = (
    DATA_FOLDER / "employee_engagement_survey_data_clean.csv"
)
training_file = (
    DATA_FOLDER / "training_and_development_data_clean.csv"
)

employees = pd.read_csv(employee_file)
engagement = pd.read_csv(engagement_file)
training = pd.read_csv(training_file)

print("Az új adatfájlok sikeresen betöltődtek.")
print(f"Munkavállalók: {len(employees):,} sor")
print(f"Engagement-válaszok: {len(engagement):,} sor")
print(f"Képzési rekordok: {len(training):,} sor")


employee_ids = set(employees["EmpID"])
engagement_employee_ids = set(engagement["EmpID"])
training_employee_ids = set(training["EmpID"])

duplicate_employee_ids = employees["EmpID"].duplicated().sum()
duplicate_response_ids = engagement["ResponseID"].duplicated().sum()
duplicate_training_ids = training[
    "TrainingRecordID"
].duplicated().sum()

unknown_engagement_ids = (
    engagement_employee_ids - employee_ids
)
unknown_training_ids = (
    training_employee_ids - employee_ids
)

print()
print("AZONOSÍTÓK ÉS KAPCSOLATOK")
print(f"Duplikált EmpID: {duplicate_employee_ids}")
print(f"Duplikált ResponseID: {duplicate_response_ids}")
print(
    f"Duplikált TrainingRecordID: {duplicate_training_ids}"
)
print(
    "Ismeretlen EmpID az engagement-adatokban: "
    f"{len(unknown_engagement_ids)}"
)
print(
    "Ismeretlen EmpID a képzési adatokban: "
    f"{len(unknown_training_ids)}"
)

employees["StartDate"] = pd.to_datetime(
    employees["StartDate"],
    errors="coerce",
    format="mixed"
)
employees["ExitDate"] = pd.to_datetime(
    employees["ExitDate"],
    errors="coerce",
    format="mixed"
)
engagement["SurveyDate"] = pd.to_datetime(
    engagement["SurveyDate"],
    errors="coerce",
    format="mixed"
)
training["TrainingDate"] = pd.to_datetime(
    training["TrainingDate"],
    errors="coerce",
    format="mixed"
)

exit_before_start = (
    employees["ExitDate"].notna()
    & (employees["ExitDate"] < employees["StartDate"])
).sum()

engagement_dates = engagement.merge(
    employees[["EmpID", "StartDate", "ExitDate"]],
    on="EmpID",
    how="left"
)

survey_before_start = (
    engagement_dates["SurveyDate"]
    < engagement_dates["StartDate"]
).sum()

survey_after_exit = (
    engagement_dates["ExitDate"].notna()
    & (
        engagement_dates["SurveyDate"]
        > engagement_dates["ExitDate"]
    )
).sum()

training_dates = training.merge(
    employees[["EmpID", "StartDate", "ExitDate"]],
    on="EmpID",
    how="left"
)

training_before_start = (
    training_dates["TrainingDate"]
    < training_dates["StartDate"]
).sum()

training_after_exit = (
    training_dates["ExitDate"].notna()
    & (
        training_dates["TrainingDate"]
        > training_dates["ExitDate"]
    )
).sum()

print()
print("DÁTUMOK ÉS FOGLALKOZTATÁSI IDŐSZAKOK")
print(
    "Kilépés a belépés előtt: "
    f"{exit_before_start}"
)
print(
    "Felmérés a belépés előtt: "
    f"{survey_before_start}"
)
print(
    "Felmérés a kilépés után: "
    f"{survey_after_exit}"
)
print(
    "Képzés a belépés előtt: "
    f"{training_before_start}"
)
print(
    "Képzés a kilépés után: "
    f"{training_after_exit}"
)

