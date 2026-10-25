import pandas as pd

from pln_rates.analysis import answers


def make_df():
    rows = []
    for i, rate in enumerate([4.0, 4.4, 4.2, 4.6]):
        rows.append((f"2026-01-0{i + 1}", "EUR", rate))
    for i, rate in enumerate([0.025, 0.024, 0.026]):
        rows.append((f"2026-01-0{i + 1}", "JPY", rate))
    df = pd.DataFrame(rows, columns=["date", "currency", "rate"])
    df["date"] = pd.to_datetime(df["date"])
    return df


def get(result, question, code):
    return result[(result["question"] == question) & (result["currency"] == code)].iloc[0]


def test_lowest_and_highest():
    result = answers(make_df())
    assert str(get(result, "lowest", "EUR")["date"]) == "2026-01-01"
    assert str(get(result, "highest", "EUR")["date"]) == "2026-01-04"


def test_biggest_one_day_moves():
    result = answers(make_df())
    assert str(get(result, "biggest one-day rise", "EUR")["date"]) == "2026-01-02"
    assert str(get(result, "biggest one-day fall", "EUR")["date"]) == "2026-01-03"


def test_currencies_are_not_mixed():
    # if JPY's first day were compared with EUR's last day, it would show a fake 99% fall
    result = answers(make_df())
    assert str(get(result, "biggest one-day fall", "JPY")["date"]) == "2026-01-02"


def test_tie_gives_earliest_date():
    df = pd.DataFrame({"date": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
                       "currency": "EUR", "rate": [4.0, 4.5, 4.0]})
    result = answers(df)
    assert str(get(result, "lowest", "EUR")["date"]) == "2026-01-01"