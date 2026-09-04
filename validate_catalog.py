from pathlib import Path

import pandas as pd
import yaml


CONFIG_DIR = Path("config")
DATA_DIR = Path("data/processed")

CATALOG_FILES = [
    "catalog.yaml",
    "employee.yaml",
    "engagement.yaml",
    "training.yaml",
    "metrics.yaml",
    "business_rules.yaml",
    "analysis_rules.yaml",
    "question_routing.yaml",
    "glossary.yaml",
]

DATASETS = {
    "employee.yaml": DATA_DIR / "employee_data_clean.csv",
    "engagement.yaml": (
        DATA_DIR
        / "employee_engagement_survey_data_clean.csv"
    ),
    "training.yaml": (
        DATA_DIR
        / "training_and_development_data_clean.csv"
    ),
}


errors = []
warnings = []


def load_yaml(path):
    try:
        with path.open(encoding="utf-8") as file:
            content = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        errors.append(f"Hibás YAML: {path} – {exc}")
        return {}

    if not isinstance(content, dict):
        errors.append(
            f"A fájl gyökere nem objektum: {path}"
        )
        return {}

    return content


def get_names(items):
    names = []

    if not isinstance(items, list):
        return names

    for item in items:
        if isinstance(item, dict) and item.get("name"):
            names.append(item["name"])

    return names


print("=" * 60)
print("AI-ADATKATALÓGUS ELLENŐRZÉSE")
print("=" * 60)

loaded_catalogs = {}

for filename in CATALOG_FILES:
    path = CONFIG_DIR / filename

    if not path.exists():
        errors.append(f"Hiányzó katalógusfájl: {path}")
        continue

    loaded_catalogs[filename] = load_yaml(path)

print(
    f"\nBetöltött katalógusfájlok: "
    f"{len(loaded_catalogs)}/{len(CATALOG_FILES)}"
)


print("\n" + "=" * 60)
print("ADATMEZŐK ELLENŐRZÉSE")
print("=" * 60)

for catalog_name, csv_path in DATASETS.items():
    catalog = loaded_catalogs.get(catalog_name, {})

    if not csv_path.exists():
        errors.append(f"Hiányzó adatfájl: {csv_path}")
        continue

    csv_columns = set(
        pd.read_csv(csv_path, nrows=0).columns
    )
    catalog_fields = set(
        get_names(catalog.get("fields", []))
    )

    missing_from_csv = sorted(
        catalog_fields - csv_columns
    )
    undocumented_columns = sorted(
        csv_columns - catalog_fields
    )

    print(f"\n{catalog_name}")
    print(f"  CSV-mezők: {len(csv_columns)}")
    print(f"  Dokumentált mezők: {len(catalog_fields)}")

    if missing_from_csv:
        errors.append(
            f"{catalog_name}: a CSV-ben nem létező mezők: "
            + ", ".join(missing_from_csv)
        )

    if undocumented_columns:
        warnings.append(
            f"{catalog_name}: nem dokumentált CSV-mezők: "
            + ", ".join(undocumented_columns)
        )


print("\n" + "=" * 60)
print("EGYEDI AZONOSÍTÓK ELLENŐRZÉSE")
print("=" * 60)

identifier_groups = {
    "metrics.yaml": "metrics",
    "business_rules.yaml": "business_rules",
    "analysis_rules.yaml": "analysis_rules",
    "question_routing.yaml": "routing_rules",
    "glossary.yaml": "terms",
}

for filename, section_name in identifier_groups.items():
    catalog = loaded_catalogs.get(filename, {})
    items = catalog.get(section_name, [])

    identifiers = []

    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue

            identifier = item.get("id") or item.get("name")

            if identifier:
                identifiers.append(identifier)

    duplicates = sorted({
        identifier
        for identifier in identifiers
        if identifiers.count(identifier) > 1
    })

    print(
        f"{filename}: "
        f"{len(identifiers)} azonosító"
    )

    if duplicates:
        errors.append(
            f"{filename}: duplikált azonosítók: "
            + ", ".join(duplicates)
        )


print("\n" + "=" * 60)
print("EREDMÉNY")
print("=" * 60)

if errors:
    print(f"\nHibák száma: {len(errors)}")

    for error in errors:
        print(f"  HIBA: {error}")
else:
    print("\nHiba nem található.")

if warnings:
    print(f"\nFigyelmeztetések száma: {len(warnings)}")

    for warning in warnings:
        print(f"  FIGYELMEZTETÉS: {warning}")
else:
    print("\nFigyelmeztetés nincs.")

if errors:
    raise SystemExit(1)

print("\nA katalógus technikai ellenőrzése sikeres.")