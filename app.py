from pathlib import Path
import html
import textwrap

import pandas as pd
import streamlit as st
import altair as alt
from catalog_service import get_metric, load_catalogs
from ai_service import (
    get_local_capability_answer,
    get_training_type_clarification,
    interpret_results,
    plan_question,
)
from metric_engine import (
    SUPPORTED_METRICS,
    TRAINING_TIME_SERIES_METRICS,
    calculate_engagement_time_series,
    calculate_metric,
    calculate_training_time_series,
)

st.set_page_config(
    page_title="HR Insight AI",
    page_icon="📊",
    layout="wide"
)

st.markdown(
    """
    <style>
    div[class*="st-key-kpi_"] button {
        min-height: 125px;
        padding: 14px 10px;
        border-radius: 12px;
    }

    div[class*="st-key-kpi_"] button p {
        line-height: 1.25;
    }

    div[class*="st-key-kpi_"] button strong {
        display: inline-block;
        margin: 7px 0;
        font-size: 1.45rem;
    }

    div[class*="st-key-kpi_"] button em {
        font-size: 0.78rem;
        font-style: normal;
        color: #6b7280;
    }

    div[class*="st-key-kpi_"] button[kind="primary"] {
        background-color: #3568b8;
        border-color: #3568b8;
        color: white;
    }

    div[class*="st-key-kpi_"] button[kind="primary"] em {
        color: #e8eef9;
    }

    div[class*="st-key-kpi_"] button[kind="primary"]:hover {
        background-color: #2d5a9f;
        border-color: #2d5a9f;
    }

@media (max-width: 768px) {
    div[data-testid="stMainBlockContainer"] {
        padding-top: 9rem !important;
    }

    div[data-testid="stHorizontalBlock"]:has(
        div[class*="st-key-kpi_"]
    ) {
        flex-wrap: wrap;
        gap: 12px;
    }

    div[data-testid="stHorizontalBlock"]:has(
        div[class*="st-key-kpi_"]
    ) > div[data-testid="stColumn"] {
        flex: 0 0 calc(50% - 6px) !important;
        width: calc(50% - 6px) !important;
        min-width: 0 !important;
    }

    div[data-testid="stHorizontalBlock"]:has(
        div[class*="st-key-kpi_"]
    ) > div[data-testid="stColumn"]:nth-child(5) {
        margin-left: auto;
        margin-right: auto;
    }

    div[class*="st-key-kpi_"] button {
        min-height: 105px;
        padding: 8px 5px;
    }

    div[class*="st-key-kpi_"] button strong {
        margin: 5px 0;
        font-size: 1.25rem;
    }

    div[class*="st-key-kpi_"] button em {
        font-size: 0.68rem;
    }

    div[data-testid="stElementContainer"]:has(
        .st-key-reference_month
    ):has(
        .st-key-department_filter
    ) {
        display: contents !important;
    }

    div[data-testid="stHorizontalBlock"]:has(
        .st-key-reference_month
    ):has(
        .st-key-department_filter
    ) {
        position: fixed !important;
        top: 3.25rem !important;
        left: 1rem !important;
        right: 1rem !important;
        width: auto !important;
        z-index: 999999 !important;
        flex-wrap: nowrap;
        gap: 8px;
        padding: 6px 8px 8px 8px !important;
        background-color: white !important;
        border-bottom: 1px solid #d9dee7 !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.10) !important;
    }

    div[data-testid="stHorizontalBlock"]:has(
        .st-key-reference_month
    ):has(
        .st-key-department_filter
    ) > div[data-testid="stColumn"] {
        flex: 0 0 calc(50% - 4px) !important;
        width: calc(50% - 4px) !important;
        min-width: 0 !important;
    }

    div[data-testid="stHorizontalBlock"]:has(
        .st-key-reference_month
    ):has(
        .st-key-department_filter
    ) label p {
        font-size: 0.72rem;
    }
}

    </style>
    """,
    unsafe_allow_html=True
)

BASE_DIR = Path(__file__).resolve().parent
DATA_FOLDER = BASE_DIR / "data" / "processed"



@st.cache_data
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

    engagement["SurveyLaunchDate"] = pd.to_datetime(
        engagement["SurveyLaunchDate"],
        format="mixed"
    )
    engagement["SurveyDate"] = pd.to_datetime(
        engagement["SurveyDate"],
        format="mixed"
    )

    training["TrainingDate"] = pd.to_datetime(
        training["TrainingDate"],
        format="mixed"
    )

    return employees, engagement, training

catalogs = load_catalogs()


employees, engagement, training = load_data()

all_employees = employees.copy()
all_engagement = engagement.copy()
all_training = training.copy()

first_month = employees["StartDate"].min().to_period("M")
last_complete_month = pd.Period("2026-06", freq="M")


available_months = list(
    reversed(
        pd.period_range(
            start=first_month,
            end=last_complete_month,
            freq="M"
        )
    )
)

hungarian_months = {
    1: "január",
    2: "február",
    3: "március",
    4: "április",
    5: "május",
    6: "június",
    7: "július",
    8: "augusztus",
    9: "szeptember",
    10: "október",
    11: "november",
    12: "december"
}

st.title("HR Insight AI")
reference_caption = st.empty()


date_column, department_column = st.columns(2)

with date_column:
    selected_month = st.selectbox(
        "Vizsgálati hónap",
        options=available_months,
        index=0,
        format_func=lambda period: (
            f"{period.year}. "
            f"{hungarian_months[period.month]}"
        ),
        key="reference_month"
    )

with department_column:
    selected_department = st.selectbox(
        "Szervezeti terület",
        options=[
            "Összes",
            *sorted(
                employees[
                    "DepartmentType"
                ].dropna().unique()
            )
        ],
        index=0,
        key="department_filter"
    )

if selected_department != "Összes":
    employees = employees[
        employees["DepartmentType"]
        == selected_department
    ].copy()

    selected_employee_ids = set(
        employees["EmpID"]
    )

    engagement = engagement[
        engagement["EmpID"].isin(
            selected_employee_ids
        )
    ].copy()

    training = training[
        training["EmpID"].isin(
            selected_employee_ids
        )
    ].copy()

reference_date = selected_month.end_time.normalize()


reference_caption.caption(
    "Referencia-időpont: "
    f"{reference_date.date()}"
)

st.caption(
    "A KPI-k és elemzések a kiválasztott "
    "vizsgálati hónaphoz igazodnak."
)


def headcount_on_date(date):
    return (
        (employees["StartDate"] <= date)
        & (
            employees["ExitDate"].isna()
            | (employees["ExitDate"] > date)
        )
    ).sum()

def average_headcount_between(start_date, end_date):
    days = pd.date_range(
        start=start_date,
        end=end_date,
        freq="D"
    )

    if len(days) == 0:
        return 0

    daily_headcounts = [
        headcount_on_date(day)
        for day in days
    ]

    return sum(daily_headcounts) / len(daily_headcounts)

# Gördülő 12 hónap
period_12m_start = (
    reference_date
    - pd.DateOffset(years=1)
    + pd.Timedelta(days=1)
)

opening_reference_date = (
    period_12m_start - pd.Timedelta(days=1)
)

headcount_current = headcount_on_date(reference_date)
headcount_previous = headcount_on_date(
    opening_reference_date
)

headcount_change = (
    headcount_current - headcount_previous
)

hires_12m = (
    (employees["StartDate"] >= period_12m_start)
    & (employees["StartDate"] <= reference_date)
).sum()


exits_12m_mask = (
    (employees["ExitDate"] >= period_12m_start)
    & (employees["ExitDate"] <= reference_date)
)

exits_12m = exits_12m_mask.sum()

average_headcount = average_headcount_between(
    period_12m_start,
    reference_date
)

turnover_rate = (
    exits_12m / average_headcount * 100
    if average_headcount > 0
    else 0
)

voluntary_exits_12m = (
    exits_12m_mask
    & (
        employees["EmployeeStatus"]
        == "Voluntarily Terminated"
    )
).sum()

voluntary_turnover_rate = (
    voluntary_exits_12m
    / average_headcount
    * 100
    if average_headcount > 0
    else 0
)


# Legutóbbi engagement-hullám
available_surveys = engagement[
    engagement["SurveyLaunchDate"] <= reference_date
]

if available_surveys.empty:
    engagement_value = None
    engagement_wave = "Nincs adat"
    engagement_respondents = 0
    engagement_response_rate = None
