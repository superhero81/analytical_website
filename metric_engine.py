import pandas as pd

from catalog_service import get_metric


SUPPORTED_METRICS = {
    "ClosingHeadcount",
    "OpeningHeadcount",
    "AverageHeadcount",
    "OpeningClosingAverageHeadcount",
    "HireCount",
    "ExitCount",
    "TotalTurnoverRate",
    "VoluntaryTurnoverRate",
    "InvoluntaryTurnoverRate",
    "Rolling12MonthTurnoverRate",
    "Rolling3MonthTurnoverRate",
    "RetirementExitRate",
    "AverageEngagementScore",
    "AverageEngagementIndex",
    "AverageSatisfactionScore",
    "AverageSatisfactionIndex",
    "AverageWorkLifeBalanceScore",
    "AverageWorkLifeBalanceIndex",
    "CompositeEngagementIndex",
    "EngagementTop2BoxRate",
    "EngagementLow2BoxRate",
    "SatisfactionTop2BoxRate",
    "SatisfactionLow2BoxRate",
    "WorkLifeBalanceTop2BoxRate",
    "WorkLifeBalanceLow2BoxRate",
    "SurveyResponseRate",
    "EngagementIndexChange",
    "SatisfactionIndexChange",
    "WorkLifeBalanceIndexChange",
    "PooledAverageEngagementIndex",
    "PooledAverageSatisfactionIndex",
    "PooledAverageWorkLifeBalanceIndex",
    "PooledCompositeEngagementIndex",
    "TrainingParticipationRate",
    "TrainingCompletionRate",
    "SuccessfulTrainingCoverage",
    "AssessmentPassRate",
    "TrainingFeedbackResponseRate",
    "AverageOverallSatisfactionScore",
    "AverageOverallSatisfactionIndex",
    "AverageTrainerEvaluationScore",
    "AverageTrainerEvaluationIndex",
    "AverageJobRelevanceScore",
    "AverageJobRelevanceIndex",
    "AveragePersonalRelevanceScore",
    "AveragePersonalRelevanceIndex",
    "AverageDigitalContentUsabilityScore",
    "AverageDigitalContentUsabilityIndex",
    "OverallSatisfactionTop2BoxRate",
    "OverallSatisfactionLow2BoxRate",
    "TrainerEvaluationTop2BoxRate",
    "TrainerEvaluationLow2BoxRate",
    "JobRelevanceTop2BoxRate",
    "JobRelevanceLow2BoxRate",
    "PersonalRelevanceTop2BoxRate",
    "PersonalRelevanceLow2BoxRate",
    "DigitalContentUsabilityTop2BoxRate",
    "DigitalContentUsabilityLow2BoxRate",
    "CostPerParticipant",
    "CostPerSuccessfulCompletion",
    "TrainingCostByProgram",
    "TrainingCostByProvider",
    "TrainingIncompleteRate",
    "TrainingCancellationRate",
    "TotalTrainingCost",
    "TrainingParticipantCount",
    "SuccessfulTrainingCompletionCount",
}


ENGAGEMENT_SCORE_FIELDS = {
    "AverageEngagementScore": "EngagementScore",
    "AverageSatisfactionScore": "SatisfactionScore",
    "AverageWorkLifeBalanceScore": "WorkLifeBalanceScore",
}

ENGAGEMENT_INDEX_FIELDS = {
    "AverageEngagementIndex": "EngagementScore",
    "AverageSatisfactionIndex": "SatisfactionScore",
    "AverageWorkLifeBalanceIndex": "WorkLifeBalanceScore",
}

ENGAGEMENT_BOX_METRICS = {
    "EngagementTop2BoxRate": ("EngagementScore", {4, 5}),
    "EngagementLow2BoxRate": ("EngagementScore", {1, 2}),
    "SatisfactionTop2BoxRate": ("SatisfactionScore", {4, 5}),
    "SatisfactionLow2BoxRate": ("SatisfactionScore", {1, 2}),
    "WorkLifeBalanceTop2BoxRate": (
        "WorkLifeBalanceScore",
        {4, 5},
    ),
    "WorkLifeBalanceLow2BoxRate": (
        "WorkLifeBalanceScore",
        {1, 2},
    ),
}

