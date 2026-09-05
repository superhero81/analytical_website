from pathlib import Path
import math

import pandas as pd

from catalog_service import load_catalogs
from metric_engine import SUPPORTED_METRICS, calculate_metric


DATA_FOLDER = Path("data/processed")
START_DATE = "2026-01-01"
END_DATE = "2026-06-30"


def load_data():
    employees = pd.read_csv(
        DATA_FOLDER / "employee_data_clean.csv"
    )
    engagement = pd.read_csv(
        DATA_FOLDER
        / "employee_engagement_survey_data_clean.csv"
    )
    training = pd.read_csv(
        DATA_FOLDER
        / "training_and_development_data_clean.csv"
    )

    employees["StartDate"] = pd.to_datetime(
        employees["StartDate"],
        format="mixed"
    )
    employees["ExitDate"] = pd.to_datetime(
        employees["ExitDate"],
        errors="coerce",
        format="mixed"
    )

    return employees, engagement, training


def validate_value(metric_name, value):
    if isinstance(value, dict):
        if not value:
            return "A csoportos eredmény üres."
        if not all(
            isinstance(item, (int, float))
            and math.isfinite(float(item))
            for item in value.values()
        ):
            return "A csoportos eredmény hibás értéket tartalmaz."
        return None

    if not isinstance(value, (int, float)):
        return f"Nem numerikus eredmény: {type(value).__name__}"

    if not math.isfinite(float(value)):
        return "Az eredmény nem véges szám."

    if "Rate" in metric_name and not 0 <= value <= 100:
        return "A százalékos eredmény kívül esik a 0–100 tartományon."

    return None


def main():
    employees, engagement, training = load_data()
    catalogs = load_catalogs()
    catalog_metrics = {
        metric["name"]
        for metric in catalogs["metrics"]["metrics"]
    }

    errors = []
    passed = 0

    missing_from_engine = catalog_metrics - SUPPORTED_METRICS
    unknown_in_engine = SUPPORTED_METRICS - catalog_metrics

    if missing_from_engine:
        errors.append(
            "Hiányzik a motorból: "
            + ", ".join(sorted(missing_from_engine))
        )

    if unknown_in_engine:
        errors.append(
            "Nincs a katalógusban: "
            + ", ".join(sorted(unknown_in_engine))
        )

    print("=" * 60)
    print("METRIKAMOTOR ELLENŐRZÉSE")
    print("=" * 60)

    for metric_name in sorted(catalog_metrics):
        try:
            result = calculate_metric(
                metric_name,
                employees,
                START_DATE,
                END_DATE,
                engagement=engagement,
                training=training,
            )

            value_error = validate_value(
                metric_name,
                result.get("value")
            )

            if value_error:
                errors.append(
                    f"{metric_name}: {value_error}"
                )
                print(f"HIBA  {metric_name}: {value_error}")
            else:
                passed += 1
                print(f"OK    {metric_name}")

        except Exception as error:
            errors.append(f"{metric_name}: {error}")
            print(f"HIBA  {metric_name}: {error}")

    print("=" * 60)
    print(f"Sikeres metrikák: {passed}/{len(catalog_metrics)}")

    if errors:
        print(f"Hibák száma: {len(errors)}")
        raise SystemExit(1)

    print("A metrikamotor technikai ellenőrzése sikeres.")


if __name__ == "__main__":
    main()