else:
    latest_launch_date = available_surveys[
        "SurveyLaunchDate"
    ].max()

    latest_wave = available_surveys[
        available_surveys["SurveyLaunchDate"]
        == latest_launch_date
    ]

    engagement_value = latest_wave[
        "EngagementScore"
    ].mean()

    engagement_wave = latest_wave[
        "SurveyWaveID"
    ].iloc[0]

    engagement_respondents = latest_wave[
        "EmpID"
    ].nunique()

    eligible_at_survey = (
        (employees["StartDate"] <= latest_launch_date)
        & (
            employees["ExitDate"].isna()
            | (
                employees["ExitDate"]
                >= latest_launch_date
            )
        )
    ).sum()

    engagement_response_rate = (
        engagement_respondents
        / eligible_at_survey
        * 100
        if eligible_at_survey > 0
        else 0
    )

# Havi képzési részvétel
training_month_start = (
    selected_month.start_time.normalize()
)

training_month = training[
    (training["TrainingDate"] >= training_month_start)
    & (training["TrainingDate"] <= reference_date)
]

trained_employees = training_month[
    "EmpID"
].nunique()

eligible_for_training = (
    (employees["StartDate"] <= reference_date)
    & (
        employees["ExitDate"].isna()
        | (
            employees["ExitDate"]
            > training_month_start
        )
    )
).sum()

training_participation_rate = (
    trained_employees
    / eligible_for_training
    * 100
    if eligible_for_training > 0
    else 0
)

completed_trainings = (
    training_month["CompletionStatus"]
    == "Completed"
).sum()

incomplete_trainings = (
    training_month["CompletionStatus"]
    == "Incomplete"
).sum()

started_trainings = (
    completed_trainings + incomplete_trainings
)

training_completion_rate = (
    completed_trainings
    / started_trainings
    * 100
    if started_trainings > 0
    else 0
)

# KPI-kártyák
st.subheader("Fő HR-mutatók")
if "selected_kpi" not in st.session_state:
    st.session_state.selected_kpi = "headcount"

def show_kpi_card(
    column,
    key,
    metric_name,
    title,
    value,
    detail
):
    metric = get_metric(metric_name)
    is_selected = (
        st.session_state.selected_kpi == key
    )

    card_text = (
        f"{title}\n\n"
        f"**{value}**\n\n"
        f"_{detail}_"
    )

    if column.button(
        card_text,
        key=f"kpi_{key}",
        type="primary" if is_selected else "secondary",
        use_container_width=True,
        help=metric["description"]
    ):
        st.session_state.selected_kpi = key
        st.rerun()



col1, col2, col3, col4, col5 = st.columns(5)

headcount_card_value = (
    f"{headcount_current:,}".replace(",", " ")
)

hires_card_value = f"{hires_12m} fő"

turnover_card_value = f"{turnover_rate:.1f}%"
if engagement_value is None:
    engagement_card_value = "Nincs adat"
else:
    engagement_index_value = (
        engagement_value - 1
    ) * 25

    engagement_card_value = (
        f"{engagement_index_value:.1f} / 100"
    )

training_card_value = (
    f"{training_participation_rate:.1f}%"
)

show_kpi_card(
    col1,
    "headcount",
    "ClosingHeadcount",
    "Állományi létszám",
    headcount_card_value,
    f"{headcount_change:+} fő / 12 hó"
)

show_kpi_card(
    col2,
    "hires",
    "HireCount",
    "Belépők",
    hires_card_value,
    "Gördülő 12 hónap"
)

show_kpi_card(
    col3,
    "turnover",
    "Rolling12MonthTurnoverRate",
    "Fluktuáció",
    turnover_card_value,
    f"Önkéntes: {voluntary_turnover_rate:.1f}%"
)

show_kpi_card(
    col4,
    "engagement",
    "AverageEngagementIndex",
    "Engagement",
    engagement_card_value,
    (
        "Nincs korábbi felmérés"
        if engagement_value is None
        else (
            f"{engagement_wave} · "
            f"válaszadás: "
            f"{engagement_response_rate:.1f}%"
        )
    )
)

show_kpi_card(
    col5,
    "training",
    "TrainingParticipationRate",
    "Képzési részvétel",
    training_card_value,
    "Legalább 1 képzés / hónap"
)


if st.session_state.selected_kpi == "headcount":
    st.subheader("Állományi létszám alakulása")

    trend_months = pd.period_range(
        end=selected_month,
        periods=12,
        freq="M"
    )

    headcount_trend = pd.DataFrame({
        "Hónap": [
            str(month)
            for month in trend_months      
        ],
        "Állományi létszám": [
            headcount_on_date(month.end_time.normalize())
            for month in trend_months
        ]
    })

    headcount_chart = (
        alt.Chart(headcount_trend)
        .mark_line(
            point=alt.OverlayMarkDef(
                size=110,
                filled=True
        ),
        strokeWidth=2.5
    )
        .encode(
            x=alt.X(
                "Hónap:O",
                title="Hónap",
                axis=alt.Axis(
                    labelAngle=-45,
                    labelOverlap="greedy"
                )
            ),
            y=alt.Y(
                "Állományi létszám:Q",
                title="Létszám",
                scale=alt.Scale(zero=True)
            ),
            tooltip=[
                alt.Tooltip(
                    "Hónap:N",
                    title="Hónap"
                ),
                alt.Tooltip(
                    "Állományi létszám:Q",
                    title="Állományi létszám"
                )
            ]
        )
        .properties(height=350)
    )

    st.altair_chart(headcount_chart, width="stretch")

elif st.session_state.selected_kpi == "hires":
    st.subheader("Belépők számának alakulása")

    hires_trend_months = pd.period_range(
        end=selected_month,
        periods=12,
        freq="M"
    )

    monthly_hires = (
        employees.assign(
            HireMonth=employees["StartDate"].dt.to_period("M")
        )
        .groupby("HireMonth")
        .size()
        .reindex(hires_trend_months, fill_value=0)
    )

    hires_trend = pd.DataFrame({
        "Hónap": [
            str(month)
            for month in hires_trend_months
        ],
        "Belépők száma": monthly_hires.values
    })

    hires_chart = (
        alt.Chart(hires_trend)
        .mark_bar(
            color="#3568b8",
            cornerRadiusTopLeft=4,
            cornerRadiusTopRight=4
        )
        .encode(
            x=alt.X(
                "Hónap:O",
                title="Hónap",
                axis=alt.Axis(
                    labelAngle=-45,
                    labelOverlap="greedy"
    )
),
            y=alt.Y(
                "Belépők száma:Q",
                title="Belépők száma"
            ),
            tooltip=[
                alt.Tooltip(
                    "Hónap:N",
                    title="Hónap"
                ),
                alt.Tooltip(
                    "Belépők száma:Q",
                    title="Belépők száma"
                )
            ]
        )
        .properties(height=350)
    )

    st.altair_chart(hires_chart, width="stretch")


elif st.session_state.selected_kpi == "turnover":
    st.subheader("Gördülő 12 havi fluktuáció")

    turnover_trend_months = pd.period_range(
        end=selected_month,
        periods=12,
        freq="M"
    )

    turnover_records = []

    for month in turnover_trend_months:
        month_end = month.end_time.normalize()
        month_start = (
            month_end - pd.DateOffset(years=1)
        )

        opening_headcount = headcount_on_date(
            month_start
        )
        closing_headcount = headcount_on_date(
            month_end
        )

        monthly_average_headcount = (
            average_headcount_between(
                month_start,
                month_end
            )
        )

        monthly_exit_mask = (
            (employees["ExitDate"] >= month_start)
            & (employees["ExitDate"] <= month_end)
        )

        monthly_total_exits = monthly_exit_mask.sum()

        monthly_voluntary_exits = (
            monthly_exit_mask
            & (
                employees["EmployeeStatus"]
                == "Voluntarily Terminated"
            )
        ).sum()

        if monthly_average_headcount > 0:
            monthly_turnover = (
                monthly_total_exits
                / monthly_average_headcount
                * 100
            )
            monthly_voluntary_turnover = (
                monthly_voluntary_exits
                / monthly_average_headcount
                * 100
            )
        else:
            monthly_turnover = 0
            monthly_voluntary_turnover = 0

        turnover_records.extend([
            {
                "Hónap": str(month),
                "Mutató": "Teljes fluktuáció",
                "Fluktuáció": monthly_turnover
            },
            {
                "Hónap": str(month),
                "Mutató": "Önkéntes fluktuáció",
                "Fluktuáció": monthly_voluntary_turnover
            }
        ])

    turnover_trend = pd.DataFrame(
        turnover_records
    )

    turnover_chart = (
        alt.Chart(turnover_trend)
        .mark_line(
            point=alt.OverlayMarkDef(
                size=110,
                filled=True
            ),
            strokeWidth=2.5
        )
        .encode(
            x=alt.X(
                "Hónap:O",
                title="Hónap",
                axis=alt.Axis(
                    labelAngle=-45,
                    labelOverlap="greedy"
                ),
            ),
            y=alt.Y(
                "Fluktuáció:Q",
                title="Fluktuáció (%)"
            ),
            color=alt.Color(
                "Mutató:N",
                title=None,
                scale=alt.Scale(
                    domain=[
                        "Teljes fluktuáció",
                        "Önkéntes fluktuáció"
                    ],
                    range=[
                        "#3568b8",
                        "#7ea6df"
                    ]
                ),
                legend=alt.Legend(
                    orient="bottom",
                    direction="vertical",
                    title=None
                )
            ),
            tooltip=[
                alt.Tooltip(
                    "Hónap:N",
                    title="Hónap"
                ),
                alt.Tooltip(
                    "Mutató:N",
                    title="Mutató"
                ),
                alt.Tooltip(
                    "Fluktuáció:Q",
                    title="Érték",
                    format=".1f"
                )
            ]
        )
        .properties(height=350)
    )

    st.altair_chart(
        turnover_chart,
        width="stretch"
    )

