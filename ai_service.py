import json
from typing import Literal

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field

from catalog_service import (
    get_metric_registry,
    get_routing_registry,
    load_catalogs,
)
from datetime import date


MODEL_NAMES = (
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
)


class QuestionFilter(BaseModel):
    field: Literal[
        "DepartmentType",
        "Generation",
        "AgeGroup",
    ]
    value: str


class QuestionPlan(BaseModel):
    status: Literal[
        "answerable",
        "clarification_needed",
        "out_of_scope",
    ]
    route_id: str | None = None
    metric_names: list[str] = Field(
        default_factory=list
    )
    start_date: date | None = None
    end_date: date | None = None
    filters: list[QuestionFilter] = Field(
        default_factory=list
    )
    clarification_question: str | None = None
    reason: str


def build_routing_context():
    routes = get_routing_registry()
    metrics = get_metric_registry()
    catalogs = load_catalogs()
    employee_fields = catalogs["employee"]["fields"]
    department_field = next(
        field
        for field in employee_fields
        if field["name"] == "DepartmentType"
    )
    derived_dimensions = catalogs["employee"].get(
        "derived_dimensions",
        []
    )
    demographic_filters = {
        dimension["name"]: [
            category["label"]
            for category in dimension["categories"]
        ]
        for dimension in derived_dimensions
        if dimension["name"] in {
            "Generation",
            "AgeGroup",
        }
    }

    return {
        "official_cutoff_date": "2026-06-30",
        "available_routes": list(routes.values()),
        "available_metrics": [
            {
                "name": metric["name"],
                "label": metric["label"],
                "description": metric.get(
                    "description",
                    metric.get("formula", "")
                ),
            }
            for metric in metrics.values()
        ],
        "filter_dimensions": {
            "DepartmentType": department_field[
                "allowed_values"
            ],
            **demographic_filters,
        },
    }


def plan_question(question, api_key):
    client = genai.Client(api_key=api_key)

    system_instruction = """
Te egy HR-adatelemzési kérdéstervező vagy.

Feladatod kizárólag a felhasználói kérdés besorolása.
Ne számolj eredményt, és ne találj ki adatot.

Szabályok:
- Csak a megadott útvonal- és metrikaazonosítókat használd.
- Ha a kérdés megválaszolható, a status legyen answerable.
- Ha lényeges időszak, mutató vagy összehasonlítási alap
  hiányzik, a status legyen clarification_needed.
- Ilyenkor egyetlen rövid magyar pontosító kérdést adj.
- Ha a szükséges adat nem áll rendelkezésre, a status
  legyen out_of_scope.
- A reason rövid, magyar nyelvű indoklás legyen.
- Az explicit időszakot start_date és end_date mezőkkel add meg,
  ISO YYYY-MM-DD formátumban.
- Egy konkrét napnál a start_date és end_date legyen azonos.
- A kérdésben megadott szervezeti vagy demográfiai szűréseket a filters
  listában add vissza.
- Csak a filter_dimensions alatt felsorolt mezők és pontos kategóriaértékek
  használhatók.
- Egy mezőhöz több kért kategória esetén külön listaelemeket adj vissza.
- Ha nincs szűrés a kérdésben, a filters lista legyen üres.
- A „2026 első féléve” időszaka 2026-01-01–2026-06-30.
- Hiányzó időszakot csak a katalógus kifejezett
  alapértelmezési szabálya alapján tölts ki.
"""

    context = build_routing_context()

    prompt = (
        "ADATKATALÓGUS:\n"
        + json.dumps(
            context,
            ensure_ascii=False,
            default=str,
        )
        + "\n\nFELHASZNÁLÓI KÉRDÉS:\n"
        + question
    )

    response = None
    last_error = None

    for model_name in MODEL_NAMES:
        try:
            chat = client.chats.create(
                model=model_name,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0,
                    response_mime_type="application/json",
                    response_schema=QuestionPlan,
                ),
            )

            response = chat.send_message(prompt)
            break

        except errors.ServerError as exc:
            last_error = exc

        except errors.ClientError as exc:
            status_code = getattr(
                exc,
                "code",
                getattr(exc, "status_code", None),
            )

            if status_code == 429:
                last_error = exc
                continue

            raise

    if response is None:
        raise last_error

    if response.parsed is None:
        raise ValueError(
            "Az AI nem adott értelmezhető kérdéstervet."
        )

    return response.parsed
