import math
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats


MIN_GROUP_SIZE = 4
MIN_INFERENCE_GROUP = 20

DISCOVERY_ANALYSES = {
    "engagement_group_differences": {
        "label": "Engagement-mutatók rejtett csoportkülönbségei",
        "description": (
            "A legutóbbi elérhető engagement-hullámban szervezeti, nemi, "
            "generációs és korcsoportos eltéréseket keres az engagement, "
            "elégedettség és work–life balance mutatókban."
        ),
    },
    "engagement_internal_correlations": {
        "label": "Engagement-dimenziók együttjárása",
        "description": (
            "A legutóbbi elérhető hullámban az engagement, elégedettség és "
            "work–life balance közötti Spearman-korrelációkat vizsgálja."
        ),
    },
    "engagement_exit_association": {
        "label": "Engagement és későbbi önkéntes kilépés kapcsolata",
        "description": (
            "Munkavállalónként egy, teljes 12 havi utánkövetéssel rendelkező "
            "engagement-választ használ, és összeveti a később önkéntesen "
            "kilépők és nem kilépők mutatóit."
        ),
    },
    "training_engagement_association": {
        "label": "Képzési aktivitás és engagement kapcsolata",
        "description": (
            "Munkavállalói szinten megvizsgálja, együtt jár-e a megelőző "
            "12 hónap képzési aktivitása a legutóbbi engagement-válasszal."
        ),
    },
    "training_group_differences": {
        "label": "Képzési visszajelzések rejtett csoportkülönbségei",
        "description": (
            "A vizsgálati záródátumot megelőző 12 hónap képzési visszajelzéseit "
            "munkavállalói szintre aggregálja, majd szervezeti és demográfiai "
            "különbségeket keres."
        ),
    },
    "turnover_group_differences": {
        "label": "Önkéntes kilépés és munkavállalói csoportok kapcsolata",
        "description": (
            "A záródátumot megelőző 12 hónap nyitóállományában vizsgálja, "
            "eltér-e az önkéntes kilépés előfordulása szervezeti vagy "
            "demográfiai csoportok között."
        ),
    },
}


def get_discovery_catalog():
    return [
        {
            "analysis_id": analysis_id,
            "label": definition["label"],
            "description": definition["description"],
        }
        for analysis_id, definition in DISCOVERY_ANALYSES.items()
    ]


def _to_timestamp(value, default=None):
    if value is None:
        return pd.Timestamp(default) if default is not None else None
    return pd.Timestamp(value)


def _add_demographic_dimensions(employee_data, reference_date):
    result = employee_data.copy()
    reference_date = pd.Timestamp(reference_date)
    birth_date = pd.to_datetime(result["DOB"], errors="coerce", format="mixed")
    birth_year = birth_date.dt.year

    result["Generation"] = pd.cut(
        birth_year,
        bins=[0, 1945, 1964, 1980, 1996, 2012],
        labels=[
            "Silent Generation (1945 vagy korábban)",
            "Baby Boomer (1946–1964)",
            "Generation X (1965–1980)",
            "Generation Y (Millennial, 1981–1996)",
            "Generation Z (1997–2012)",
        ],
    ).astype("string")

    age = (
        reference_date.year
        - birth_date.dt.year
        - (
            (birth_date.dt.month > reference_date.month)
            | (
                (birth_date.dt.month == reference_date.month)
                & (birth_date.dt.day > reference_date.day)
            )
        ).astype("Int64")
    )
    result["AgeGroup"] = pd.cut(
        age,
        bins=[-1, 29, 44, 59, float("inf")],
        labels=[
            "29 éves vagy fiatalabb",
            "30–44 éves",
            "45–59 éves",
            "60 éves vagy idősebb",
        ],
    ).astype("string")
    return result