elif st.session_state.selected_kpi == "engagement":
    st.subheader("Munkavállalói élmény alakulása")

    available_engagement = engagement[
        engagement["SurveyLaunchDate"]
        <= reference_date
    ].copy()

    if available_engagement.empty:
        st.info(
            "A kiválasztott időpontig nincs "
            "elérhető engagement-felmérés."
        )
    else:
        engagement_summary = (
            available_engagement
            .groupby(
                [
                    "SurveyWaveID",
                    "SurveyLaunchDate"
                ],
                as_index=False
            )
            .agg(
                Engagement=(
                    "EngagementScore",
                    "mean"
                ),
                Elégedettség=(
                    "SatisfactionScore",
                    "mean"
                ),
                Munka_magánélet=(
                    "WorkLifeBalanceScore",
                    "mean"
                ),
                Válaszadók=(
                    "EmpID",
                    "nunique"
                )
            )
            .sort_values("SurveyLaunchDate")
            .tail(8)
        )

        engagement_summary[
            "Válaszadási arány"
        ] = engagement_summary.apply(
            lambda row: (
                row["Válaszadók"]
                / headcount_on_date(
                    row["SurveyLaunchDate"]
                )
                * 100
            )
            if headcount_on_date(
                row["SurveyLaunchDate"]
            ) > 0
            else 0,
            axis=1
        )

        engagement_summary[
            "Engagement_index"
        ] = (
            engagement_summary["Engagement"] - 1
        ) * 25

        engagement_summary[
            "Elégedettség_index"
        ] = (
            engagement_summary["Elégedettség"] - 1
        ) * 25

        engagement_summary[
            "Munka_magánélet_index"
        ] = (
            engagement_summary["Munka_magánélet"] - 1
        ) * 25


        engagement_long = (
            engagement_summary
            .melt(
                id_vars=[
                    "SurveyWaveID",
                    "SurveyLaunchDate",
                    "Válaszadók",
                    "Válaszadási arány"
                ],
                value_vars=[
                    "Engagement_index",
                    "Elégedettség_index",
                    "Munka_magánélet_index"
                ],
                var_name="Mutató",
                value_name="Index"
            )
        )

        engagement_long["Mutató"] = (
            engagement_long["Mutató"]
            .replace({
                "Engagement_index": "Engagement",
                "Elégedettség_index": "Elégedettség",
                "Munka_magánélet_index":
                    "Munka–magánélet egyensúlya"
            })
        )

        engagement_chart = (
            alt.Chart(engagement_long)
            .mark_line(
                point=alt.OverlayMarkDef(
                    size=110,
                    filled=True
                ),
                strokeWidth=2.5
            )
            .encode(
                x=alt.X(
                    "SurveyLaunchDate:T",
                    title="Felmérési hullám",
                    axis=alt.Axis(
                        format="%Y-%m"
                    )
                ),
                y=alt.Y(
                    "Index:Q",
                    title="Engagement index",
                    scale=alt.Scale(
                        domain=[50, 100]
                    )
                ),                color=alt.Color(
                    "Mutató:N",
                    title=None,
                    scale=alt.Scale(
                        domain=[
                            "Engagement",
                            "Elégedettség",
                            "Munka–magánélet egyensúlya"
                        ],
                        range=[
                            "#3568b8",
                            "#64a78f",
                            "#d68b55"
                        ]
                    ),
                    legend=alt.Legend(
                        orient="bottom",
                        direction="vertical"
                    )
                ),
                tooltip=[
                    alt.Tooltip(
                        "SurveyWaveID:N",
                        title="Hullám"
                    ),
                    alt.Tooltip(
                        "Mutató:N",
                        title="Mutató"
                    ),
                    alt.Tooltip(
                        "Index:Q",
                        title="Index",
                        format=".1f"
                    ),

                    alt.Tooltip(
                        "Válaszadók:Q",
                        title="Válaszadók"
                    ),
                    alt.Tooltip(
                        "Válaszadási arány:Q",
                        title="Válaszadási arány",
                        format=".1f"
                    )
                ]
            )
            .properties(height=350)
        )

        st.altair_chart(
            engagement_chart,
            width="stretch"
        )

        st.caption(
            "Az index 0–100 pontos értéket vehet fel, "
            "átkódolása: 1 = 0, 2 = 25, 3 = 50, "
            "4 = 75, 5 = 100. "
            "A diagram nagyított, rögzített "
            "50–100 pontos skálát használ."
        )

elif st.session_state.selected_kpi == "training":
    st.subheader(
        "Képzési részvétel és teljesítés"
    )

    training_trend_months = pd.period_range(
        end=selected_month,
        periods=12,
        freq="M"
    )

    training_records = []

    for month in training_trend_months:
        month_start = month.start_time.normalize()
        month_end = month.end_time.normalize()

        training_window = training[
            (training["TrainingDate"] >= month_start)
            & (training["TrainingDate"] <= month_end)
        ]

        trained_in_window = training_window[
            "EmpID"
        ].nunique()

        eligible_in_window = (
            (employees["StartDate"] <= month_end)
            & (
                employees["ExitDate"].isna()
                | (
                    employees["ExitDate"]
                    > month_start
                )
            )
        ).sum()

        participation_in_window = (
            trained_in_window
            / eligible_in_window
            * 100
            if eligible_in_window > 0
            else 0
        )

        completed_in_window = (
            training_window["CompletionStatus"]
            == "Completed"
        ).sum()

        incomplete_in_window = (
            training_window["CompletionStatus"]
            == "Incomplete"
        ).sum()

        started_in_window = (
            completed_in_window
            + incomplete_in_window
        )

        completion_in_window = (
            completed_in_window
            / started_in_window
            * 100
            if started_in_window > 0
            else 0
        )

        training_records.extend([
            {
                "Hónap": str(month),
                "Mutató": "Részvételi arány",
                "Érték": participation_in_window
            },
            {
                "Hónap": str(month),
                "Mutató": "Teljesítési arány",
                "Érték": completion_in_window
            }
        ])

    training_trend = pd.DataFrame(
        training_records
    )

    training_chart = (
        alt.Chart(training_trend)
        .mark_line(
            point=alt.OverlayMarkDef(
                size=110,
                filled=True
            ),
            strokeWidth=2.5
        )
        .encode(
            x=alt.X(
                "Hónap:O",
                title="Hónap",
                axis=alt.Axis(
                    labelAngle=-45,
                    labelOverlap="greedy"
                )
            ),
            y=alt.Y(
                "Érték:Q",
                title="Arány (%)",
                scale=alt.Scale(
                    domain=[0, 100]
                )
            ),
            color=alt.Color(
                "Mutató:N",
                title=None,
                scale=alt.Scale(
                    domain=[
                        "Részvételi arány",
                        "Teljesítési arány"
                    ],
                    range=[
                        "#3568b8",
                        "#64a78f"
                    ]
                ),
                legend=alt.Legend(
                    orient="bottom",
                    direction="vertical",
                    labelLimit=300
                )
            ),
            tooltip=[
                alt.Tooltip(
                    "Hónap:N",
                    title="Hónap"
                ),
                alt.Tooltip(
                    "Mutató:N",
                    title="Mutató"
                ),
                alt.Tooltip(
                    "Érték:Q",
                    title="Érték",
                    format=".1f"
                )
            ]
        )
        .properties(height=350)
    )

    st.altair_chart(
        training_chart,
        width="stretch"
    )

    st.caption(
        "**Részvétel:** legalább egy képzéssel "
        "rendelkező munkavállalók aránya az "
        "adott hónapban.  \n"
        "**Teljesítés:** a befejezett képzések "
        "aránya a befejezett és nem teljesített "
        "képzések között."
    )


