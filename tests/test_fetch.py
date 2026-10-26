from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch
from zoneinfo import ZoneInfo

import pytest
import requests

from pln_rates import fetch


def response(status, rates=None):
    r = Mock()
    r.status_code = status
    r.json.return_value = {"rates": rates or []}
    return r


def test_windows():
    windows = fetch.make_windows(date(2021, 10, 26), date(2026, 10, 23))
    assert windows[0][0] == date(2021, 10, 26)
    assert windows[-1][1] == date(2026, 10, 23)
    for s, e in windows:
        assert (e - s).days + 1 <= 93
    for a, b in zip(windows, windows[1:]):
        assert b[0] == a[1] + timedelta(days=1)


def test_end_date_before_and_after_publication():
    before = datetime(2026, 10, 26, 11, 0, tzinfo=ZoneInfo("Europe/Warsaw"))
    after = datetime(2026, 10, 26, 13, 0, tzinfo=ZoneInfo("Europe/Warsaw"))
    assert fetch.default_end_date(before) == date(2026, 10, 25)
    assert fetch.default_end_date(after) == date(2026, 10, 26)


@patch("pln_rates.fetch.time.sleep")
@patch("pln_rates.fetch.requests.get")
def test_404_gives_empty_list(get, sleep):
    get.return_value = response(404)
    assert fetch.get_rates("EUR", date(2026, 1, 3), date(2026, 1, 4)) == []


@patch("pln_rates.fetch.time.sleep")
@patch("pln_rates.fetch.requests.get")
def test_400_raises(get, sleep):
    get.return_value = response(400)
    with pytest.raises(RuntimeError):
        fetch.get_rates("EUR", date(2026, 1, 1), date(2026, 1, 2))


@patch("pln_rates.fetch.time.sleep")
@patch("pln_rates.fetch.requests.get")
def test_retries_after_500(get, sleep):
    ok = response(200, [{"effectiveDate": "2026-01-02", "mid": 4.2}])
    get.side_effect = [response(500), ok]
    assert len(fetch.get_rates("EUR", date(2026, 1, 1), date(2026, 1, 2))) == 1


@patch("pln_rates.fetch.time.sleep")
@patch("pln_rates.fetch.requests.get")
def test_gives_up_after_timeouts(get, sleep):
    get.side_effect = requests.Timeout()
    with pytest.raises(RuntimeError):
        fetch.get_rates("EUR", date(2026, 1, 1), date(2026, 1, 2))
        

@patch("pln_rates.fetch.time.sleep")
@patch("pln_rates.fetch.requests.get")
def test_retries_after_429(get, sleep):
    ok = response(200, [{"effectiveDate": "2026-01-02", "mid": 4.2}])
    get.side_effect = [response(429), ok]
    assert len(fetch.get_rates("EUR", date(2026, 1, 1), date(2026, 1, 2))) == 1


@patch("pln_rates.fetch.time.sleep")
@patch("pln_rates.fetch.requests.get")
def test_response_without_rates_raises(get, sleep):
    bad = response(200)
    bad.json.return_value = {"something": "else"}
    get.return_value = bad
    with pytest.raises(RuntimeError, match="unexpected"):
        fetch.get_rates("EUR", date(2026, 1, 1), date(2026, 1, 2))


def rates_on(*days, mid=4.0):
    return [{"effectiveDate": d, "mid": mid} for d in days]


@patch("pln_rates.fetch.get_rates")
def test_fetch_all_removes_duplicates_and_sorts(get_rates):
    get_rates.return_value = rates_on("2026-01-05", "2026-01-02", "2026-01-05", "2026-01-09")
    df = fetch.fetch_all(date(2026, 1, 1), date(2026, 1, 10))
    assert len(df) == 12  # 3 days x 4 currencies
    assert list(df[df["currency"] == "EUR"]["date"].dt.day) == [2, 5, 9]


@patch("pln_rates.fetch.get_rates")
def test_fetch_all_raises_on_gap(get_rates):
    get_rates.return_value = rates_on("2026-01-02", "2026-02-20")
    with pytest.raises(RuntimeError, match="gap"):
        fetch.fetch_all(date(2026, 1, 1), date(2026, 2, 21))


@patch("pln_rates.fetch.get_rates")
def test_fetch_all_raises_on_bad_rate(get_rates):
    get_rates.return_value = rates_on("2026-01-02", "2026-01-09", mid=0)
    with pytest.raises(RuntimeError, match="non-positive"):
        fetch.fetch_all(date(2026, 1, 1), date(2026, 1, 10))