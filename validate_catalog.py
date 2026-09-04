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
print("METRIKAHIVATKOZÁSOK ELLENŐRZÉSE")
print("=" * 60)


def collect_strings(value):
    if isinstance(value, str):
        return [value]

    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(collect_strings(item))
        return result

    if isinstance(value, dict):
        result = []
        for item in value.values():
            result.extend(collect_strings(item))
        return result

    return []


metric_reference_keys = {
    "metric_selection",
    "raw_score_metrics",
    "change_metrics",
    "pooled_metrics",
    "index_metrics",
    "primary_metrics",
}

known_metrics = set(
    get_names(
        loaded_catalogs
        .get("metrics.yaml", {})
        .get("metrics", [])
    )
)

routing_rules = (
    loaded_catalogs
    .get("question_routing.yaml", {})
    .get("routing_rules", [])
)

referenced_metrics = set()

for rule in routing_rules:
    if not isinstance(rule, dict):
        continue

    for key in metric_reference_keys:
        if key in rule:
            referenced_metrics.update(
                collect_strings(rule[key])
            )

unknown_metrics = sorted(
    referenced_metrics - known_metrics
)

print(f"Hivatkozott metrikák: {len(referenced_metrics)}")
print(f"Ismert metrikák: {len(known_metrics)}")

if unknown_metrics:
    errors.append(
        "A kérdésirányítás ismeretlen metrikákra hivatkozik: "
        + ", ".join(unknown_metrics)
    )


print("\n" + "=" * 60)
print("ADATKÉSZLET-HIVATKOZÁSOK ELLENŐRZÉSE")
print("=" * 60)

main_catalog = loaded_catalogs.get("catalog.yaml", {})
dataset_entries = main_catalog.get("datasets", [])

known_datasets = {
    item["id"]
    for item in dataset_entries
    if isinstance(item, dict) and item.get("id")
}

referenced_datasets = set()


def find_dataset_references(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "source_datasets":
                referenced_datasets.update(
                    collect_strings(item)
                )
            elif (
                key == "dataset"
                and isinstance(item, str)
                and item in {"employee", "engagement", "training"}
            ):
                referenced_datasets.add(item)

            find_dataset_references(item)

    elif isinstance(value, list):
        for item in value:
            find_dataset_references(item)


for catalog in loaded_catalogs.values():
    find_dataset_references(catalog)

unknown_datasets = sorted(
    referenced_datasets - known_datasets
)

print(f"Ismert adatkészletek: {len(known_datasets)}")
print(f"Hivatkozott adatkészletek: {len(referenced_datasets)}")

if unknown_datasets:
    errors.append(
        "Ismeretlen adatkészlet-hivatkozások: "
        + ", ".join(unknown_datasets)
    )

for dataset in dataset_entries:
    if not isinstance(dataset, dict):
        continue

    detail_catalog = dataset.get("detail_catalog")
    data_file = dataset.get("file")

    if detail_catalog and not (
        CONFIG_DIR / detail_catalog
    ).exists():
        errors.append(
            f"Hiányzó részletes katalógus: {detail_catalog}"
        )

    if data_file and not (
        DATA_DIR / data_file
    ).exists():
        errors.append(
            f"Hiányzó adatfájl: {data_file}"
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