def add_demographic_dimensions(employee_data, filter_date):
    result = employee_data.copy()
    birth_date = pd.to_datetime(
        result["DOB"],
        errors="coerce",
        format="mixed"
    )
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
        ]
    ).astype("string")

    filter_date = pd.Timestamp(filter_date)
    age = (
        filter_date.year
        - birth_date.dt.year
        - (
            (birth_date.dt.month > filter_date.month)
            | (
                (birth_date.dt.month == filter_date.month)
                & (birth_date.dt.day > filter_date.day)
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
        ]
    ).astype("string")

    return result


def workforce_composition_dates(start_date, end_date, granularity):
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    if start == end:
        return [end]

    if granularity == "automatic":
        duration_days = (end - start).days
        if duration_days <= 550:
            granularity = "month"
        elif duration_days <= 1825:
            granularity = "quarter"
        else:
            granularity = "year"

    frequency = {
        "month": "M",
        "quarter": "Q",
        "year": "Y",
    }.get(granularity, "M")
    periods = pd.period_range(start=start, end=end, freq=frequency)
    dates = [
        min(period.end_time.normalize(), end)
        for period in periods
    ]
    return list(dict.fromkeys(dates))


def build_workforce_composition(
    employee_data,
    grouping_field,
    requested_values,
    start_date,
    end_date,
    granularity,
):
    records = []
    for snapshot_date in workforce_composition_dates(
        start_date,
        end_date,
        granularity,
    ):
        dimensioned = add_demographic_dimensions(
            employee_data,
            snapshot_date,
        )
        active = dimensioned[
            (dimensioned["StartDate"] <= snapshot_date)
            & (
                dimensioned["ExitDate"].isna()
                | (dimensioned["ExitDate"] > snapshot_date)
            )
        ]
        if requested_values:
            active = active[
                active[grouping_field].isin(requested_values)
            ]
        counts = active.groupby(
            grouping_field,
            observed=True,
        )["EmpID"].nunique()
        counts = counts[counts >= 4]
        visible_total = counts.sum()
        for group_value, count in counts.items():
            records.append({
                "Dátum": snapshot_date,
                "Időszak": snapshot_date.strftime("%Y-%m-%d"),
                "Csoport": str(group_value),
                "Létszám": int(count),
                "Arány": (
                    count / visible_total * 100
                    if visible_total > 0
                    else 0
                ),
            })
    if not records:
        raise ValueError(
            "Nincs megjeleníthető, legalább 4 fős csoporteredmény."
        )
    return pd.DataFrame(records)


def render_workforce_composition(data, chart_type, grouping_field):
    logical_orders = {
        "Generation": [
            "Silent Generation (1945 vagy korábban)",
            "Baby Boomer (1946–1964)",
            "Generation X (1965–1980)",
            "Generation Y (Millennial, 1981–1996)",
            "Generation Z (1997–2012)",
        ],
        "AgeGroup": [
            "29 éves vagy fiatalabb",
            "30–44 éves",
            "45–59 éves",
            "60 éves vagy idősebb",
        ],
        "GenderCode": ["Female", "Male"],
    }
    group_order = logical_orders.get(
        grouping_field,
        list(dict.fromkeys(data["Csoport"])),
    )
    order_lookup = {
        value: index
        for index, value in enumerate(group_order)
    }
    data = data.copy()
    data["Sorrend"] = data["Csoport"].map(order_lookup).fillna(
        len(group_order)
    )

    if chart_type == "pie":
        chart = (
            alt.Chart(data)
            .mark_arc(innerRadius=45)
            .encode(
                theta=alt.Theta("Létszám:Q"),
                color=alt.Color(
                    "Csoport:N",
                    title=grouping_field,
                    sort=group_order,
                    legend=alt.Legend(labelLimit=260),
                ),
                order=alt.Order("Sorrend:Q", sort="ascending"),
                tooltip=[
                    alt.Tooltip("Csoport:N", title="Csoport"),
                    alt.Tooltip("Létszám:Q", title="Létszám"),
                    alt.Tooltip("Arány:Q", title="Arány", format=".1f"),
                ],
            )
            .properties(height=400)
        )
    else:
        value_field = "Arány" if chart_type == "stacked_100" else "Létszám"
        value_title = "Megoszlás (%)" if chart_type == "stacked_100" else "Létszám (fő)"
        chart = (
            alt.Chart(data)
            .mark_area()
            .encode(
                x=alt.X("Dátum:T", title="Időpont"),
                y=alt.Y(
                    f"{value_field}:Q",
                    title=value_title,
                    stack="normalize" if chart_type == "stacked_100" else "zero",
                    axis=alt.Axis(format="%") if chart_type == "stacked_100" else alt.Axis(),
                ),
                color=alt.Color(
                    "Csoport:N",
                    title=grouping_field,
                    sort=group_order,
                    legend=alt.Legend(labelLimit=260),
                ),
                order=alt.Order("Sorrend:Q", sort="ascending"),
                tooltip=[
                    alt.Tooltip("Időszak:N", title="Időpont"),
                    alt.Tooltip("Csoport:N", title="Csoport"),
                    alt.Tooltip("Létszám:Q", title="Létszám"),
                    alt.Tooltip("Arány:Q", title="Arány (%)", format=".1f"),
                ],
            )
            .properties(height=400)
        )
    st.altair_chart(chart, width="stretch")


def apply_question_filters(
    employee_data,
    engagement_data,
    training_data,
    question_filters,
    filter_date
):
    filtered_employees = add_demographic_dimensions(
        employee_data,
        filter_date
    )

    employee_filter_fields = {
        "DepartmentType",
        "GenderCode",
        "Generation",
        "AgeGroup",
    }
    training_filter_fields = {
        "TrainingCategory",
        "TrainingProgramName",
        "TrainingPurpose",
        "TrainingType",
        "DeliveryMode",
    }
    filters_by_field = {}
    for question_filter in question_filters:
        filters_by_field.setdefault(
            question_filter.field,
            []
        ).append(question_filter.value)

    for field, values in filters_by_field.items():
        if field not in employee_filter_fields:
            continue
        filtered_employees = filtered_employees[
            filtered_employees[field].isin(values)
        ]

    employee_ids = set(filtered_employees["EmpID"])
    filtered_engagement = engagement_data[
        engagement_data["EmpID"].isin(employee_ids)
    ].copy()
    filtered_training = training_data[
        training_data["EmpID"].isin(employee_ids)
    ].copy()
    for field, values in filters_by_field.items():
        if field not in training_filter_fields:
            continue
        filtered_training = filtered_training[
            filtered_training[field].isin(values)
        ]

    filter_label = ", ".join(
        f"{field}: {' / '.join(values)}"
        for field, values in filters_by_field.items()
    )

    return (
        filtered_employees,
        filtered_engagement,
        filtered_training,
        filter_label,
    )


def _axis_key(unit):
    if "0–100" in unit or unit in {"pont", "indexpont"}:
        return "0–100-as skála"
    if unit == "százalék":
        return "százalék"
    if "1–5" in unit:
        return "1–5-ös skála"
    return unit


def _wrap_legend_label(value, width=24):
    return "\n".join(
        textwrap.wrap(
            str(value),
            width=width,
            break_long_words=False,
            break_on_hyphens=False,
        )
    )


def _metric_short_label(metric_name, label):
    return {
        "AverageEngagementIndex": "Elkötelezettség",
        "AverageSatisfactionIndex": "Elégedettség",
        "AverageWorkLifeBalanceIndex": "Work–life balance",
        "SurveyResponseRate": "Válaszadási arány",
        "SatisfactionLow2BoxRate": "Elégedettség Low2Box",
        "AverageOverallSatisfactionIndex": "Képzési elégedettség",
        "AverageTrainerEvaluationIndex": "Oktatói értékelés",
        "AverageJobRelevanceIndex": "Munkaköri relevancia",
        "AveragePersonalRelevanceIndex": "Személyes relevancia",
        "AverageDigitalContentUsabilityIndex": (
            "Digitális használhatóság"
        ),
    }.get(metric_name, label)


def build_combined_engagement_time_series(
    question_plan,
    employee_data,
    engagement_data,
    filter_label,
):
    grouping_specs = [(filter_label, employee_data)]

    if question_plan.groupings:
        grouping = question_plan.groupings[0]
        dimensioned = add_demographic_dimensions(
            employee_data,
            question_plan.end_date,
        )
        values = sorted(
            dimensioned[grouping.field].dropna().unique()
        )
        if grouping.values:
            values = [
                value for value in values
                if value in grouping.values
            ]
        grouping_specs = [
            (
                value,
                dimensioned[
                    dimensioned[grouping.field] == value
                ],
            )
            for value in values
        ]

    explicit_comparison = bool(
        question_plan.comparison_groups
    )
    comparison_groups = [
        group.model_dump()
        for group in question_plan.comparison_groups
    ] or [{
        "kind": "all_employees",
        "label": None,
        "exit_window_months": None,
    }]

    records = []
    for group_label, group_employees in grouping_specs:
        group_ids = set(group_employees["EmpID"])
        group_engagement = engagement_data[
            engagement_data["EmpID"].isin(group_ids)
        ]

        for comparison_group in comparison_groups:
            comparison_label = comparison_group.get("label")
            if (
                explicit_comparison
                and comparison_group["kind"] == "all_employees"
            ):
                comparison_label = "Teljes vállalat"
            elif explicit_comparison and comparison_group["kind"] == (
                "voluntary_exit_within_months_after_survey"
            ):
                months = comparison_group["exit_window_months"]
                comparison_label = (
                    "1 éven belül felmondók"
                    if months == 12
                    else f"{months} hónapon belül felmondók"
                )
            elif explicit_comparison and comparison_group["kind"] == (
                "no_voluntary_exit_within_months_after_survey"
            ):
                months = comparison_group["exit_window_months"]
                comparison_label = (
                    "1 éven belül nem felmondók"
                    if months == 12
                    else f"{months} hónapon belül nem felmondók"
                )
            display_group = group_label
            if comparison_label:
                display_group = (
                    comparison_label
                    if not question_plan.groupings
                    else f"{group_label} – {comparison_label}"
                )

            for metric_name in question_plan.metric_names:
                if metric_name not in SUPPORTED_METRICS:
                    continue
                try:
                    result = calculate_engagement_time_series(
                        metric_name,
                        group_employees,
                        group_engagement,
                        question_plan.start_date,
                        question_plan.end_date,
                        comparison_group=comparison_group,
                    )
                except ValueError:
                    continue

                for record in result["records"]:
                    sample_size = record.get("RespondentCount")
                    if sample_size is not None and sample_size < 4:
                        continue
                    metric_short = _metric_short_label(
                        result["metric_name"], result["label"]
                    )
                    records.append({
                        **record,
                        "PeriodStart": record["SurveyLaunchDate"],
                        "PeriodEnd": record["SurveyLaunchDate"],
                        "PeriodLabel": record["SurveyWaveID"],
                        "Metric": result["label"],
                        "MetricShort": metric_short,
                        "MetricLegend": _wrap_legend_label(
                            metric_short
                        ),
                        "MetricName": result["metric_name"],
                        "Unit": result["unit"],
                        "Axis": _axis_key(result["unit"]),
                        "Group": display_group,
                        "GroupLegend": _wrap_legend_label(
                            display_group
                        ),
                        "Series": (
                            f"{result['label']} – {display_group}"
                        ),
                    })

    if not records:
        raise ValueError(
            "Nincs megjeleníthető, legalább 4 választ "
            "tartalmazó idősoros eredmény."
        )
    return pd.DataFrame(records)


def build_combined_training_time_series(
    question_plan,
    employee_data,
    training_data,
    filter_label,
):
    if question_plan.comparison_groups:
        raise ValueError(
            "A felmérés utáni kilépői csoportok csak "
            "engagement-idősornál használhatók."
        )

    employee_group_fields = {
        "DepartmentType",
        "GenderCode",
        "Generation",
        "AgeGroup",
    }
    training_group_fields = {
        "TrainingCategory",
        "TrainingProgramName",
        "TrainingPurpose",
        "TrainingType",
        "DeliveryMode",
    }
    grouping_specs = [
        (filter_label, employee_data, training_data)
    ]

    if question_plan.groupings:
        grouping = question_plan.groupings[0]
        if grouping.field in employee_group_fields:
            dimensioned = add_demographic_dimensions(
                employee_data,
                question_plan.end_date,
            )
            values = sorted(
                dimensioned[grouping.field].dropna().unique()
            )
            if grouping.values:
                values = [
                    value for value in values
                    if value in grouping.values
                ]
            grouping_specs = []
            for value in values:
                group_employees = dimensioned[
                    dimensioned[grouping.field] == value
                ]
                group_ids = set(group_employees["EmpID"])
                group_training = training_data[
                    training_data["EmpID"].isin(group_ids)
                ]
                grouping_specs.append(
                    (value, group_employees, group_training)
                )
        elif grouping.field in training_group_fields:
            values = sorted(
                training_data[grouping.field].dropna().unique()
            )
            if grouping.values:
                values = [
                    value for value in values
                    if value in grouping.values
                ]
            grouping_specs = [
                (
                    value,
                    employee_data,
                    training_data[
                        training_data[grouping.field] == value
                    ],
                )
                for value in values
            ]
        else:
            raise ValueError(
                f"Nem támogatott képzési bontás: {grouping.field}"
            )

    records = []
    for group_label, group_employees, group_training in grouping_specs:
        for metric_name in question_plan.metric_names:
            if metric_name not in TRAINING_TIME_SERIES_METRICS:
                continue
            try:
                result = calculate_training_time_series(
                    metric_name,
                    group_employees,
                    group_training,
                    question_plan.start_date,
                    question_plan.end_date,
                    granularity=question_plan.time_granularity,
                )
            except ValueError:
                continue

            metric_short = _metric_short_label(
                result["metric_name"], result["label"]
            )
            for record in result["records"]:
                sample_size = (
                    record.get("RespondentCount")
                    if record.get("RespondentCount") is not None
                    else record.get("ParticipantCount")
                )
                if sample_size is not None and sample_size < 4:
                    continue
                records.append({
                    **record,
                    "Metric": result["label"],
                    "MetricShort": metric_short,
                    "MetricLegend": _wrap_legend_label(metric_short),
                    "MetricName": result["metric_name"],
                    "Unit": result["unit"],
                    "Axis": _axis_key(result["unit"]),
                    "Group": group_label,
                    "GroupLegend": _wrap_legend_label(group_label),
                    "Series": f"{result['label']} – {group_label}",
                })

    if not records:
        raise ValueError(
            "Nincs megjeleníthető, legalább 4 résztvevőt "
            "vagy választ tartalmazó képzési idősor."
        )
    return pd.DataFrame(records)


def _time_series_layer(
    data,
    axis_name,
    metric_domain,
    dash_range,
    group_domain,
    group_range,
    orient="left",
):
    axis_data = data[data["Axis"] == axis_name]
    domain = None
    if axis_name == "0–100-as skála":
        domain = [0, 100]
    elif axis_name == "százalék":
        domain = [0, 100]
    elif axis_name == "1–5-ös skála":
        domain = [1, 5]

    return (
        alt.Chart(axis_data)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                "PeriodLabel:N",
                title="Időszak",
                axis=alt.Axis(labelAngle=-45),
                sort=alt.SortField(
                    field="PeriodStart",
                    order="ascending",
                ),
            ),
            y=alt.Y(
                "Value:Q",
                title=axis_name,
                scale=alt.Scale(domain=domain, zero=False),
                axis=alt.Axis(orient=orient),
            ),
            color=alt.Color(
                "Group:N",
                scale=alt.Scale(
                    domain=group_domain,
                    range=group_range,
                ),
                legend=None,
            ),
            strokeDash=alt.StrokeDash(
                "MetricShort:N",
                scale=alt.Scale(
                    domain=metric_domain,
                    range=dash_range,
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("PeriodLabel:N", title="Időszak"),
                alt.Tooltip("Metric:N", title="Mutató"),
                alt.Tooltip("Group:N", title="Csoport"),
                alt.Tooltip(
                    "Value:Q", title="Érték", format=".1f"
                ),
                alt.Tooltip(
                    "RespondentCount:Q",
                    title="Érvényes válaszok",
                    format=",.0f",
                ),
            ],
        )
        .properties(height=380)
    )


