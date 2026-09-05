import pandas as pd

from catalog_service import get_metric


SUPPORTED_METRICS = {
    "ClosingHeadcount",
    "OpeningHeadcount",
    "AverageHeadcount",
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


def calculate_metric(
    metric_name,
    employees,
    start_date=None,
    end_date=None
):
    metric = get_metric(metric_name)

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

    else:
        raise NotImplementedError(
            f"A metrika számítása még nincs "
            f"implementálva: {metric_name}"
        )

    return {
        "metric_name": metric_name,
        "label": metric["label"],
        "value": value,
        "unit": metric["unit"],
        "start_date": (
            str(start_date) if start_date else None
        ),
        "end_date": (
            str(end_date) if end_date else None
        ),
    }
