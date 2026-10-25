import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import requests

BASE_URL = "https://api.nbp.pl/api/exchangerates/rates/a"
CURRENCIES = ["EUR", "USD", "GBP", "JPY"]
MAX_DAYS = 93   # NBP limit for one request
TIMEOUT = 10    #seconds
ATTEMPTS = 3    # error handling
WAIT = 2        #seconds between attempts


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
    #One request to NBP. Returns a list of rates, or [] if there is no data
    url = f"{BASE_URL}/{code}/{start}/{end}/"
    for attempt in range(1, ATTEMPTS + 1):
        try:
            response = requests.get(url, params={"format": "json"}, timeout=TIMEOUT)
        except (requests.Timeout, requests.ConnectionError) as error:
            if attempt == ATTEMPTS:
                raise RuntimeError(f"{code} {start}..{end}: gave up after {ATTEMPTS} attempts") from error
            time.sleep(WAIT)
            continue

        if response.status_code == 200:
            return response.json()["rates"]
        if response.status_code == 404:  # no data in this window
            return []
        if response.status_code >= 500 and attempt < ATTEMPTS:
            time.sleep(WAIT)
            continue
        raise RuntimeError(f"{code} {start}..{end}: HTTP {response.status_code}")


def fetch_all(start, end):
    #Download all currencies for start..end into one DataFrame
    rows = []
    for code in CURRENCIES:
        for window_start, window_end in make_windows(start, end):
            for item in get_rates(code, window_start, window_end):
                rows.append({"date": item["effectiveDate"], "currency": code, "rate": item["mid"]})

    df = pd.DataFrame(rows, columns=["date", "currency", "rate"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.drop_duplicates(["date", "currency"])
    df = df.sort_values(["currency", "date"]).reset_index(drop=True)

    for code in CURRENCIES:
        part = df[df["currency"] == code]
        if part.empty:
            raise RuntimeError(f"no data for {code}")
        print(f"{code}: {part['date'].min().date()} to {part['date'].max().date()}, {len(part)} rows")
    return df