POOLED_INDEX_FIELDS = {
    "PooledAverageEngagementIndex": "EngagementScore",
    "PooledAverageSatisfactionIndex": "SatisfactionScore",
    "PooledAverageWorkLifeBalanceIndex": "WorkLifeBalanceScore",
}

CHANGE_INDEX_FIELDS = {
    "EngagementIndexChange": "EngagementScore",
    "SatisfactionIndexChange": "SatisfactionScore",
    "WorkLifeBalanceIndexChange": "WorkLifeBalanceScore",
}

TRAINING_SCORE_FIELDS = {
    "AverageOverallSatisfactionScore": (
        "OverallSatisfactionScore"
    ),
    "AverageTrainerEvaluationScore": (
        "TrainerEvaluationScore"
    ),
    "AverageJobRelevanceScore": "JobRelevanceScore",
    "AveragePersonalRelevanceScore": (
        "PersonalRelevanceScore"
    ),
    "AverageDigitalContentUsabilityScore": (
        "DigitalContentUsabilityScore"
    ),
}

TRAINING_INDEX_FIELDS = {
    "AverageOverallSatisfactionIndex": (
        "OverallSatisfactionScore"
    ),
    "AverageTrainerEvaluationIndex": (
        "TrainerEvaluationScore"
    ),
    "AverageJobRelevanceIndex": "JobRelevanceScore",
    "AveragePersonalRelevanceIndex": (
        "PersonalRelevanceScore"
    ),
    "AverageDigitalContentUsabilityIndex": (
        "DigitalContentUsabilityScore"
    ),
}

TRAINING_BOX_METRICS = {
    "OverallSatisfactionTop2BoxRate": (
        "OverallSatisfactionScore",
        {4, 5},
    ),
    "OverallSatisfactionLow2BoxRate": (
        "OverallSatisfactionScore",
        {1, 2},
    ),
    "TrainerEvaluationTop2BoxRate": (
        "TrainerEvaluationScore",
        {4, 5},
    ),
    "TrainerEvaluationLow2BoxRate": (
        "TrainerEvaluationScore",
        {1, 2},
    ),
    "JobRelevanceTop2BoxRate": (
        "JobRelevanceScore",
        {4, 5},
    ),
    "JobRelevanceLow2BoxRate": (
        "JobRelevanceScore",
        {1, 2},
    ),
    "PersonalRelevanceTop2BoxRate": (
        "PersonalRelevanceScore",
        {4, 5},
    ),
    "PersonalRelevanceLow2BoxRate": (
        "PersonalRelevanceScore",
        {1, 2},
    ),
    "DigitalContentUsabilityTop2BoxRate": (
        "DigitalContentUsabilityScore",
        {4, 5},
    ),
    "DigitalContentUsabilityLow2BoxRate": (
        "DigitalContentUsabilityScore",
        {1, 2},
    ),
}


def headcount_on_date(employees, date):
    date = pd.Timestamp(date)

    active_mask = (
        (employees["StartDate"] <= date)
        & (
            employees["ExitDate"].isna()
            | (employees["ExitDate"] > date)
        )
    )

    return employees.loc[
        active_mask,
        "EmpID"
    ].nunique()


def average_headcount_between(
    employees,
    start_date,
    end_date
):
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    if start_date > end_date:
        raise ValueError(
            "A kezdődátum nem lehet későbbi "
            "a záródátumnál."
        )

    days = pd.date_range(
        start=start_date,
        end=end_date,
        freq="D"
    )

    daily_headcounts = [
        headcount_on_date(employees, day)
        for day in days
    ]

    return sum(daily_headcounts) / len(
        daily_headcounts
    )