def _bh_adjust(p_values):
    if not p_values:
        return []
    indexed = sorted(enumerate(p_values), key=lambda item: item[1])
    n = len(indexed)
    adjusted_sorted = [0.0] * n
    previous = 1.0
    for reverse_rank, (original_index, p_value) in enumerate(reversed(indexed), start=1):
        rank = n - reverse_rank + 1
        adjusted = min(previous, float(p_value) * n / rank)
        previous = adjusted
        adjusted_sorted[rank - 1] = adjusted
    result = [0.0] * n
    for rank_index, (original_index, _) in enumerate(indexed):
        result[original_index] = min(1.0, adjusted_sorted[rank_index])
    return result


def _holm_adjust(p_values):
    if not p_values:
        return []
    indexed = sorted(enumerate(p_values), key=lambda item: item[1])
    n = len(indexed)
    adjusted_sorted = []
    running = 0.0
    for rank, (_, p_value) in enumerate(indexed):
        adjusted = min(1.0, (n - rank) * float(p_value))
        running = max(running, adjusted)
        adjusted_sorted.append(running)
    result = [0.0] * n
    for rank, (original_index, _) in enumerate(indexed):
        result[original_index] = adjusted_sorted[rank]
    return result


def _safe_float(value):
    if value is None or not np.isfinite(value):
        return None
    return float(value)


def _rank_biserial_from_u(u_stat, n1, n2):
    if n1 == 0 or n2 == 0:
        return None
    return 2 * float(u_stat) / (n1 * n2) - 1


def _epsilon_squared(h_stat, group_count, n_total):
    denominator = n_total - group_count
    if denominator <= 0:
        return None
    return max(0.0, (float(h_stat) - group_count + 1) / denominator)


def _cramers_v(chi2, n, rows, cols):
    denominator = n * min(rows - 1, cols - 1)
    if denominator <= 0:
        return None
    return math.sqrt(float(chi2) / denominator)


def _hedges_g(group_a, group_b):
    a = np.asarray(group_a, dtype=float)
    b = np.asarray(group_b, dtype=float)
    n1, n2 = len(a), len(b)
    if n1 < 2 or n2 < 2:
        return None
    s1 = np.var(a, ddof=1)
    s2 = np.var(b, ddof=1)
    pooled_df = n1 + n2 - 2
    if pooled_df <= 0:
        return None
    pooled = math.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / pooled_df)
    if pooled == 0:
        return 0.0
    d = (np.mean(a) - np.mean(b)) / pooled
    correction = 1 - 3 / (4 * (n1 + n2) - 9)
    return float(d * correction)


def _mean_difference_ci(group_a, group_b, confidence=0.95):
    a = np.asarray(group_a, dtype=float)
    b = np.asarray(group_b, dtype=float)
    n1, n2 = len(a), len(b)
    if n1 < 2 or n2 < 2:
        return None, None
    mean_diff = np.mean(a) - np.mean(b)
    v1 = np.var(a, ddof=1) / n1
    v2 = np.var(b, ddof=1) / n2
    se = math.sqrt(v1 + v2)
    if se == 0:
        return float(mean_diff), float(mean_diff)
    df_num = (v1 + v2) ** 2
    df_den = (v1 ** 2) / (n1 - 1) + (v2 ** 2) / (n2 - 1)
    df = df_num / df_den if df_den > 0 else n1 + n2 - 2
    critical = stats.t.ppf((1 + confidence) / 2, df)
    return float(mean_diff - critical * se), float(mean_diff + critical * se)


def _latest_wave(engagement, end_date):
    data = engagement.copy()
    data["SurveyLaunchDate"] = pd.to_datetime(data["SurveyLaunchDate"], errors="coerce")
    data = data[data["SurveyLaunchDate"] <= pd.Timestamp(end_date)]
    if data.empty:
        return None, None
    launch_date = data["SurveyLaunchDate"].max()
    return data[data["SurveyLaunchDate"] == launch_date].copy(), launch_date