def render_combined_time_series(data, chart_layout):
    axes = list(data["Axis"].drop_duplicates())
    series_count = data["Series"].nunique()
    metric_domain = list(data["MetricShort"].drop_duplicates())
    group_domain = list(data["Group"].drop_duplicates())
    color_palette = [
        "#0068C9",
        "#83C9FF",
        "#FF2B2B",
        "#FFABAB",
        "#29B09D",
        "#7DE3D1",
        "#6D3FC0",
        "#B8A1E3",
    ]
    group_range = [
        color_palette[index % len(color_palette)]
        for index in range(len(group_domain))
    ]
    available_dash_ranges = [
        [1, 0],
        [7, 4],
        [2, 3],
        [10, 3, 2, 3],
        [12, 4],
    ]
    dash_range = [
        available_dash_ranges[
            index % len(available_dash_ranges)
        ]
        for index in range(len(metric_domain))
    ]
    legend_symbols = [
        "━━━━",
        "┄ ┄ ┄",
        "· · · ·",
        "━ · ━ ·",
        "━━  ━━",
    ]

    def show_custom_legend():
        st.markdown("**Csoport**")
        for label, color in zip(group_domain, group_range):
            safe_label = html.escape(str(label))
            st.markdown(
                f'<span style="color:{color};font-size:1.2rem">'
                f'●</span>&nbsp; {safe_label}',
                unsafe_allow_html=True,
            )
        st.markdown("**Mutató**")
        for index, label in enumerate(metric_domain):
            symbol = legend_symbols[
                index % len(legend_symbols)
            ]
            st.markdown(
                f"{symbol}&nbsp; {html.escape(str(label))}",
                unsafe_allow_html=True,
            )

    separate = (
        chart_layout == "separate"
        or len(axes) > 2
        or series_count > 8
    )
    if separate:
        chart_column, legend_column = st.columns([5, 1.15])
        with chart_column:
            for metric_label in data["Metric"].drop_duplicates():
                metric_data = data[data["Metric"] == metric_label]
                axis_name = metric_data["Axis"].iloc[0]
                st.markdown(f"**{metric_label}**")
                st.altair_chart(
                    _time_series_layer(
                        metric_data,
                        axis_name,
                        metric_domain,
                        dash_range,
                        group_domain,
                        group_range,
                    ),
                    width="stretch",
                )
        with legend_column:
            show_custom_legend()
        return

    chart = _time_series_layer(
        data,
        axes[0],
        metric_domain,
        dash_range,
        group_domain,
        group_range,
    )
    if len(axes) == 2:
        chart = alt.layer(
            chart,
            _time_series_layer(
                data,
                axes[1],
                metric_domain,
                dash_range,
                group_domain,
                group_range,
                orient="right",
            ),
        ).resolve_scale(y="independent")

    chart_column, legend_column = st.columns([5, 1.15])
    with chart_column:
        st.altair_chart(chart, width="stretch")
    with legend_column:
        show_custom_legend()