def hire_count(employees, start_date, end_date):
    mask = (
        (employees["StartDate"] >= start_date)
        & (employees["StartDate"] <= end_date)
    )

    return employees.loc[
        mask,
        "EmpID"
    ].nunique()


def exit_count(
    employees,
    start_date,
    end_date,
    statuses=None
):
    mask = (
        (employees["ExitDate"] >= start_date)
        & (employees["ExitDate"] <= end_date)
    )

    if statuses is not None:
        mask &= employees[
            "EmployeeStatus"
        ].isin(statuses)

    return employees.loc[
        mask,
        "EmpID"
    ].nunique()


def turnover_rate(
    employees,
    start_date,
    end_date,
    statuses=None
):
    exits = exit_count(
        employees,
        start_date,
        end_date,
        statuses
    )

    average_headcount = average_headcount_between(
        employees,
        start_date,
        end_date
    )

    if average_headcount == 0:
        return 0

    return exits / average_headcount * 100


def _prepare_engagement(engagement):
    if engagement is None:
        raise ValueError(
            "Az engagement-metrikához az engagement "
            "adatállomány is szükséges."
        )

    data = engagement.copy()
    data["SurveyLaunchDate"] = pd.to_datetime(
        data["SurveyLaunchDate"]
    )
    return data


def _waves_in_period(engagement, start_date, end_date):
    data = _prepare_engagement(engagement)

    if start_date is not None:
        data = data[
            data["SurveyLaunchDate"] >= start_date
        ]

    if end_date is not None:
        data = data[
            data["SurveyLaunchDate"] <= end_date
        ]

    return data


def _single_wave(engagement, start_date, end_date):
    data = _waves_in_period(
        engagement,
        start_date,
        end_date
    )

    launch_dates = sorted(
        data["SurveyLaunchDate"].dropna().unique()
    )

    if not launch_dates:
        raise ValueError(
            "A megadott időszakban nincs felmérési hullám."
        )

    if len(launch_dates) > 1:
        raise ValueError(
            "A megadott időszak több felmérési hullámot "
            "tartalmaz. Válassz egy hullámot, vagy kérj "
            "összevont mutatót."
        )

    launch_date = pd.Timestamp(launch_dates[0])
    return (
        data[data["SurveyLaunchDate"] == launch_date],
        launch_date,
    )


def _latest_wave(engagement, end_date=None):
    data = _prepare_engagement(engagement)

    if end_date is not None:
        data = data[
            data["SurveyLaunchDate"] <= end_date
        ]

    if data.empty:
        raise ValueError(
            "A megadott időpontig nincs felmérési hullám."
        )

    launch_date = data["SurveyLaunchDate"].max()
    return (
        data[data["SurveyLaunchDate"] == launch_date],
        launch_date,
    )


def _selected_wave(engagement, start_date, end_date):
    if start_date is None:
        return _latest_wave(engagement, end_date)

    return _single_wave(
        engagement,
        start_date,
        end_date
    )


def _valid_score_mean(data, field):
    values = data[field].dropna()
    if values.empty:
        raise ValueError(
            f"Nincs érvényes {field} érték."
        )
    return values.mean(), len(values)


def _score_to_index(score):
    return (score - 1) * 25


def _box_rate(data, field, accepted_values):
    values = data[field].dropna()
    if values.empty:
        raise ValueError(
            f"Nincs érvényes {field} érték."
        )
    return values.isin(accepted_values).mean() * 100, len(values)