def _group_test(values, groups):
    frame = pd.DataFrame({"value": values, "group": groups}).dropna()
    grouped = [
        group["value"].astype(float).to_numpy()
        for _, group in frame.groupby("group", observed=True)
        if len(group) >= MIN_INFERENCE_GROUP
    ]
    labels = [
        str(name)
        for name, group in frame.groupby("group", observed=True)
        if len(group) >= MIN_INFERENCE_GROUP
    ]
    if len(grouped) < 2:
        return None

    summary = {
        label: {
            "n": int(len(values_array)),
            "mean": float(np.mean(values_array)),
            "median": float(np.median(values_array)),
        }
        for label, values_array in zip(labels, grouped)
    }

    if len(grouped) == 2:
        test = stats.mannwhitneyu(grouped[0], grouped[1], alternative="two-sided")
        effect = _rank_biserial_from_u(test.statistic, len(grouped[0]), len(grouped[1]))
        method = "Mann–Whitney-próba"
    else:
        test = stats.kruskal(*grouped)
        effect = _epsilon_squared(test.statistic, len(grouped), sum(len(g) for g in grouped))
        method = "Kruskal–Wallis-próba"

    means = {label: values["mean"] for label, values in summary.items()}
    highest = max(means, key=means.get)
    lowest = min(means, key=means.get)
    return {
        "method": method,
        "p_value": float(test.pvalue),
        "effect_size": _safe_float(effect),
        "groups": summary,
        "highest_group": highest,
        "lowest_group": lowest,
        "difference_high_low": float(means[highest] - means[lowest]),
        "n": int(sum(item["n"] for item in summary.values())),
    }


def _engagement_group_differences(employees, engagement, end_date):
    wave, launch_date = _latest_wave(engagement, end_date)
    if wave is None:
        return _empty_result("engagement_group_differences", "Nincs elérhető engagement-hullám.")

    emp = _add_demographic_dimensions(employees, launch_date)
    merged = wave.merge(
        emp[["EmpID", "DepartmentType", "GenderCode", "Generation", "AgeGroup"]],
        on="EmpID",
        how="inner",
    )
    score_fields = {
        "EngagementScore": "Elkötelezettségi index",
        "SatisfactionScore": "Elégedettségi index",
        "WorkLifeBalanceScore": "Work–life balance index",
    }
    dimensions = ["DepartmentType", "GenderCode", "Generation", "AgeGroup"]
    findings = []
    for field, label in score_fields.items():
        index_values = (merged[field] - 1) * 25
        for dimension in dimensions:
            test_result = _group_test(index_values, merged[dimension])
            if not test_result:
                continue
            findings.append({
                "relationship": f"{label} × {dimension}",
                "metric": label,
                "dimension": dimension,
                **test_result,
            })

    _apply_adjustment(findings, method="bh")
    result = _result(
        "engagement_group_differences",
        findings,
        scope=f"Legutóbbi hullám: {wave['SurveyWaveID'].iloc[0]} ({launch_date.date().isoformat()})",
        correction="Benjamini–Hochberg FDR-korrekció",
    )
    result["limitations"] = [
        "A történeti szervezeti bontás a munkavállalói törzs aktuális vagy utolsó ismert DepartmentType értékét használja; szervezeti változástörténet nincs."
    ]
    return result


def _engagement_internal_correlations(engagement, end_date):
    wave, launch_date = _latest_wave(engagement, end_date)
    if wave is None:
        return _empty_result("engagement_internal_correlations", "Nincs elérhető engagement-hullám.")
    fields = {
        "EngagementScore": "Elkötelezettség",
        "SatisfactionScore": "Elégedettség",
        "WorkLifeBalanceScore": "Work–life balance",
    }
    findings = []
    for (field_a, label_a), (field_b, label_b) in combinations(fields.items(), 2):
        pairs = wave[[field_a, field_b]].dropna()
        if len(pairs) < MIN_INFERENCE_GROUP:
            continue
        test = stats.spearmanr(pairs[field_a], pairs[field_b])
        findings.append({
            "relationship": f"{label_a} × {label_b}",
            "method": "Spearman-féle rangkorreláció",
            "coefficient": _safe_float(test.statistic),
            "p_value": float(test.pvalue),
            "n": int(len(pairs)),
        })
    _apply_adjustment(findings, method="bh")
    return _result(
        "engagement_internal_correlations",
        findings,
        scope=f"Legutóbbi hullám: {wave['SurveyWaveID'].iloc[0]} ({launch_date.date().isoformat()})",
        correction="Benjamini–Hochberg FDR-korrekció",
    )