st.divider()
st.header("Kérdezd a HR-adatokat")

st.caption(
    "Fejlesztési teszt: az AI értelmezi a kérdést, "
    "a már bekötött mutatókat pedig az alkalmazás "
    "az adatbázisból számítja ki."
)

ai_interpretation_enabled = st.toggle(
    "AI-alapú szöveges értelmezés",
    value=False,
    help=(
        "Bekapcsolva az aggregált eredményekből rövid "
        "értelmezést készít. Ez további AI-kvótát használ."
    ),
)

if "pending_ai_question" not in st.session_state:
    st.session_state.pending_ai_question = None

if "pending_clarification_question" not in st.session_state:
    st.session_state.pending_clarification_question = None

if "clarification_round" not in st.session_state:
    st.session_state.clarification_round = 0

is_clarification = (
    st.session_state.pending_ai_question is not None
)


def set_ai_example_question(question):
    st.session_state.ai_question = question

if is_clarification:
    st.markdown("**Eredeti kérdés:**")
    st.markdown(
        f"> {st.session_state.pending_ai_question}"
    )
    st.info(
        st.session_state.pending_clarification_question
        or "Kérlek, pontosítsd a kérésedet."
    )
    ai_question = st.text_area(
        "Válasz a pontosító kérdésre",
        placeholder="Írd ide a pontosítást...",
        key=(
            "ai_clarification_answer_"
            f"{st.session_state.clarification_round}"
        ),
    )
else:
    example_questions = (
        (
            "Mit kérdezhetek?",
            "Milyen kérdéseket tehetek fel?",
        ),
        (
            "Milyen idősorok vannak?",
            "Milyen idősorokat tudsz mutatni?",
        ),
        (
            "Munkaerő-elemzések",
            "Milyen jellemzőket tudsz elemezni a "
            "munkavállalókkal kapcsolatban?"
        ),
        (
            "Engagement-elemzések",
            "Milyen jellemzőket tudsz elemezni az "
            "engagementtel kapcsolatban?"
        ),
        (
            "Képzési elemzések",
            "Milyen jellemzőket tudsz elemezni a "
            "képzésekkel kapcsolatban?"
        ),
    )
    example_columns = st.columns(5)
    for question_index, (
        column,
        (button_label, example_question),
    ) in enumerate(zip(example_columns, example_questions)):
        column.button(
            button_label,
            key=f"ai_example_{question_index}",
            on_click=set_ai_example_question,
            args=(example_question,),
            use_container_width=True,
        )

    ai_question = st.text_area(
        "Mit szeretnél megtudni?",
        placeholder=(
            "Például: Mennyi volt az átlagos "
            "létszám 2026 első félévében?"
        ),
        key="ai_question",
    )