def _change_between_waves(
    engagement,
    field,
    start_date,
    end_date
):
    all_data = _prepare_engagement(engagement)
    selected = _waves_in_period(
        engagement,
        start_date,
        end_date
    )
    selected_dates = sorted(
        selected["SurveyLaunchDate"].dropna().unique()
    )

    if not selected_dates:
        raise ValueError(
            "A megadott időszakban nincs felmérési hullám."
        )

    later_date = pd.Timestamp(selected_dates[-1])

    if len(selected_dates) >= 2:
        earlier_date = pd.Timestamp(selected_dates[0])
    else:
        previous_dates = all_data.loc[
            all_data["SurveyLaunchDate"] < later_date,
            "SurveyLaunchDate",
        ]
        if previous_dates.empty:
            raise ValueError(
                "A kiválasztott hullám előtt nincs "
                "összehasonlítható felmérési hullám."
            )
        earlier_date = previous_dates.max()

    earlier = all_data[
        all_data["SurveyLaunchDate"] == earlier_date
    ]
    later = all_data[
        all_data["SurveyLaunchDate"] == later_date
    ]
    earlier_mean, earlier_count = _valid_score_mean(
        earlier,
        field
    )
    later_mean, later_count = _valid_score_mean(
        later,
        field
    )

    return {
        "value": _score_to_index(later_mean)
        - _score_to_index(earlier_mean),
        "comparison_start_date": earlier_date,
        "comparison_end_date": later_date,
        "comparison_start_count": earlier_count,
        "comparison_end_count": later_count,
    }


def _training_in_period(training, start_date, end_date):
    if training is None:
        raise ValueError(
            "A képzési metrikához a képzési "
            "adatállomány is szükséges."
        )
    if start_date is None or end_date is None:
        raise ValueError(
            "A képzési metrikához kezdő- és "
            "záródátum szükséges."
        )

    data = training.copy()
    data["TrainingDate"] = pd.to_datetime(
        data["TrainingDate"]
    )
    return data[
        (data["TrainingDate"] >= start_date)
        & (data["TrainingDate"] <= end_date)
    ]


def _eligible_employee_count(
    employees,
    start_date,
    end_date
):
    mask = (
        (employees["StartDate"] <= end_date)
        & (
            employees["ExitDate"].isna()
            | (employees["ExitDate"] > start_date)
        )
    )
    return employees.loc[mask, "EmpID"].nunique()


def _rate(numerator, denominator):
    return (
        numerator / denominator * 100
        if denominator > 0
        else 0
    )