def _engagement_exit_association(employees, engagement, official_cutoff_date):
    cutoff = pd.Timestamp(official_cutoff_date)
    latest_eligible_response_date = cutoff - pd.DateOffset(months=12)
    responses = engagement.copy()
    responses["SurveyDate"] = pd.to_datetime(responses["SurveyDate"], errors="coerce")
    responses = responses[responses["SurveyDate"] <= latest_eligible_response_date].copy()
    if responses.empty:
        return _empty_result("engagement_exit_association", "Nincs teljes 12 havi utánkövetéssel rendelkező engagement-válasz.")

    responses = responses.sort_values(["EmpID", "SurveyDate"]).drop_duplicates("EmpID", keep="last")
    emp = employees[["EmpID", "ExitDate", "EmployeeStatus"]].copy()
    emp["ExitDate"] = pd.to_datetime(emp["ExitDate"], errors="coerce")
    data = responses.merge(emp, on="EmpID", how="inner")
    followup_end = data["SurveyDate"] + pd.DateOffset(months=12)
    data["LaterVoluntaryExit"] = (
        (data["EmployeeStatus"] == "Voluntarily Terminated")
        & data["ExitDate"].notna()
        & (data["ExitDate"] > data["SurveyDate"])
        & (data["ExitDate"] <= followup_end)
    )

    fields = {
        "EngagementScore": "Elkötelezettségi index",
        "SatisfactionScore": "Elégedettségi index",
        "WorkLifeBalanceScore": "Work–life balance index",
    }
    findings = []
    for field, label in fields.items():
        valid = data[[field, "LaterVoluntaryExit"]].dropna()
        exited = ((valid.loc[valid["LaterVoluntaryExit"], field] - 1) * 25).astype(float)
        stayed = ((valid.loc[~valid["LaterVoluntaryExit"], field] - 1) * 25).astype(float)
        if len(exited) < MIN_INFERENCE_GROUP or len(stayed) < MIN_INFERENCE_GROUP:
            continue
        test = stats.mannwhitneyu(exited, stayed, alternative="two-sided")
        findings.append({
            "relationship": f"{label} × 12 hónapon belüli önkéntes kilépés",
            "metric": label,
            "method": "Mann–Whitney-próba",
            "mean_later_voluntary_exit": float(exited.mean()),
            "mean_no_voluntary_exit_within_12m": float(stayed.mean()),
            "difference_exit_minus_no_voluntary_exit": float(exited.mean() - stayed.mean()),
            "effect_size": _safe_float(
                _rank_biserial_from_u(test.statistic, len(exited), len(stayed))
            ),
            "p_value": float(test.pvalue),
            "n_later_voluntary_exit": int(len(exited)),
            "n_no_voluntary_exit_within_12m": int(len(stayed)),
            "n": int(len(exited) + len(stayed)),
        })
    _apply_adjustment(findings, method="holm")
    return _result(
        "engagement_exit_association",
        findings,
        scope=(
            "Munkavállalónként a legutolsó olyan válasz, amely után teljes 12 havi "
            f"követés rendelkezésre áll {cutoff.date().isoformat()}-ig."
        ),
        correction="Holm-korrekció",
    )


