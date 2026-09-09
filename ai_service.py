import json
import unicodedata
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

from insight_engine import get_discovery_catalog


MODEL_NAMES = (
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
)


def _normalized_text(text):
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )


def get_local_capability_answer(question):
    """Return quota-free answers for local capability and company-context questions."""
    text = _normalized_text(question)

    company_phrases = (
        "mivel foglalkozik a vallalat",
        "mi a vallalat profilja",
        "milyen ceg a vallalat",
        "mit csinal a vallalat",
        "mivel foglalkozik a ceg",
    )
    if any(phrase in text for phrase in company_phrases):
        organization_context = (
            load_catalogs()
            .get("catalog", {})
            .get("organization_context", {})
        )
        organization_type = organization_context.get(
            "organization_type",
            "fiktív ipari-technológiai nagyvállalat",
        )
        description = organization_context.get(
            "description",
            (
                "A vállalat ipari berendezéseket és intelligens műszaki "
                "megoldásokat gyárt. Saját termelési, értékesítési, "
                "informatikai, adat- és szoftverfejlesztési területekkel "
                "rendelkezik."
            ),
        ).strip()
        return (
            f"A demóban szereplő vállalat egy **{organization_type}**. "
            f"{description}"
        )

    capability_phrases = (
        "mit tudsz elemezni",
        "miket tudsz elemezni",
        "milyen ismerveket tudsz elemezni",
        "milyen jellemzoket tudsz elemezni",
        "milyen adatokat tudsz elemezni",
        "milyen mutatokat tudsz elemezni",
        "milyen bontasokat tudsz",
        "elemzesi lehetoseg",
        "mirol kerdezhetlek",
        "mit kerdezhetek",
        "milyen kerdeseket tehetek fel",
        "milyen elemzeseket tudsz kesziteni",
        "milyen idosorokat tudsz",
        "milyen trendeket tudsz",
        "milyen idobeli elemzeseket tudsz",
    )
    if not any(phrase in text for phrase in capability_phrases):
        return None

    if any(
        word in text
        for word in ("idosor", "trend", "idobeli")
    ):
        return (
            "**Jelenleg az alábbi idősorokat tudom megjeleníteni:**\n\n"
            "- **Munkaerő és fluktuáció:** létszám, belépők, kilépők és "
            "fluktuáció havi, negyedéves vagy éves bontásban.\n"
            "- **Engagement:** elkötelezettség, elégedettség, work–life "
            "balance, Top2Box-, Low2Box- és válaszadási arány felmérési "
            "hullámonként.\n"
            "- **Képzés:** részvétel, teljesítés, eredményesség, értékelés, "
            "relevancia és költség havi, negyedéves vagy éves bontásban.\n"
            "- **Csoportos összehasonlítás:** szervezeti, demográfiai, "
            "képzési vagy későbbi kilépés szerinti bontásban.\n"
            "- **Közös ábra:** több mutató és több csoport együttes "
            "megjelenítésével."
        )

    if any(word in text for word in ("kepzes", "training")):
        return (
            "**A képzéseket az alábbi szempontok szerint tudom elemezni:**\n\n"
            "- **Képzés jellemzői:** témakör, program, cél, megvalósítási "
            "mód, belső/külső besorolás és időszak.\n"
            "- **Részvétel és eredmény:** résztvevők, részvétel, teljesítés, "
            "félbehagyás, törlés és sikeres vizsga.\n"
            "- **Értékelés:** általános elégedettség, oktatói értékelés, "
            "munkaköri és személyes relevancia, digitális használhatóság.\n"
            "- **Költség:** teljes költség, résztvevőnkénti és sikeres "
            "teljesítésenkénti költség, program vagy szolgáltató szerint.\n"
            "- **Bontások:** szervezeti, demográfiai és képzési csoportok "
            "szerint, egy időszakban vagy idősorosan."
        )

    if any(
        word in text
        for word in (
            "engagement",
            "elkotelezettseg",
            "elegedettseg",
            "work-life",
            "work life",
            "wlb",
        )
    ):
        return (
            "**Az engagement-felméréseket az alábbi szempontok szerint "
            "tudom elemezni:**\n\n"
            "- **Mutatók:** elkötelezettség, munkahelyi elégedettség és "
            "work–life balance pontszám vagy 0–100-as index.\n"
            "- **Megoszlás:** Top2Box- és Low2Box-arányok, valamint "
            "válaszadási arány.\n"
            "- **Időbeli elemzés:** felmérési hullámok, változások és "
            "összevont időszaki eredmények.\n"
            "- **Bontások:** szervezeti, nemek szerinti, generációs és korcsoportos "
            "összehasonlítás.\n"
            "- **Kapcsolatok:** későbbi önkéntes kilépéssel és képzési "
            "jellemzőkkel való, nem oksági összevetés."
        )

    if any(
        word in text
        for word in (
            "munkaero",
            "munkavallalo",
            "letszam",
            "fluktuacio",
            "belepo",
            "kilepo",
        )
    ):
        return (
            "**A munkaerőt az alábbi szempontok szerint tudom elemezni:**\n\n"
            "- **Létszám:** nyitó-, záró- és napi átlagos létszám, valamint "
            "a nyitó- és zárólétszám egyszerű átlaga.\n"
            "- **Mozgás:** belépők, kilépők és létszámváltozás időszak szerint.\n"
            "- **Fluktuáció:** teljes, önkéntes, nem önkéntes, nyugdíjazási, "
            "gördülő 3 és 12 havi ráta.\n"
            "- **Bontások:** szervezeti egység, nem, generáció és korcsoport szerint.\n"
            "- **Időbeli elemzés:** egyedi időszakokra, trendként vagy "
            "csoportok összehasonlításával."
        )

    return (
        "**Három fő HR-területet tudok elemezni:**\n\n"
        "- **Munkaerő:** létszám, belépés, kilépés és fluktuáció.\n"
        "- **Engagement:** elkötelezettség, elégedettség, work–life balance "
        "és válaszadási arány.\n"
        "- **Képzés:** részvétel, teljesítés, értékelés, relevancia és költség.\n"
        "Az eredmények időszak, szervezeti és demográfiai csoportok szerint "
        "is összehasonlíthatók."
    )