if st.button(
    (
        "Pontosítás elküldése"
        if is_clarification
        else "Kérdés értelmezése"
    ),
    key=(
        "ai_clarification_button"
        if is_clarification
        else "ai_question_button"
    )
):
    if not ai_question.strip():
        st.warning("Írj be egy kérdést vagy pontosítást.")

    elif (
        not is_clarification
        and (
            capability_answer := get_local_capability_answer(
                ai_question
            )
        )
    ):
        st.markdown(capability_answer)

    elif (
        not is_clarification
        and (
            training_type_question := (
                get_training_type_clarification(ai_question)
            )
        )
    ):
        st.session_state.pending_ai_question = ai_question
        st.session_state.pending_clarification_question = (
            training_type_question
        )
        st.session_state.clarification_round += 1
        st.rerun()

    elif not st.secrets.get("GEMINI_API_KEY"):
        st.error("A Gemini API-kulcs nincs beállítva.")

    else:
        if is_clarification:
            question_for_planning = (
                "Eredeti kérdés:\n"
                f"{st.session_state.pending_ai_question}\n\n"
                "Felhasználói pontosítás:\n"
                f"{ai_question}"
            )
        else:
            question_for_planning = ai_question

        try:
            with st.spinner("A kérdés értelmezése..."):
                question_plan = plan_question(
                    question_for_planning,
                    st.secrets["GEMINI_API_KEY"]
                )

            if question_plan.status == "answerable":
                st.session_state.pending_ai_question = None
                st.session_state.pending_clarification_question = None

                if not question_plan.metric_names:
                    st.warning(
                        "Az AI nem választott számítható mutatót."
                    )

                else:
                    if question_plan.filters:
                        ai_filter_date = (
                            question_plan.end_date
                            or reference_date
                        )
                        (
                            analysis_employees,
                            analysis_engagement,
                            analysis_training,
                            analysis_filter_label,
                        ) = apply_question_filters(
                            all_employees,
                            all_engagement,
                            all_training,
                            question_plan.filters,
                            ai_filter_date,
                        )
                    else:
                        analysis_employees = all_employees
                        analysis_engagement = all_engagement
                        analysis_training = all_training
                        analysis_filter_label = "Teljes vállalat"

                    unsupported_metrics = [
                        metric_name
                        for metric_name in question_plan.metric_names
                        if metric_name not in SUPPORTED_METRICS
                    ]

                    if unsupported_metrics:
                        st.info(
                            "A következő mutatók számítása még "
                            "nincs bekötve: "
                            + ", ".join(unsupported_metrics)
                        )

                    interpretation_payload = []
                    combined_time_series_rendered = False
                    workforce_composition_rendered = False

                    for selected_metric in (
                        question_plan.metric_names
                    ):
                        if selected_metric not in SUPPORTED_METRICS:
                            continue

                        employee_composition_fields = {
                            "DepartmentType",
                            "GenderCode",
                            "Generation",
                            "AgeGroup",
                        }
                        if (
                            not workforce_composition_rendered
                            and selected_metric == "ClosingHeadcount"
                            and question_plan.groupings
                            and question_plan.groupings[0].field
                            in employee_composition_fields
                            and question_plan.chart_type
                            in {"pie", "stacked", "stacked_100"}
                        ):
                            grouping = question_plan.groupings[0]
                            composition_end = (
                                question_plan.end_date
                                or reference_date
                            )
                            composition_start = (
                                question_plan.start_date
                                or composition_end
                            )
                            composition_data = (
                                build_workforce_composition(
                                    analysis_employees,
                                    grouping.field,
                                    grouping.values,
                                    composition_start,
                                    composition_end,
                                    question_plan.time_granularity,
                                )
                            )
                            workforce_composition_rendered = True
                            title = (
                                "Munkavállalói összetétel"
                                if question_plan.chart_type == "pie"
                                else "Munkavállalói összetétel időbeli alakulása"
                            )
                            st.success(f"**{title}**")
                            render_workforce_composition(
                                composition_data,
                                question_plan.chart_type,
                                grouping.field,
                            )
                            with st.expander("Részletes adatok"):
                                st.dataframe(
                                    composition_data,
                                    hide_index=True,
                                    use_container_width=True,
                                )
                            st.caption(
                                "Az 1–3 fős csoporteredmények nem jelennek meg."
                            )
                            interpretation_payload.append({
                                "type": "workforce_composition",
                                "grouping": grouping.field,
                                "data": composition_data.to_dict(
                                    orient="records"
                                ),
                            })
                            continue

                        if question_plan.output_type == "time_series":
                            if combined_time_series_rendered:
                                continue

                            requested_supported_metrics = {
                                metric_name
                                for metric_name in question_plan.metric_names
                                if metric_name in SUPPORTED_METRICS
                            }
                            requested_training_metrics = (
                                requested_supported_metrics
                                & TRAINING_TIME_SERIES_METRICS
                            )
                            if (
                                requested_training_metrics
                                and requested_training_metrics
                                != requested_supported_metrics
                            ):
                                raise ValueError(
                                    "Az engagement- és képzési idősorok "
                                    "eltérő időalapúak, ezért külön ábrán "
                                    "kell megjeleníteni őket."
                                )

                            is_training_time_series = bool(
                                requested_training_metrics
                            )
                            if is_training_time_series:
                                time_series_data = (
                                    build_combined_training_time_series(
                                        question_plan,
                                        analysis_employees,
                                        analysis_training,
                                        analysis_filter_label,
                                    )
                                )
                            else:
                                time_series_data = (
                                    build_combined_engagement_time_series(
                                        question_plan,
                                        analysis_employees,
                                        analysis_engagement,
                                        analysis_filter_label,
                                    )
                                )
                            combined_time_series_rendered = True

                            st.success(
                                "**A kért mutatók időbeli alakulása**"
                            )
                            render_combined_time_series(
                                time_series_data,
                                question_plan.chart_layout,
                            )
                            with st.expander("Idősoros adatok"):
                                table_columns = [
                                    column for column in [
                                        "PeriodLabel",
                                        "Metric",
                                        "Group",
                                        "Value",
                                        "Unit",
                                        "RespondentCount",
                                        "ParticipantCount",
                                        "RecordCount",
                                    ]
                                    if column in time_series_data.columns
                                ]
                                st.dataframe(
                                    time_series_data[table_columns],
                                    hide_index=True,
                                    use_container_width=True,
                                )
                            if is_training_time_series:
                                st.caption(
                                    "Az 1–3 résztvevőt vagy érvényes "
                                    "visszajelzést tartalmazó képzési "
                                    "csoportpontok nem jelennek meg."
                                )
                            else:
                                st.caption(
                                    "Az 1–3 érvényes választ tartalmazó "
                                    "csoportpontok nem jelennek meg. A "
                                    "kilépői csoportoknál csak a teljes "
                                    "követési idővel rendelkező hullámok "
                                    "szerepelnek."
                                )
                            interpretation_payload.append({
                                "type": "combined_time_series",
                                "data": time_series_data.to_dict(
                                    orient="records"
                                ),
                            })
                            continue

                        if question_plan.output_type == "time_series":
                            grouped_time_series = bool(
                                question_plan.groupings
                            )

                            if grouped_time_series:
                                grouping = question_plan.groupings[0]
                                grouping_field = grouping.field
                                dimensioned_employees = (
                                    add_demographic_dimensions(
                                        analysis_employees,
                                        question_plan.end_date,
                                    )
                                )
                                requested_group_values = (
                                    grouping.values
                                )
                                available_group_values = sorted(
                                    dimensioned_employees[
                                        grouping_field
                                    ].dropna().unique()
                                )
                                if requested_group_values:
                                    available_group_values = [
                                        value
                                        for value in available_group_values
                                        if value in requested_group_values
                                    ]
                                grouped_records = []

                                for group_value in available_group_values:
                                    group_employees = (
                                        dimensioned_employees[
                                            dimensioned_employees[
                                                grouping_field
                                            ] == group_value
                                        ]
                                    )
                                    group_ids = set(
                                        group_employees["EmpID"]
                                    )
                                    group_engagement = (
                                        analysis_engagement[
                                            analysis_engagement[
                                                "EmpID"
                                            ].isin(group_ids)
                                        ]
                                    )

                                    try:
                                        group_result = (
                                            calculate_engagement_time_series(
                                                selected_metric,
                                                group_employees,
                                                group_engagement,
                                                question_plan.start_date,
                                                question_plan.end_date,
                                            )
                                        )
                                    except ValueError:
                                        continue

                                    for record in group_result["records"]:
                                        if (
                                            record["RespondentCount"]
                                            is not None
                                            and record["RespondentCount"] >= 4
                                        ):
                                            grouped_records.append({
                                                **record,
                                                "Group": group_value,
                                            })

                                if not grouped_records:
                                    raise ValueError(
                                        "Nincs megjeleníthető, legalább "
                                        "4 fős csoporteredmény."
                                    )

                                time_series_result = group_result
                                time_series_data = pd.DataFrame(
                                    grouped_records
                                )
                            else:
                                time_series_result = (
                                    calculate_engagement_time_series(
                                        selected_metric,
                                        analysis_employees,
                                        analysis_engagement,
                                        question_plan.start_date,
                                        question_plan.end_date,
                                    )
                                )
                                time_series_data = pd.DataFrame(
                                    time_series_result["records"]
                                )
                                time_series_data["Group"] = (
                                    analysis_filter_label
                                )

                            if "0–100" in time_series_result["unit"]:
                                time_series_domain = [50, 100]
                            elif time_series_result["unit"] == "százalék":
                                time_series_domain = [0, 100]
                            else:
                                time_series_domain = [1, 5]

                            time_series_chart = (
                                alt.Chart(time_series_data)
                                .mark_line(point=True)
                                .encode(
                                    x=alt.X(
                                        "SurveyWaveID:N",
                                        title="Felmérési hullám",
                                        axis=alt.Axis(
                                            labelAngle=-45,
                                        ),
                                        sort=alt.SortField(
                                            field="SurveyLaunchDate",
                                            order="ascending",
                                        ),
                                    ),
                                    y=alt.Y(
                                        "Value:Q",
                                        title=time_series_result[
                                            "unit"
                                        ],
                                        scale=alt.Scale(
                                            domain=time_series_domain,
                                            zero=False,
                                        ),
                                    ),
                                    color=alt.Color(
                                        "Group:N",
                                        title=(
                                            grouping_field
                                            if grouped_time_series
                                            else None
                                        ),
                                        legend=(
                                            alt.Legend()
                                            if grouped_time_series
                                            else None
                                        ),
                                    ),
                                    tooltip=[
                                        alt.Tooltip(
                                            "SurveyWaveID:N",
                                            title="Hullám",
                                        ),
                                        alt.Tooltip(
                                            "SurveyLaunchDate:T",
                                            title="Indulás",
                                            format="%Y-%m-%d",
                                        ),
                                        alt.Tooltip(
                                            "Value:Q",
                                            title="Érték",
                                            format=".1f",
                                        ),
                                        alt.Tooltip(
                                            "Group:N",
                                            title="Csoport",
                                        ),
                                        alt.Tooltip(
                                            "RespondentCount:Q",
                                            title="Érvényes válaszok",
                                            format=",.0f",
                                        ),
                                    ]
                                )
                                .properties(height=350)
                            )

                            st.success(
                                f"**{time_series_result['label']} "
                                "időbeli alakulása**"
                            )
                            st.altair_chart(
                                time_series_chart,
                                width="stretch"
                            )
                            if grouped_time_series:
                                with st.expander(
                                    "Idősoros adatok"
                                ):
                                    st.dataframe(
                                        time_series_data[[
                                            "SurveyWaveID",
                                            "Group",
                                            "Value",
                                            "RespondentCount",
                                        ]],
                                        hide_index=True,
                                        use_container_width=True,
                                    )
                                st.caption(
                                    "Az 1–3 érvényes választ "
                                    "tartalmazó csoportpontok nem "
                                    "jelennek meg."
                                )
                            else:
                                change_value = (
                                    time_series_result["change"]
                                )
                                st.caption(
                                    f"Változás az első és utolsó "
                                    f"hullám között: {change_value:+.1f} "
                                    f"indexpont · Szűrés: "
                                    f"{analysis_filter_label}"
                                )
                            interpretation_payload.append({
                                "metric": time_series_result["label"],
                                "unit": time_series_result["unit"],
                                "type": "time_series",
                                "data": time_series_data.to_dict(
                                    orient="records"
                                ),
                            })
                            continue

                        if question_plan.groupings:
                            grouping = question_plan.groupings[0]
                            grouping_field = grouping.field
                            grouping_date = (
                                question_plan.end_date
                                or reference_date
                            )
                            training_group_fields = {
                                "TrainingCategory",
                                "TrainingProgramName",
                                "TrainingPurpose",
                                "TrainingType",
                                "DeliveryMode",
                            }
                            if grouping_field in training_group_fields:
                                group_values = sorted(
                                    analysis_training[
                                        grouping_field
                                    ].dropna().unique()
                                )
                            else:
                                dimensioned_employees = (
                                    add_demographic_dimensions(
                                        analysis_employees,
                                        grouping_date,
                                    )
                                )
                                group_values = sorted(
                                    dimensioned_employees[
                                        grouping_field
                                    ].dropna().unique()
                                )
                            requested_values = (
                                grouping.values
                            )
                            if requested_values:
                                group_values = [
                                    value
                                    for value in group_values
                                    if value in requested_values
                                ]

                            comparison_records = []
                            for group_value in group_values:
                                if grouping_field in training_group_fields:
                                    group_employees = analysis_employees
                                    group_engagement = analysis_engagement
                                    group_training = analysis_training[
                                        analysis_training[grouping_field]
                                        == group_value
                                    ]
                                else:
                                    group_employees = (
                                        dimensioned_employees[
                                            dimensioned_employees[
                                                grouping_field
                                            ] == group_value
                                        ]
                                    )
                                    group_ids = set(
                                        group_employees["EmpID"]
                                    )
                                    group_engagement = (
                                        analysis_engagement[
                                            analysis_engagement[
                                                "EmpID"
                                            ].isin(group_ids)
                                        ]
                                    )
                                    group_training = (
                                        analysis_training[
                                            analysis_training[
                                                "EmpID"
                                            ].isin(group_ids)
                                        ]
                                    )

                                group_metric_result = calculate_metric(
                                    selected_metric,
                                    group_employees,
                                    question_plan.start_date,
                                    question_plan.end_date,
                                    engagement=group_engagement,
                                    training=group_training,
                                )
                                sample_size = group_metric_result.get(
                                    "valid_response_count"
                                )
                                if sample_size is None:
                                    sample_size = (
                                        group_training["EmpID"].nunique()
                                        if grouping_field
                                        in training_group_fields
                                        else group_employees[
                                            "EmpID"
                                        ].nunique()
                                    )
                                if sample_size >= 4:
                                    comparison_records.append({
                                        "Csoport": group_value,
                                        "Érték": group_metric_result[
                                            "value"
                                        ],
                                        "Elemszám": sample_size,
                                    })

                            if not comparison_records:
                                raise ValueError(
                                    "Nincs megjeleníthető, legalább "
                                    "4 fős csoporteredmény."
                                )

                            comparison_data = pd.DataFrame(
                                comparison_records
                            )
                            comparison_chart = (
                                alt.Chart(comparison_data)
                                .mark_bar()
                                .encode(
                                    x=alt.X(
                                        "Csoport:N",
                                        title=None,
                                        sort="-y",
                                        axis=alt.Axis(labelAngle=-30),
                                    ),
                                    y=alt.Y(
                                        "Érték:Q",
                                        title=group_metric_result["unit"],
                                        scale=alt.Scale(zero=False),
                                    ),
                                    tooltip=[
                                        alt.Tooltip(
                                            "Csoport:N",
                                            title="Csoport",
                                        ),
                                        alt.Tooltip(
                                            "Érték:Q",
                                            title="Érték",
                                            format=".1f",
                                        ),
                                        alt.Tooltip(
                                            "Elemszám:Q",
                                            title="Elemszám",
                                            format=",.0f",
                                        ),
                                    ]
                                )
                                .properties(height=350)
                            )
                            st.success(
                                f"**{group_metric_result['label']} "
                                f"– összehasonlítás**"
                            )
                            st.altair_chart(
                                comparison_chart,
                                width="stretch"
                            )
                            st.dataframe(
                                comparison_data,
                                hide_index=True,
                                use_container_width=True,
                            )
                            st.caption(
                                "Az 1–3 fős csoporteredmények nem "
                                "jelennek meg."
                            )
                            interpretation_payload.append({
                                "metric": group_metric_result["label"],
                                "unit": group_metric_result["unit"],
                                "type": "group_comparison",
                                "data": comparison_records,
                            })
                            continue

                        metric_result = calculate_metric(
                            selected_metric,
                            analysis_employees,
                            question_plan.start_date,
                            question_plan.end_date,
                            engagement=analysis_engagement,
                            training=analysis_training
                        )
                        metric_value = metric_result["value"]
                        metric_definition = get_metric(
                            selected_metric
                        )
                        decimals = metric_definition.get(
                            "rounding",
                            {}
                        ).get("decimals", 0)

                        if isinstance(metric_value, dict):
                            grouped_result = pd.DataFrame(
                                metric_value.items(),
                                columns=["Csoport", "Érték"]
                            )
                            grouped_result["Érték"] = (
                                grouped_result["Érték"].round(2)
                            )

                            st.success(
                                f"**{metric_result['label']}**"
                            )
                            st.dataframe(
                                grouped_result,
                                hide_index=True,
                                use_container_width=True,
                                column_config={
                                    "Érték": st.column_config.NumberColumn(
                                        "Költség (USD)",
                                        format="%.2f"
                                    )
                                }
                            )

                        elif metric_result["unit"] == "százalék":
                            formatted_value = (
                                f"{metric_value:.{decimals}f}"
                                .replace(".", ",")
                            )
                            displayed_unit = "%"

                        elif selected_metric in {
                            "AverageHeadcount",
                            "OpeningClosingAverageHeadcount",
                        }:
                            formatted_value = (
                                f"{metric_value:,.{decimals}f}"
                                .replace(",", " ")
                                .replace(".", ",")
                            )
                            displayed_unit = metric_result["unit"]

                        else:
                            formatted_value = (
                                f"{metric_value:,.{decimals}f}"
                                .replace(",", " ")
                                .replace(".", ",")
                            )
                            displayed_unit = metric_result["unit"]

                        if not isinstance(metric_value, dict):
                            st.success(
                                f"**{metric_result['label']}: "
                                f"{formatted_value} "
                                f"{displayed_unit}**"
                            )

                        interpretation_payload.append({
                            "metric": metric_result["label"],
                            "unit": metric_result["unit"],
                            "type": (
                                "grouped_table"
                                if isinstance(metric_value, dict)
                                else "single_value"
                            ),
                            "value": metric_value,
                            "valid_response_count": (
                                metric_result.get(
                                    "valid_response_count"
                                )
                            ),
                        })

                        st.caption(
                            f"Időszak: "
                            f"{metric_result['start_date']} – "
                            f"{metric_result['end_date']} · "
                            f"Szűrés: "
                            f"{analysis_filter_label}"
                        )

                    if (
                        ai_interpretation_enabled
                        and interpretation_payload
                    ):
                        with st.spinner(
                            "AI-értelmezés készítése..."
                        ):
                            interpretation_text = interpret_results(
                                question_for_planning,
                                interpretation_payload,
                                st.secrets["GEMINI_API_KEY"],
                            )
                        st.info(interpretation_text)

            elif (
                question_plan.status
                == "clarification_needed"
            ):
                st.session_state.pending_ai_question = (
                    question_for_planning
                )
                st.session_state.pending_clarification_question = (
                    question_plan.clarification_question
                )
                st.session_state.clarification_round += 1
                st.rerun()

            else:
                st.session_state.pending_ai_question = None
                st.session_state.pending_clarification_question = None
                st.warning(question_plan.reason)

            with st.expander("Értelmezési részletek"):
                st.json(question_plan.model_dump())

        except Exception as exc:
            st.error(
                "Az AI-szolgáltatás átmenetileg "
                f"nem érhető el: {exc}"
            )
