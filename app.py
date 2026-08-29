from pathlib import Path

import pandas as pd
import streamlit as st
import altair as alt


st.set_page_config(
    page_title="HR Insight AI",
    page_icon="📊",
    layout="wide"
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

date_column, empty_column = st.columns([1, 2])

with date_column:
    selected_month = st.selectbox(
        "Vizsgálati hónap",
        options=available_months,
        index=0,
        format_func=lambda period: (
            f"{period.year}. "
            f"{hungarian_months[period.month]}"
        )
    )

reference_date = selected_month.end_time.normalize()

st.title("HR Insight AI")
st.caption(
    "Referencia-időpont: "
    f"{reference_date.date()}"
)

st.write(
    "A KPI-k és elemzések a bal oldalon kiválasztott "
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

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Állományi létszám",
        f"{headcount_current:,}".replace(",", " "),
        delta=f"{headcount_change:+} fő / 12 hó"
    )
    st.caption(
        f"Állapot: {reference_date.date()}"
    )

with col2:
    st.metric(
        "Belépők",
        f"{hires_12m} fő"
    )
    st.caption("Gördülő 12 hónap")

with col3:
    st.metric(
        "Fluktuáció",
        f"{turnover_rate:.1f}%"
    )
    st.caption(
        "Gördülő 12 hónap · "
        f"önkéntes: {voluntary_turnover_rate:.1f}%"
    )

with col4:
    if engagement_value is None:
        st.metric("Engagement", "Nincs adat")
        st.caption(
            "A kiválasztott időpontig nincs felmérés"
        )
    else:
        st.metric(
            "Engagement",
            f"{engagement_value:.2f} / 5"
        )
        st.caption(
            f"{engagement_wave} · "
            f"n={engagement_respondents} · "
            f"válaszadás: "
            f"{engagement_response_rate:.1f}%"
        )

with col5:
    st.metric(
        "Képzési részvétel",
        f"{training_participation_rate:.1f}%"
    )
    st.caption(
        "Gördülő 6 hónap · "
        f"teljesítés: {training_completion_rate:.1f}%"
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