def get_training_type_clarification(question):
    """Clarify the ambiguous Hungarian expression 'képzéstípus'."""
    text = _normalized_text(question)
    compact_text = "".join(
        character
        for character in text
        if character.isalnum()
    )
    if "kepzestipus" not in compact_text:
        return None

    explicit_meanings = (
        "temakor",
        "tema szerint",
        "kategori",
        "program",
        "megvalositasi mod",
        "delivery",
        "kepzesi cel",
        "trainingpurpose",
        "belso",
        "kulso",
        "internal",
        "external",
    )
    if any(meaning in text for meaning in explicit_meanings):
        return None

    relevance_is_ambiguous = (
        any(
            word in text
            for word in ("hasznossag", "relevancia")
        )
        and not any(
            meaning in text
            for meaning in (
                "munkakori",
                "szemelyes",
                "mindket",
                "mind a ket",
            )
        )
    )

    type_question = (
        "Mit értesz képzéstípus alatt: képzési témakört, konkrét "
        "programot, megvalósítási módot, képzési célt vagy belső/külső "
        "besorolást?"
    )
    if not relevance_is_ambiguous:
        return type_question

    return (
        f"{type_question} Továbbá a munkaköri relevanciát, a személyes "
        "relevanciát vagy mindkettőt szeretnéd látni?"
    )


class QuestionFilter(BaseModel):
    field: Literal[
        "DepartmentType",
        "GenderCode",
        "Generation",
        "AgeGroup",
        "TrainingCategory",
        "TrainingProgramName",
        "TrainingPurpose",
        "TrainingType",
        "DeliveryMode",
    ]
    value: str


class QuestionGrouping(BaseModel):
    field: Literal[
        "DepartmentType",
        "GenderCode",
        "Generation",
        "AgeGroup",
        "TrainingCategory",
        "TrainingProgramName",
        "TrainingPurpose",
        "TrainingType",
        "DeliveryMode",
    ]
    values: list[str] = Field(default_factory=list)


