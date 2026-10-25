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