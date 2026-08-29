from pathlib import Path

import pandas as pd
import streamlit as st
import altair as alt


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
    .st-key-reference_month {
    margin-bottom: -24px;
    }
}

    </style>
    """,
    unsafe_allow_html=True
)

DATA_FOLDER = Path("data/processed")


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


employees, engagement, training = load_data()

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

date_column, empty_column = st.columns([1, 2])

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


# Gördülő 12 hónap
period_12m_start = (
    reference_date - pd.DateOffset(years=1)
)

headcount_current = headcount_on_date(reference_date)
headcount_previous = headcount_on_date(period_12m_start)
headcount_change = (
    headcount_current - headcount_previous
)

hires_12m = (
    (employees["StartDate"] > period_12m_start)
    & (employees["StartDate"] <= reference_date)
).sum()

exits_12m_mask = (
    (employees["ExitDate"] > period_12m_start)
    & (employees["ExitDate"] <= reference_date)
)

exits_12m = exits_12m_mask.sum()

average_headcount = (
    headcount_previous + headcount_current
) / 2

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


# Gördülő 6 havi képzési részvétel
training_period_start = (
    selected_month - 5
).start_time.normalize()

training_6m = training[
    (training["TrainingDate"] >= training_period_start)
    & (training["TrainingDate"] <= reference_date)
]

trained_employees = training_6m[
    "EmpID"
].nunique()

eligible_for_training = (
    (employees["StartDate"] <= reference_date)
    & (
        employees["ExitDate"].isna()
        | (
            employees["ExitDate"]
            >= training_period_start
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
    training_6m["CompletionStatus"]
    == "Completed"
).sum()

incomplete_trainings = (
    training_6m["CompletionStatus"]
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
    title,
    value,
    detail
):
    is_selected = st.session_state.selected_kpi == key

    card_text = (
        f"{title}\n\n"
        f"**{value}**\n\n"
        f"_{detail}_"
    )

    if column.button(
        card_text,
        key=f"kpi_{key}",
        type="primary" if is_selected else "secondary",
        use_container_width=True
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
    engagement_card_value = f"{engagement_value:.2f} / 5"

training_card_value = (
    f"{training_participation_rate:.1f}%"
)

show_kpi_card(
    col1,
    "headcount",
    "Állományi létszám",
    headcount_card_value,
    f"{headcount_change:+} fő / 12 hó"
)

show_kpi_card(
    col2,
    "hires",
    "Belépők",
    hires_card_value,
    "Gördülő 12 hónap"
)

show_kpi_card(
    col3,
    "turnover",
    "Fluktuáció",
    turnover_card_value,
    f"Önkéntes: {voluntary_turnover_rate:.1f}%"
)

show_kpi_card(
    col4,
    "engagement",
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
    "Képzési részvétel",
    training_card_value,
    f"Teljesítés: {training_completion_rate:.1f}%"
)



st.subheader("Állományi létszám alakulása")

trend_months = pd.period_range(
    end=selected_month,
    periods=12,
    freq="M"
)

headcount_trend = pd.DataFrame({
    "Hónap": [
        month.end_time.normalize()
        for month in trend_months
    ],
    "Állományi létszám": [
        headcount_on_date(month.end_time.normalize())
        for month in trend_months
    ]
})

headcount_chart = (
    alt.Chart(headcount_trend)
    .mark_line(point=True)
    .encode(
        x=alt.X(
            "Hónap:T",
            title="Hónap",
            axis=alt.Axis(format="%Y-%m")
        ),
        y=alt.Y(
            "Állományi létszám:Q",
            title="Létszám",
            scale=alt.Scale(zero=False)
        ),
        tooltip=[
            alt.Tooltip("Hónap:T", title="Hónap", format="%Y. %B"),
            alt.Tooltip(
                "Állományi létszám:Q",
                title="Állományi létszám"
            )
        ]
    )
    .properties(height=350)
)

st.altair_chart(headcount_chart, width="stretch")