class ComparisonGroup(BaseModel):
    kind: Literal[
        "all_employees",
        "voluntary_exit_within_months_after_survey",
        "no_voluntary_exit_within_months_after_survey",
    ]
    label: str
    exit_window_months: int | None = Field(
        default=None,
        ge=1,
        le=60,
    )


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
    groupings: list[QuestionGrouping] = Field(
        default_factory=list
    )
    comparison_groups: list[ComparisonGroup] = Field(
        default_factory=list
    )
    output_type: Literal[
        "single_value",
        "comparison",
        "time_series",
        "grouped_table",
    ] = "single_value"
    chart_layout: Literal[
        "automatic",
        "combined",
        "separate",
    ] = "automatic"
    chart_type: Literal[
        "automatic",
        "table",
        "line",
        "bar",
        "pie",
        "stacked",
        "stacked_100",
    ] = "automatic"
    time_granularity: Literal[
        "automatic",
        "month",
        "quarter",
        "half_year",
        "year",
        "survey_wave",
    ] = "automatic"
    clarification_question: str | None = None
    reason: str


class FollowupAnalysisItem(BaseModel):
    analysis_id: Literal[
        "engagement_group_differences",
        "engagement_internal_correlations",
        "engagement_exit_association",
        "training_engagement_association",
        "training_group_differences",
        "turnover_group_differences",
    ]
    reason: str