def calculate_metric(
    metric_name,
    employees,
    start_date=None,
    end_date=None,
    engagement=None,
    training=None
):
    metric = get_metric(metric_name)

    if end_date is not None:
        end_date = pd.Timestamp(end_date)

    if start_date is not None:
        start_date = pd.Timestamp(start_date)

    if metric_name == "Rolling12MonthTurnoverRate":
        if end_date is None:
            raise ValueError(
                "A gördülő fluktuációhoz "
                "záródátum szükséges."
            )

        start_date = (
            end_date
            - pd.DateOffset(years=1)
            + pd.Timedelta(days=1)
        )

    elif metric_name == "Rolling3MonthTurnoverRate":
        if end_date is None:
            raise ValueError(
                "A gördülő fluktuációhoz "
                "záródátum szükséges."
            )

        start_date = (
            end_date
            - pd.DateOffset(months=3)
            + pd.Timedelta(days=1)
        )

    if metric_name == "ClosingHeadcount":
        if end_date is None:
            raise ValueError(
                "A zárónapi létszámhoz dátum szükséges."
            )

        value = headcount_on_date(
            employees,
            end_date
        )

    elif metric_name == "OpeningHeadcount":
        if start_date is None:
            raise ValueError(
                "A nyitónapi létszámhoz dátum szükséges."
            )

        value = headcount_on_date(
            employees,
            start_date
        )

    elif metric_name == "AverageHeadcount":
        if start_date is None or end_date is None:
            raise ValueError(
                "Az átlagos létszámhoz "
                "kezdő- és záródátum szükséges."
            )

        value = average_headcount_between(
            employees,
            start_date,
            end_date
        )

    elif metric_name == "OpeningClosingAverageHeadcount":
        if start_date is None or end_date is None:
            raise ValueError(
                "A mutatóhoz kezdő- és "
                "záródátum szükséges."
            )

        value = (
            headcount_on_date(employees, start_date)
            + headcount_on_date(employees, end_date)
        ) / 2

    elif metric_name == "HireCount":
        if start_date is None or end_date is None:
            raise ValueError(
                "A belépők számához időszak szükséges."
            )

        value = hire_count(
            employees,
            start_date,
            end_date
        )

    elif metric_name == "ExitCount":
        if start_date is None or end_date is None:
            raise ValueError(
                "A kilépők számához időszak szükséges."
            )

        value = exit_count(
            employees,
            start_date,
            end_date
        )

    elif metric_name in {
        "TotalTurnoverRate",
        "Rolling12MonthTurnoverRate",
        "Rolling3MonthTurnoverRate",
    }:
        if start_date is None or end_date is None:
            raise ValueError(
                "A fluktuációhoz időszak szükséges."
            )

        value = turnover_rate(
            employees,
            start_date,
            end_date
        )

    elif metric_name == "VoluntaryTurnoverRate":
        if start_date is None or end_date is None:
            raise ValueError(
                "A fluktuációhoz időszak szükséges."
            )

        value = turnover_rate(
            employees,
            start_date,
            end_date,
            statuses=["Voluntarily Terminated"]
        )

    elif metric_name == "InvoluntaryTurnoverRate":
        if start_date is None or end_date is None:
            raise ValueError(
                "A fluktuációhoz időszak szükséges."
            )

        value = turnover_rate(
            employees,
            start_date,
            end_date,
            statuses=["Terminated for Cause"]
        )

    elif metric_name == "RetirementExitRate":
        if start_date is None or end_date is None:
            raise ValueError(
                "A nyugdíjazási kilépési rátához "
                "időszak szükséges."
            )

        value = turnover_rate(
            employees,
            start_date,
            end_date,
            statuses=["Retired"]
        )

    elif metric_name in ENGAGEMENT_SCORE_FIELDS:
        wave, launch_date = _selected_wave(
            engagement,
            start_date,
            end_date
        )
        value, valid_response_count = _valid_score_mean(
            wave,
            ENGAGEMENT_SCORE_FIELDS[metric_name]
        )
        wave_id = wave["SurveyWaveID"].iloc[0]

    elif metric_name in ENGAGEMENT_INDEX_FIELDS:
        wave, launch_date = _selected_wave(
            engagement,
            start_date,
            end_date
        )
        score, valid_response_count = _valid_score_mean(
            wave,
            ENGAGEMENT_INDEX_FIELDS[metric_name]
        )
        value = _score_to_index(score)
        wave_id = wave["SurveyWaveID"].iloc[0]

    elif metric_name == "CompositeEngagementIndex":
        wave, launch_date = _selected_wave(
            engagement,
            start_date,
            end_date
        )
        fields = [
            "EngagementScore",
            "SatisfactionScore",
            "WorkLifeBalanceScore",
        ]
        complete = wave[fields].dropna()
        if complete.empty:
            raise ValueError(
                "Nincs mindhárom pontszámot tartalmazó válasz."
            )
        value = (
            complete.apply(_score_to_index).mean(axis=1).mean()
        )
        valid_response_count = len(complete)
        wave_id = wave["SurveyWaveID"].iloc[0]

    elif metric_name in ENGAGEMENT_BOX_METRICS:
        wave, launch_date = _selected_wave(
            engagement,
            start_date,
            end_date
        )
        field, accepted_values = ENGAGEMENT_BOX_METRICS[
            metric_name
        ]
        value, valid_response_count = _box_rate(
            wave,
            field,
            accepted_values
        )
        wave_id = wave["SurveyWaveID"].iloc[0]

    elif metric_name == "SurveyResponseRate":
        wave, launch_date = _selected_wave(
            engagement,
            start_date,
            end_date
        )
        respondent_count = wave["EmpID"].nunique()
        eligible_count = headcount_on_date(
            employees,
            launch_date
        )
        value = (
            respondent_count / eligible_count * 100
            if eligible_count > 0
            else 0
        )
        valid_response_count = respondent_count
        wave_id = wave["SurveyWaveID"].iloc[0]

    elif metric_name in CHANGE_INDEX_FIELDS:
        change = _change_between_waves(
            engagement,
            CHANGE_INDEX_FIELDS[metric_name],
            start_date,
            end_date
        )
        value = change["value"]

    elif metric_name in POOLED_INDEX_FIELDS:
        pooled = _waves_in_period(
            engagement,
            start_date,
            end_date
        )
        if pooled.empty:
            raise ValueError(
                "A megadott időszakban nincs felmérési adat."
            )
        score, valid_response_count = _valid_score_mean(
            pooled,
            POOLED_INDEX_FIELDS[metric_name]
        )
        value = _score_to_index(score)
        unique_employee_count = pooled["EmpID"].nunique()
        wave_count = pooled["SurveyWaveID"].nunique()

    elif metric_name == "PooledCompositeEngagementIndex":
        pooled = _waves_in_period(
            engagement,
            start_date,
            end_date
        )
        fields = [
            "EngagementScore",
            "SatisfactionScore",
            "WorkLifeBalanceScore",
        ]
        complete = pooled[fields].dropna()
        if complete.empty:
            raise ValueError(
                "Nincs mindhárom pontszámot tartalmazó válasz."
            )
        value = (
            complete.apply(_score_to_index).mean(axis=1).mean()
        )
        valid_response_count = len(complete)
        unique_employee_count = pooled.loc[
            complete.index,
            "EmpID",
        ].nunique()
        wave_count = pooled.loc[
            complete.index,
            "SurveyWaveID",
        ].nunique()

    elif metric_name in {
        "TrainingParticipationRate",
        "SuccessfulTrainingCoverage",
    }:
        period_training = _training_in_period(
            training,
            start_date,
            end_date
        )
        eligible_count = _eligible_employee_count(
            employees,
            start_date,
            end_date
        )
        required_status = (
            "Completed"
            if metric_name == "SuccessfulTrainingCoverage"
            else None
        )
        if required_status is None:
            relevant = period_training[
                period_training["CompletionStatus"]
                != "Cancelled"
            ]
        else:
            relevant = period_training[
                period_training["CompletionStatus"]
                == required_status
            ]
        participant_count = relevant["EmpID"].nunique()
        value = _rate(participant_count, eligible_count)

    elif metric_name in {
        "TrainingCompletionRate",
        "TrainingIncompleteRate",
    }:
        period_training = _training_in_period(
            training,
            start_date,
            end_date
        )
        started = period_training[
            period_training["CompletionStatus"].isin(
                ["Completed", "Incomplete"]
            )
        ]
        target_status = (
            "Completed"
            if metric_name == "TrainingCompletionRate"
            else "Incomplete"
        )
        value = _rate(
            (started["CompletionStatus"] == target_status).sum(),
            len(started),
        )

    elif metric_name == "TrainingCancellationRate":
        period_training = _training_in_period(
            training,
            start_date,
            end_date
        )
        valid_statuses = period_training[
            "CompletionStatus"
        ].dropna()
        value = _rate(
            (valid_statuses == "Cancelled").sum(),
            len(valid_statuses),
        )

    elif metric_name == "AssessmentPassRate":
        period_training = _training_in_period(
            training,
            start_date,
            end_date
        )
        assessed = period_training[
            period_training["TrainingResult"].isin(
                ["Passed", "Failed"]
            )
        ]
        value = _rate(
            (assessed["TrainingResult"] == "Passed").sum(),
            len(assessed),
        )

    elif metric_name == "TrainingFeedbackResponseRate":
        period_training = _training_in_period(
            training,
            start_date,
            end_date
        )
        eligible_feedback = period_training[
            period_training["CompletionStatus"] != "Cancelled"
        ]
        value = _rate(
            (
                eligible_feedback["FeedbackSubmitted"] == "Yes"
            ).sum(),
            len(eligible_feedback),
        )

    elif metric_name in TRAINING_SCORE_FIELDS:
        period_training = _training_in_period(
            training,
            start_date,
            end_date
        )
        value, valid_response_count = _valid_score_mean(
            period_training,
            TRAINING_SCORE_FIELDS[metric_name]
        )

    elif metric_name in TRAINING_INDEX_FIELDS:
        period_training = _training_in_period(
            training,
            start_date,
            end_date
        )
        score, valid_response_count = _valid_score_mean(
            period_training,
            TRAINING_INDEX_FIELDS[metric_name]
        )
        value = _score_to_index(score)

    elif metric_name in TRAINING_BOX_METRICS:
        period_training = _training_in_period(
            training,
            start_date,
            end_date
        )
        field, accepted_values = TRAINING_BOX_METRICS[
            metric_name
        ]
        value, valid_response_count = _box_rate(
            period_training,
            field,
            accepted_values
        )

    elif metric_name in {
        "CostPerParticipant",
        "CostPerSuccessfulCompletion",
        "TotalTrainingCost",
    }:
        period_training = _training_in_period(
            training,
            start_date,
            end_date
        )
        non_cancelled = period_training[
            period_training["CompletionStatus"] != "Cancelled"
        ]
        total_cost = non_cancelled["TrainingCostUSD"].sum()

        if metric_name == "TotalTrainingCost":
            value = total_cost
        elif metric_name == "CostPerParticipant":
            participant_total = non_cancelled["EmpID"].nunique()
            value = (
                total_cost / participant_total
                if participant_total > 0
                else 0
            )
        else:
            completed_count = (
                non_cancelled["CompletionStatus"] == "Completed"
            ).sum()
            value = (
                total_cost / completed_count
                if completed_count > 0
                else 0
            )

    elif metric_name in {
        "TrainingParticipantCount",
        "SuccessfulTrainingCompletionCount",
    }:
        period_training = _training_in_period(
            training,
            start_date,
            end_date
        )
        if metric_name == "TrainingParticipantCount":
            relevant = period_training[
                period_training["CompletionStatus"].isin(
                    ["Completed", "Incomplete"]
                )
            ]
            value = relevant["EmpID"].nunique()
        else:
            relevant = period_training[
                period_training["CompletionStatus"] == "Completed"
            ]
            value = relevant["TrainingRecordID"].nunique()

    elif metric_name in {
        "TrainingCostByProgram",
        "TrainingCostByProvider",
    }:
        period_training = _training_in_period(
            training,
            start_date,
            end_date
        )
        non_cancelled = period_training[
            period_training["CompletionStatus"] != "Cancelled"
        ]
        grouping_field = (
            "TrainingProgramName"
            if metric_name == "TrainingCostByProgram"
            else "TrainingProvider"
        )
        value = (
            non_cancelled.groupby(grouping_field)["TrainingCostUSD"]
            .sum()
            .sort_values(ascending=False)
            .to_dict()
        )

    else:
        raise NotImplementedError(
            f"A metrika számítása még nincs "
            f"implementálva: {metric_name}"
        )

    result = {
        "metric_name": metric_name,
        "label": metric["label"],
        "value": value,
        "unit": metric["unit"],
        "start_date": (
            start_date.date().isoformat()
            if start_date is not None
            else None
        ),
        "end_date": (
            end_date.date().isoformat()
            if end_date is not None
            else None
        ),
    }

    if "wave_id" in locals():
        result["wave_id"] = wave_id
        result["survey_launch_date"] = (
            launch_date.date().isoformat()
        )

    if "valid_response_count" in locals():
        result["valid_response_count"] = int(
            valid_response_count
        )

    if "unique_employee_count" in locals():
        result["unique_employee_count"] = int(
            unique_employee_count
        )

    if "wave_count" in locals():
        result["wave_count"] = int(wave_count)

    if "change" in locals():
        result.update({
            "comparison_start_date": change[
                "comparison_start_date"
            ].date().isoformat(),
            "comparison_end_date": change[
                "comparison_end_date"
            ].date().isoformat(),
            "comparison_start_count": change[
                "comparison_start_count"
            ],
            "comparison_end_count": change[
                "comparison_end_count"
            ],
        })

    return result