def _training_engagement_association(employees, engagement, training, end_date):
    end_date = pd.Timestamp(end_date)
    responses = engagement.copy()
    responses["SurveyDate"] = pd.to_datetime(responses["SurveyDate"], errors="coerce")
    responses = responses[responses["SurveyDate"] <= end_date].copy()
    if responses.empty:
        return _empty_result("training_engagement_association", "Nincs engagement-válasz a referencia-időpontig.")
    responses = responses.sort_values(["EmpID", "SurveyDate"]).drop_duplicates("EmpID", keep="last")

    training_data = training.copy()
    training_data["TrainingDate"] = pd.to_datetime(training_data["TrainingDate"], errors="coerce")
    merged_rows = []
    training_by_emp = {emp_id: group for emp_id, group in training_data.groupby("EmpID")}
    for row in responses.itertuples(index=False):
        survey_date = pd.Timestamp(row.SurveyDate)
        start = survey_date - pd.DateOffset(months=12) + pd.Timedelta(days=1)
        emp_training = training_by_emp.get(row.EmpID)
        if emp_training is None:
            count = 0
            completed = 0
        else:
            period = emp_training[
                (emp_training["TrainingDate"] >= start)
                & (emp_training["TrainingDate"] <= survey_date)
                & (emp_training["CompletionStatus"] != "Cancelled")
            ]
            count = int(len(period))
            completed = int((period["CompletionStatus"] == "Completed").sum())
        merged_rows.append({
            "EmpID": row.EmpID,
            "TrainingCount12M": count,
            "CompletedTrainingCount12M": completed,
            "EngagementScore": getattr(row, "EngagementScore"),
            "SatisfactionScore": getattr(row, "SatisfactionScore"),
            "WorkLifeBalanceScore": getattr(row, "WorkLifeBalanceScore"),
        })
    data = pd.DataFrame(merged_rows)

    findings = []
    outcomes = {
        "EngagementScore": "Elkötelezettségi index",
        "SatisfactionScore": "Elégedettségi index",
        "WorkLifeBalanceScore": "Work–life balance index",
    }
    exposures = {
        "TrainingCount12M": "Képzési részvételek száma az előző 12 hónapban",
        "CompletedTrainingCount12M": "Teljesített képzések száma az előző 12 hónapban",
    }
    for exposure, exposure_label in exposures.items():
        for outcome, outcome_label in outcomes.items():
            valid = data[[exposure, outcome]].dropna()
            if len(valid) < MIN_INFERENCE_GROUP or valid[exposure].nunique() < 2:
                continue
            test = stats.spearmanr(valid[exposure], valid[outcome])
            findings.append({
                "relationship": f"{exposure_label} × {outcome_label}",
                "method": "Spearman-féle rangkorreláció",
                "coefficient": _safe_float(test.statistic),
                "p_value": float(test.pvalue),
                "n": int(len(valid)),
            })
    _apply_adjustment(findings, method="bh")
    return _result(
        "training_engagement_association",
        findings,
        scope=(
            "Munkavállalónként a referencia-időpontig adott legutolsó engagement-válasz; "
            "ehhez az azt megelőző 12 hónap képzési aktivitása kapcsolódik."
        ),
        correction="Benjamini–Hochberg FDR-korrekció",
    )


def _training_group_differences(employees, training, end_date):
    end_date = pd.Timestamp(end_date)
    start_date = end_date - pd.DateOffset(months=12) + pd.Timedelta(days=1)
    data = training.copy()
    data["TrainingDate"] = pd.to_datetime(data["TrainingDate"], errors="coerce")
    data = data[(data["TrainingDate"] >= start_date) & (data["TrainingDate"] <= end_date)].copy()
    if data.empty:
        return _empty_result("training_group_differences", "Nincs képzési rekord a vizsgált 12 hónapban.")

    score_fields = {
        "OverallSatisfactionScore": "Képzési elégedettségi index",
        "JobRelevanceScore": "Munkaköri relevanciaindex",
        "PersonalRelevanceScore": "Személyes relevanciaindex",
        "DigitalContentUsabilityScore": "Digitális használhatósági index",
    }
    employee_level = data.groupby("EmpID")[list(score_fields)].mean().reset_index()
    emp = _add_demographic_dimensions(employees, end_date)
    merged = employee_level.merge(
        emp[["EmpID", "DepartmentType", "GenderCode", "Generation", "AgeGroup"]],
        on="EmpID",
        how="inner",
    )
    findings = []
    for field, label in score_fields.items():
        index_values = (merged[field] - 1) * 25
        for dimension in ["DepartmentType", "GenderCode", "Generation", "AgeGroup"]:
            test_result = _group_test(index_values, merged[dimension])
            if not test_result:
                continue
            findings.append({
                "relationship": f"{label} × {dimension}",
                "metric": label,
                "dimension": dimension,
                **test_result,
            })
    _apply_adjustment(findings, method="bh")
    result = _result(
        "training_group_differences",
        findings,
        scope=f"{start_date.date().isoformat()} – {end_date.date().isoformat()}, munkavállalói szintre aggregálva.",
        correction="Benjamini–Hochberg FDR-korrekció",
    )
    result["limitations"] = [
        "A szervezeti bontás a munkavállalói törzs aktuális vagy utolsó ismert DepartmentType értékét használja; szervezeti változástörténet nincs."
    ]
    return result


