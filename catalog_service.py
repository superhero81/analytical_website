from functools import lru_cache
from pathlib import Path

import yaml


BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"


@lru_cache(maxsize=1)
def load_catalogs():
    catalogs = {}

    for path in sorted(CONFIG_DIR.glob("*.yaml")):
        with path.open(encoding="utf-8") as file:
            content = yaml.safe_load(file)

        if not isinstance(content, dict):
            raise ValueError(
                f"Hibás katalógusszerkezet: {path.name}"
            )

        catalogs[path.stem] = content

    return catalogs


@lru_cache(maxsize=1)
def get_metric_registry():
    catalogs = load_catalogs()

    return {
        metric["name"]: metric
        for metric in catalogs["metrics"]["metrics"]
    }


@lru_cache(maxsize=1)
def get_routing_registry():
    catalogs = load_catalogs()

    return {
        rule["id"]: rule
        for rule in catalogs[
            "question_routing"
        ]["routing_rules"]
    }


def get_metric(metric_name):
    metrics = get_metric_registry()

    if metric_name not in metrics:
        raise KeyError(
            f"Ismeretlen metrika: {metric_name}"
        )

    return metrics[metric_name]


def get_routing_rule(route_id):
    routes = get_routing_registry()

    if route_id not in routes:
        raise KeyError(
            f"Ismeretlen kérdésútvonal: {route_id}"
        )

    return routes[route_id]


def get_catalog_summary():
    catalogs = load_catalogs()

    return {
        "catalog_files": len(catalogs),
        "metrics": len(get_metric_registry()),
        "routing_rules": len(get_routing_registry()),
        "business_rules": len(
            catalogs["business_rules"]["business_rules"]
        ),
        "analysis_rules": len(
            catalogs["analysis_rules"]["analysis_rules"]
        ),
        "glossary_terms": len(
            catalogs["glossary"]["terms"]
        ),
    }