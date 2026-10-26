import logging
import time
from datetime import timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import requests

URL = "https://api.nbp.pl/api/exchangerates/rates/a"
CURRENCIES = ["EUR", "USD", "GBP", "JPY"]
MAX_DAYS = 93
TRIES = 3
MAX_GAP = 7  # days: weekend + holidays never make a longer break

log = logging.getLogger(__name__)


def make_windows(start, end):
    #Split start and end into windows of at most MAX_DAYS days, no overlap
    windows = []
    current = start
    while current <= end:
        window_end = min(current + timedelta(days=MAX_DAYS - 1), end)
        windows.append((current, window_end))
        current = window_end + timedelta(days=1)
    return windows


def default_end_date(now):
    #Table A is published 11:45-12:15 Warsaw time, so before 12:15 use yesterday
    warsaw = now.astimezone(ZoneInfo("Europe/Warsaw"))
    if (warsaw.hour, warsaw.minute) < (12, 15):
        return warsaw.date() - timedelta(days=1)
    return warsaw.date()


def get_rates(code, start, end):
    url = f"{URL}/{code}/{start}/{end}/?format=json"
    for i in range(TRIES):
        try:
            r = requests.get(url, timeout=10)
        except (requests.Timeout, requests.ConnectionError):
            r = None
        if r is not None:
            if r.status_code == 200:
                try:
                    return r.json()["rates"]
                except (ValueError, KeyError):
                    raise RuntimeError(f"{code} {start} to {end}: unexpected response from NBP")
            if r.status_code == 404:  # no data in this window
                return []
            if r.status_code < 500 and r.status_code != 429:  # 400 etc: our request is wrong, retrying won't help
                raise RuntimeError(f"{code} {start} to {end}: HTTP {r.status_code}")
        # timeout, 5xx or 429 (too many requests): wait longer each time, then try again
        log.warning("%s %s to %s: try %d of %d failed", code, start, end, i + 1, TRIES)
        time.sleep(2 ** i)
    raise RuntimeError(f"{code} {start} to {end}: failed after {TRIES} tries")

def fetch_all(start, end):
    rows = []
    for code in CURRENCIES:
        for s, e in make_windows(start, end):
            for item in get_rates(code, s, e):
                rows.append((item["effectiveDate"], code, item["mid"]))

    df = pd.DataFrame(rows, columns=["date", "currency", "rate"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.drop_duplicates(["date", "currency"]).sort_values(["currency", "date"])

    if df["rate"].isna().any() or (df["rate"] <= 0).any():
        raise RuntimeError("found missing or non-positive rates")

    for code in CURRENCIES:
        dates = df[df["currency"] == code]["date"]
        if dates.empty:
            raise RuntimeError(f"no data for {code}")
        # a 404 is skipped in get_rates, so check here that no window went missing
        if dates.diff().max() > pd.Timedelta(days=MAX_GAP):
            raise RuntimeError(f"{code}: gap of more than {MAX_GAP} days, a window may be missing")
        if (dates.min() - pd.Timestamp(start)).days > MAX_GAP or (pd.Timestamp(end) - dates.max()).days > MAX_GAP:
            raise RuntimeError(f"{code}: data does not cover {start} to {end}")
        log.info("%s: %s to %s, %d rows", code, dates.min().date(), dates.max().date(), len(dates))
    return df