def _turnover_group_differences(employees, end_date):
    end_date = pd.Timestamp(end_date)
    start_date = end_date - pd.DateOffset(months=12) + pd.Timedelta(days=1)
    emp = _add_demographic_dimensions(employees, start_date)
    emp["StartDate"] = pd.to_datetime(emp["StartDate"], errors="coerce")
    emp["ExitDate"] = pd.to_datetime(emp["ExitDate"], errors="coerce")
    cohort = emp[
        (emp["StartDate"] <= start_date)
        & (emp["ExitDate"].isna() | (emp["ExitDate"] > start_date))
    ].copy()
    cohort["VoluntaryExitInPeriod"] = (
        (cohort["EmployeeStatus"] == "Voluntarily Terminated")
        & cohort["ExitDate"].notna()
        & (cohort["ExitDate"] > start_date)
        & (cohort["ExitDate"] <= end_date)
    )
    findings = []
    for dimension in ["DepartmentType", "GenderCode", "Generation", "AgeGroup"]:
        usable = cohort[[dimension, "VoluntaryExitInPeriod", "EmpID"]].dropna()
        group_sizes = usable.groupby(dimension, observed=True)["EmpID"].nunique()
        allowed = group_sizes[group_sizes >= MIN_INFERENCE_GROUP].index
        usable = usable[usable[dimension].isin(allowed)]
        if usable[dimension].nunique() < 2:
            continue
        table = pd.crosstab(usable[dimension], usable["VoluntaryExitInPeriod"])
        if table.shape[1] < 2:
            continue
        chi2, chi_p_value, _, expected = stats.chi2_contingency(table)
        if (expected < 5).any():
            if table.shape == (2, 2):
                _, p_value = stats.fisher_exact(table.to_numpy())
                method = "Fisher-féle egzakt próba"
            else:
                continue
        else:
            p_value = chi_p_value
            method = "khi-négyzet-próba"
        rates = (
            usable.groupby(dimension, observed=True)["VoluntaryExitInPeriod"]
            .mean()
            .mul(100)
            .to_dict()
        )
        highest = max(rates, key=rates.get)
        lowest = min(rates, key=rates.get)
        findings.append({
            "relationship": f"12 havi önkéntes kilépés × {dimension}",
            "dimension": dimension,
            "method": method,
            "p_value": float(p_value),
            "effect_size": _safe_float(_cramers_v(chi2, int(table.to_numpy().sum()), *table.shape)),
            "rates_percent": {str(k): float(v) for k, v in rates.items()},
            "highest_group": str(highest),
            "lowest_group": str(lowest),
            "difference_high_low_percentage_points": float(rates[highest] - rates[lowest]),
            "n": int(table.to_numpy().sum()),
            "small_expected_cell": bool((expected < 5).any()),
        })
    _apply_adjustment(findings, method="bh")
    result = _result(
        "turnover_group_differences",
        findings,
        scope=f"Nyitóállományi kohorsz: {start_date.date().isoformat()} – {end_date.date().isoformat()}.",
        correction="Benjamini–Hochberg FDR-korrekció",
    )
    result["limitations"] = [
        "A történeti szervezeti bontás a munkavállalói törzs aktuális vagy utolsó ismert DepartmentType értékét használja; szervezeti változástörténet nincs."
    ]
    return result


