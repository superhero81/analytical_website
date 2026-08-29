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


print()
print("ADATÁLLOMÁNYOK IDŐBELI LEFEDETTSÉGE")
print(
    "Legkorábbi belépés: "
    f"{employees['StartDate'].min().date()}"
)
print(
    "Legkésőbbi belépés: "
    f"{employees['StartDate'].max().date()}"
)
print(
    "Legkésőbbi kilépés: "
    f"{employees['ExitDate'].max().date()}"
)
print(
    "Legkorábbi felmérés: "
    f"{engagement['SurveyDate'].min().date()}"
)
print(
    "Legkésőbbi felmérés: "
    f"{engagement['SurveyDate'].max().date()}"
)
print(
    "Legkorábbi képzés: "
    f"{training['TrainingDate'].min().date()}"
)
print(
    "Legkésőbbi képzés: "
    f"{training['TrainingDate'].max().date()}"
)

print()
print("MUNKAVÁLLALÓI STÁTUSZOK")
print(employees["EmployeeStatus"].value_counts())

reference_date = pd.Timestamp("2026-07-01")
period_start = reference_date - pd.DateOffset(years=1)

headcount_start = (
    (employees["StartDate"] <= period_start)
    & (
        employees["ExitDate"].isna()
        | (employees["ExitDate"] > period_start)
    )
).sum()

headcount_end = (
    (employees["StartDate"] <= reference_date)
    & (
        employees["ExitDate"].isna()
        | (employees["ExitDate"] > reference_date)
    )
).sum()

average_headcount = (
    headcount_start + headcount_end
) / 2

exits_12m = (
    (employees["ExitDate"] > period_start)
    & (employees["ExitDate"] <= reference_date)
).sum()

turnover_rate_12m = (
    exits_12m / average_headcount * 100
)

voluntary_exits_12m = (
    (employees["ExitDate"] > period_start)
    & (employees["ExitDate"] <= reference_date)
    & (
        employees["EmployeeStatus"]
        == "Voluntarily Terminated"
    )
).sum()

voluntary_turnover_rate_12m = (
    voluntary_exits_12m
    / average_headcount
    * 100
)

print()
print("GÖRDÜLŐ 12 HAVI FLUKTUÁCIÓ")
print(
    f"Időszak: {period_start.date()} – "
    f"{reference_date.date()}"
)
print(f"Időszak eleji állomány: {headcount_start}")
print(f"Időszak végi állomány: {headcount_end}")
print(f"Átlagos állomány: {average_headcount:.1f}")
print(f"Kilépők száma: {exits_12m}")
print(f"Teljes fluktuáció: {turnover_rate_12m:.1f}%")
print(
    f"Önkéntes kilépők száma: "
    f"{voluntary_exits_12m}"
)
print(
    "Önkéntes fluktuáció: "
    f"{voluntary_turnover_rate_12m:.1f}%"
)

engagement["SurveyLaunchDate"] = pd.to_datetime(
    engagement["SurveyLaunchDate"],
    errors="coerce",
    format="mixed"
)

latest_launch_date = engagement[
    "SurveyLaunchDate"
].max()

latest_wave = engagement[
    engagement["SurveyLaunchDate"]
    == latest_launch_date
].copy()

latest_wave_id = latest_wave[
    "SurveyWaveID"
].iloc[0]

eligible_employees = (
    (employees["StartDate"] <= latest_launch_date)
    & (
        employees["ExitDate"].isna()
        | (
            employees["ExitDate"]
            >= latest_launch_date
        )
    )
).sum()

respondents = latest_wave["EmpID"].nunique()
response_rate = (
    respondents / eligible_employees * 100
)

print()
print("LEGFRISSEBB ENGAGEMENT-HULLÁM")
print(f"Hullám: {latest_wave_id}")
print(
    "Indulás dátuma: "
    f"{latest_launch_date.date()}"
)
print(f"Válaszadók száma: {respondents}")
print(f"Válaszadási arány: {response_rate:.1f}%")
print(
    "Engagement-átlag: "
    f"{latest_wave['EngagementScore'].mean():.2f}"
)
print(
    "Elégedettségi átlag: "
    f"{latest_wave['SatisfactionScore'].mean():.2f}"
)
print(
    "Work–life balance átlag: "
    f"{latest_wave['WorkLifeBalanceScore'].mean():.2f}"
)

print()
print("KÉPZÉSI KATEGÓRIÁK")
print()
print("CompletionStatus:")
print(training["CompletionStatus"].value_counts())

print()
print("TrainingResult:")
print(training["TrainingResult"].value_counts())

print()
print("DeliveryMode:")
print(training["DeliveryMode"].value_counts())


training_period_start = pd.Timestamp("2026-01-01")
training_period_end = pd.Timestamp("2026-06-30")

training_h1 = training[
    (
        training["TrainingDate"]
        >= training_period_start
    )
    & (
        training["TrainingDate"]
        <= training_period_end
    )
].copy()

completed_trainings = (
    training_h1["CompletionStatus"]
    == "Completed"
).sum()

incomplete_trainings = (
    training_h1["CompletionStatus"]
    == "Incomplete"
).sum()

cancelled_trainings = (
    training_h1["CompletionStatus"]
    == "Cancelled"
).sum()

started_trainings = (
    completed_trainings + incomplete_trainings
)

completion_rate = (
    completed_trainings
    / started_trainings
    * 100
)

evaluated_trainings = training_h1[
    training_h1["TrainingResult"].isin(
        ["Passed", "Failed"]
    )
]

pass_rate = (
    (
        evaluated_trainings["TrainingResult"]
        == "Passed"
    ).mean()
    * 100
)

trained_employees = training_h1[
    "EmpID"
].nunique()

eligible_h1 = (
    (employees["StartDate"] <= training_period_end)
    & (
        employees["ExitDate"].isna()
        | (
            employees["ExitDate"]
            >= training_period_start
        )
    )
).sum()

training_participation_rate = (
    trained_employees / eligible_h1 * 100
)

print()
print("2026 ELSŐ FÉLÉVI KÉPZÉSI MUTATÓK")
print(f"Képzési rekordok: {len(training_h1)}")
print(f"Képzésben részt vevők: {trained_employees}")
print(
    "Képzési részvételi arány: "
    f"{training_participation_rate:.1f}%"
)
print(f"Teljesített képzések: {completed_trainings}")
print(f"Nem teljesített képzések: {incomplete_trainings}")
print(f"Törölt képzések: {cancelled_trainings}")
print(
    "Teljesítési arány: "
    f"{completion_rate:.1f}%"
)
print(f"Sikeres vizsga aránya: {pass_rate:.1f}%")