class FollowupAnalysisPlan(BaseModel):
    analyses: list[FollowupAnalysisItem] = Field(
        default_factory=list,
        max_length=3,
    )
    overall_reason: str


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
    gender_field = next(
        field
        for field in employee_fields
        if field["name"] == "GenderCode"
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
    training_fields = catalogs["training"]["fields"]
    training_dimensions = {
        field["name"]: field["allowed_values"]
        for field in training_fields
        if field["name"] in {
            "TrainingCategory",
            "TrainingProgramName",
            "TrainingPurpose",
            "TrainingType",
            "DeliveryMode",
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
            "GenderCode": gender_field["allowed_values"],
            **demographic_filters,
            **training_dimensions,
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
- Ha a kérdés csoportok szerinti bontást kér, például „generációk szerint”,
  a dimenziót a groupings listában add vissza, ne a filters listában.
- A grouping field csak a filter_dimensions alatt felsorolt mező lehet.
- Ha nincs kért bontás, a groupings lista legyen üres.
- A „nemek szerint”, „nők és férfiak” vagy hasonló bontás a GenderCode mezőt jelenti.
- A „képzés típusa” vagy „képzéstípus” önmagában többértelmű. Ha a
  felhasználó nem pontosította a jelentését, kérdezd meg, hogy képzési
  témakört, konkrét programot, megvalósítási módot, képzési célt vagy
  belső/külső besorolást ért-e alatta. Ne válaszd automatikusan a TrainingType mezőt.
- A „képzési kategória” a TrainingCategory, a „képzési program” a
  TrainingProgramName, a „képzés célja” a TrainingPurpose, a „képzési forma”
  pedig a DeliveryMode mezőt jelenti.
- A „képzés hasznossága” vagy „relevanciája” önmagában nem egyértelmű:
  kérdezd meg, hogy a munkaköri relevanciaindexet, a személyes
  relevanciaindexet vagy mindkettőt szeretné-e látni.
- Munkaköri hasznosságnál az AverageJobRelevanceIndex, személyes fejlődésnél
  az AveragePersonalRelevanceIndex mutatót használd.
- Ha a felhasználó csak bizonyos kategóriákat akar összehasonlítani,
  a kiválasztott pontos kategóriaértékek kerüljenek a grouping values listájába.
- Ha egy dimenzió minden kategóriáját kéri, a values lista legyen üres.
- Az összehasonlítandó kategóriákat ne vond össze egyetlen filters szűrésbe.
- A teljes vállalat és egy felmérés után meghatározott időn belül önkéntesen
  kilépők összehasonlítását a comparison_groups listában add vissza.
- A teljes vállalat kind értéke all_employees legyen.
- A felmérés után önkéntesen kilépők kind értéke
  voluntary_exit_within_months_after_survey legyen, az időtávot pedig az
  exit_window_months mező tartalmazza.
- Az ugyanazon időtávon belül nem felmondók kind értéke
  no_voluntary_exit_within_months_after_survey legyen, ugyanazzal az
  exit_window_months értékkel.
- A „felmondók és nem felmondók” összehasonlításánál ne használd az
  all_employees csoportot: a két egymást kizáró kimeneti csoportot add vissza.
- A „felmondott” vagy „felmondók” önkéntes kilépést jelent, nem minden kilépést.
- A „kilépő” minden ExitDate értékkel rendelkező kilépési kategóriát jelent;
  nem azonos a kizárólag önkéntesen felmondókkal.
- Ha a kérdés a kilépők és a nem kilépők munkavállalónkénti utolsó
  engagement-, elégedettségi vagy work–life balance válaszát hasonlítja össze,
  használd rendre a LastEngagementIndexByEmploymentStatus,
  LastSatisfactionIndexByEmploymentStatus vagy
  LastWorkLifeBalanceIndexByEmploymentStatus mutatót. Az output_type comparison,
  a comparison_groups és groupings lista üres legyen.
- Ennél az elemzésnél az end_date a referencia-időpont. Ha nincs megadva,
  legyen 2026-06-30. A később kilépők a referencia-időpontban még az
  állományban lévők csoportjába tartoznak.
- Az „utolsó válasz” kilépőknél az ExitDate előtti legutolsó érvényes válasz,
  az akkor állományban lévőknél a referencia-időpontig adott legutolsó válasz.
- Ha a kilépés utáni követési időtáv hiányzik, kérj pontosítást.
- Ha nincs ilyen kimeneti csoport-összehasonlítás, a comparison_groups legyen üres.
- Ha a kérdés időbeli alakulásra, trendre vagy teljes idősorra kérdez,
  az output_type legyen time_series.
- Munkaerő-idősornál a HireCount és ExitCount együtt is kérhető. A „bármely
  okból kilépők” az ExitCount mutatót jelenti, nem csak az önkéntes kilépést.
- Ha a felhasználó „minden elérhető évre”, „az összes elérhető évre” vagy
  „a teljes elérhető időszakra” kér munkaerő-idősort, a time_granularity legyen
  year, az end_date legyen 2026-06-30, a start_date pedig maradhat üres; a
  helyi Python-motor az első rendelkezésre álló év elejétől számol.
- Munkaerő-idősornál az explicit havi, negyedéves vagy éves kérést mindig
  tartsd meg a time_granularity mezőben.
- Ha csak két időpont vagy időszak különbségét kéri, az output_type
  legyen comparison.
- Ha bontást vagy rangsort kér, az output_type legyen grouped_table.
- Egyetlen összesített eredménynél az output_type legyen single_value.
- Ha a kérdés kifejezetten táblázatot kér vagy azt mondja, hogy diagram nem
  szükséges, a chart_type legyen table.
- Két összesített csoportérték egyszerű összehasonlításánál a chart_type
  alapértelmezetten table legyen. Ha a felhasználó kifejezetten diagramot,
  grafikont vagy ábrát kér, válassz megfelelő diagramtípust, például bar értéket.
- Idősoros kérdésnél a diagram az alapértelmezett; table csak kifejezett kérésre legyen.
- Egy adott időpont munkavállalói összetételénél a ClosingHeadcount mutatót,
  a kért demográfiai vagy szervezeti grouping mezőt és a pie chart_type értéket használd.
- A munkavállalói összetétel időbeli változásánál a ClosingHeadcount mutatót,
  time_series output_type értéket és stacked_100 chart_type értéket használj.
- Ha az egyes csoportok abszolút létszámának időbeli változását kéri,
  a chart_type stacked legyen. Kördiagramot idősorra ne használj.
- Több, azonos időtengelyen értelmezhető mutató esetén a chart_layout legyen
  combined, ha a felhasználó egy közös ábrát kér. Máskor automatic.
- A chart_layout csak a megjelenítést szabályozza; emiatt mutatót vagy csoportot
  ne hagyj ki a tervből.
- Felmérési idősornál a time_granularity legyen survey_wave.
- Képzési idősornál az explicit havi, negyedéves vagy éves kérést add vissza.
  Ha a felhasználó nem adott gyakoriságot, legyen automatic.
- A féléves gyakoriság time_granularity értéke half_year legyen.
- A munkavállalói kategóriamegoszlás idősora lehet negyedéves, féléves vagy éves;
  az explicit gyakoriságot mindig tartsd meg.
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


def _get_analysis_rules(*rule_ids):
    rules = load_catalogs()["analysis_rules"]["analysis_rules"]
    selected = [
        rule
        for rule in rules
        if rule.get("id") in rule_ids
    ]
    return selected


def _generate_advisory_text(
    system_instruction,
    prompt,
    api_key,
    empty_response_message,
):
    client = genai.Client(api_key=api_key)
    response = None
    last_error = None

    for model_name in MODEL_NAMES:
        try:
            chat = client.chats.create(
                model=model_name,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2,
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

    if not response.text:
        raise ValueError(empty_response_message)

    return response.text.strip()


def interpret_results(question, result_payload, api_key):
    relevant_rules = _get_analysis_rules(
        "insight_layer_separation",
        "advisory_interpretation",
        "causal_inference_restriction",
        "uncertainty_and_generalization",
    )
    system_instruction = """
Te egy óvatos HR-insight elemző vagy.

A feladatod kizárólag a már kiszámított eredmények MÁSODIK rétegének
elkészítése: „Hogyan értelmezhető?”.

Szabályok:
- Ne számolj új eredményt, és ne találj ki adatot vagy szervezeti eseményt.
- Ne ismételd meg részletesen a „Mit mutatnak az adatok?” blokk számait.
- Lehetséges magyarázatokat és hipotéziseket adhatsz, de mindig bizonytalan,
  feltételes nyelven.
- Két jelenség együtt járását ne nevezd oknak, előjelnek vagy következménynek
  tényként. Ilyen értelmezés csak vizsgálandó hipotézisként jelenhet meg.
- Valódi előrejelző képességet csak külön prediktív vizsgálat alapján lehetne
  állítani; ennek hiányában ezt ne sugalljad.
- Oksági következtetést ne adj.
- Jelezd a lényeges bizonytalanságot, elemszám-, lefedettségi vagy
  adatértelmezési korlátot, ha a kapott eredmény ezt indokolja.
- Ne adj cselekvési javaslatot; az külön harmadik réteg.
- Legfeljebb 3 rövid felsoroláspontot írj magyarul.
"""
    prompt = (
        "FELHASZNÁLÓI KÉRDÉS:\n"
        + question
        + "\n\nMÁR KISZÁMÍTOTT AGGREGÁLT EREDMÉNYEK:\n"
        + json.dumps(
            result_payload,
            ensure_ascii=False,
            default=str,
        )
        + "\n\nALKALMAZANDÓ MÓDSZERTANI SZABÁLYOK:\n"
        + json.dumps(
            relevant_rules,
            ensure_ascii=False,
            default=str,
        )
    )
    return _generate_advisory_text(
        system_instruction,
        prompt,
        api_key,
        "Az AI nem adott szöveges értelmezést.",
    )



def plan_followup_analysis(
    question,
    result_payload,
    analysis_context,
    api_key,
):
    client = genai.Client(api_key=api_key)
    available_analyses = get_discovery_catalog()
    relevant_rules = _get_analysis_rules(
        "insight_layer_separation",
        "followup_discovery_analysis",
        "statistical_significance",
        "multiple_testing_correction",
        "minimum_sample_for_inference",
        "causal_inference_restriction",
    )
    system_instruction = """
Te egy HR-adatelemzési vizsgálattervező vagy.

A feladatod a már elkészült elemzés alapján legfeljebb 3 olyan TOVÁBBI
helyi Python-vizsgálat kiválasztása, amely valóban segíthet rejtett
összefüggést vagy fontos csoportkülönbséget feltárni.

Szabályok:
- Kizárólag az AVAILABLE_ANALYSES listában szereplő analysis_id-kat használd.
- Ne számolj eredményt és ne találj ki összefüggést.
- Csak olyan vizsgálatot válassz, amely érdemben kapcsolódik az eredeti
  kérdéshez vagy a már kiszámított eredményhez.
- Ne válassz minden lehetséges vizsgálatot automatikusan; 1–3 célzott irány legyen.
- A keresztadatállományos elemzés csak akkor választható, ha az valóban hozzáad
  az eredeti kérdés értelmezéséhez.
- A reason röviden mondja meg, mit érdemes ellenőrizni; eredményt ne előlegezzen meg.
- Ha egyik további vizsgálat sem indokolt, az analyses lista lehet üres.
- Oksági vagy prediktív állítást ne tegyél.
"""
    prompt = (
        "AVAILABLE_ANALYSES:\n"
        + json.dumps(available_analyses, ensure_ascii=False, default=str)
        + "\n\nFELHASZNÁLÓI KÉRDÉS:\n"
        + question
        + "\n\nMÁR KISZÁMÍTOTT EREDMÉNYEK:\n"
        + json.dumps(result_payload, ensure_ascii=False, default=str)
        + "\n\nELEMZÉSI KONTEXTUS:\n"
        + json.dumps(analysis_context, ensure_ascii=False, default=str)
        + "\n\nMÓDSZERTANI SZABÁLYOK:\n"
        + json.dumps(relevant_rules, ensure_ascii=False, default=str)
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
                    response_schema=FollowupAnalysisPlan,
                ),
            )
            response = chat.send_message(prompt)
            break
        except errors.ServerError as exc:
            last_error = exc
        except errors.ClientError as exc:
            status_code = getattr(exc, "code", getattr(exc, "status_code", None))
            if status_code == 429:
                last_error = exc
                continue
            raise

    if response is None:
        raise last_error
    if response.parsed is None:
        raise ValueError("Az AI nem adott értelmezhető további elemzési tervet.")
    return response.parsed


def interpret_followup_analysis(
    question,
    original_result_payload,
    followup_results,
    analysis_context,
    api_key,
):
    relevant_rules = _get_analysis_rules(
        "insight_layer_separation",
        "followup_discovery_analysis",
        "advisory_interpretation",
        "causal_inference_restriction",
        "uncertainty_and_generalization",
    )
    system_instruction = """
Te egy óvatos HR-insight elemző vagy.

A feladatod a HARMADIK réteg elkészítése: „További összefüggések keresése”.
A Python már lefuttatta a kiválasztott további vizsgálatokat. Te kizárólag ezek
tényleges eredményeit értelmezheted.

Szabályok:
- Ne számolj új eredményt és ne találj ki adatot.
- Először azt emeld ki, milyen statisztikailag ellenőrzött kapcsolat vagy
  csoportkülönbség találtatott.
- A corrected/adjusted p_value alapján tekints egy kapcsolatot
  statisztikailag igazoltnak; 0,05 felett ne nevezd annak.
- A hatásméretet vagy korrelációs együtthatót a p-érték mellett vedd figyelembe.
- Ha nincs statisztikailag igazolt új kapcsolat, ezt mondd ki röviden; ne gyárts
  hipotézist csak azért, hogy legyen.
- Hipotézist csak ténylegesen talált mintázatra építs, és jelöld külön
  „Hipotézis:” szóval.
- A hipotézis nem lehet oksági tény vagy bizonyított előrejelzés.
- A hipotézis után adhatsz célzott „További vizsgálati irány:” javaslatot,
  amely megmondja, hogyan lehetne a hipotézist ellenőrizni.
- Ne javasolj automatikusan HR-beavatkozást; előbb az összefüggés további
  ellenőrzése legyen a fókusz.
- Egyéni munkavállalóra ne tegyél következtetést.
- Legfeljebb 3 rövid pontot írj magyarul.
"""
    prompt = (
        "FELHASZNÁLÓI KÉRDÉS:\n"
        + question
        + "\n\nEREDETI KISZÁMÍTOTT EREDMÉNYEK:\n"
        + json.dumps(original_result_payload, ensure_ascii=False, default=str)
        + "\n\nPYTHONNAL LEFUTTATOTT TOVÁBBI VIZSGÁLATOK:\n"
        + json.dumps(followup_results, ensure_ascii=False, default=str)
        + "\n\nELEMZÉSI KONTEXTUS:\n"
        + json.dumps(analysis_context, ensure_ascii=False, default=str)
        + "\n\nMÓDSZERTANI SZABÁLYOK:\n"
        + json.dumps(relevant_rules, ensure_ascii=False, default=str)
    )
    return _generate_advisory_text(
        system_instruction,
        prompt,
        api_key,
        "Az AI nem adott további összefüggés-értelmezést.",
    )