def _apply_adjustment(findings, method):
    p_values = [item["p_value"] for item in findings if item.get("p_value") is not None]
    if not p_values:
        return
    adjusted = _holm_adjust(p_values) if method == "holm" else _bh_adjust(p_values)
    index = 0
    for item in findings:
        if item.get("p_value") is None:
            continue
        item["adjusted_p_value"] = float(adjusted[index])
        item["significant"] = bool(adjusted[index] < 0.05)
        index += 1


def _result(analysis_id, findings, scope, correction):
    significant_count = sum(1 for item in findings if item.get("significant"))
    findings = sorted(
        findings,
        key=lambda item: (
            not item.get("significant", False),
            item.get("adjusted_p_value", 1.0),
            -abs(item.get("effect_size") or item.get("coefficient") or 0.0),
        ),
    )
    return {
        "analysis_id": analysis_id,
        "label": DISCOVERY_ANALYSES[analysis_id]["label"],
        "status": "ok" if findings else "insufficient_data",
        "scope": scope,
        "multiple_testing_correction": correction,
        "tested_relationships": len(findings),
        "significant_relationships": significant_count,
        "findings": findings[:12],
    }


def _empty_result(analysis_id, reason):
    return {
        "analysis_id": analysis_id,
        "label": DISCOVERY_ANALYSES[analysis_id]["label"],
        "status": "insufficient_data",
        "reason": reason,
        "tested_relationships": 0,
        "significant_relationships": 0,
        "findings": [],
    }


def run_followup_analyses(
    analysis_ids,
    employees,
    engagement,
    training,
    end_date,
    official_cutoff_date="2026-06-30",
):
    unknown = [item for item in analysis_ids if item not in DISCOVERY_ANALYSES]
    if unknown:
        raise ValueError("Ismeretlen további elemzési irány: " + ", ".join(unknown))

    results = []
    for analysis_id in analysis_ids:
        if analysis_id == "engagement_group_differences":
            result = _engagement_group_differences(employees, engagement, end_date)
        elif analysis_id == "engagement_internal_correlations":
            result = _engagement_internal_correlations(engagement, end_date)
        elif analysis_id == "engagement_exit_association":
            result = _engagement_exit_association(employees, engagement, official_cutoff_date)
        elif analysis_id == "training_engagement_association":
            result = _training_engagement_association(employees, engagement, training, end_date)
        elif analysis_id == "training_group_differences":
            result = _training_group_differences(employees, training, end_date)
        elif analysis_id == "turnover_group_differences":
            result = _turnover_group_differences(employees, end_date)
        else:
            raise AssertionError(analysis_id)
        results.append(result)
    return results


def summarize_followup_results(results):
    rows = []
    for result in results:
        significant = [item for item in result.get("findings", []) if item.get("significant")]
        if significant:
            strongest = significant[0]
            relationship = strongest.get("relationship", "")
            p_value = strongest.get("adjusted_p_value")
            effect = strongest.get("effect_size", strongest.get("coefficient"))
            rows.append({
                "Vizsgálat": result["label"],
                "Tesztelt kapcsolatok": result.get("tested_relationships", 0),
                "Szignifikáns": result.get("significant_relationships", 0),
                "Legerősebb jelzés": relationship,
                "Korrigált p": p_value,
                "Hatás / kapcsolat": effect,
            })
        else:
            rows.append({
                "Vizsgálat": result["label"],
                "Tesztelt kapcsolatok": result.get("tested_relationships", 0),
                "Szignifikáns": result.get("significant_relationships", 0),
                "Legerősebb jelzés": result.get("reason", "Nem talált statisztikailag igazolt kapcsolatot."),
                "Korrigált p": None,
                "Hatás / kapcsolat": None,
            })
    return pd.DataFrame(rows)
