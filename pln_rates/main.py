import argparse
import logging
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from pln_rates.analysis import answers
from pln_rates.fetch import default_end_date, fetch_all
from pln_rates.plots import plot_indexed, plot_levels

ROOT = Path(__file__).resolve().parent.parent  # data/ and outputs/ go here, wherever the script is started from

log = logging.getLogger(__name__)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Download NBP rates for EUR, USD, GBP, JPY and analyse them")
    parser.add_argument("--end-date", type=date.fromisoformat,
                        help="last day to include, YYYY-MM-DD (default: latest published day)")
    parser.add_argument("--years", type=int, default=5, help="how many years back (default 5)")
    args = parser.parse_args()

    end = args.end_date or default_end_date(datetime.now().astimezone())
    start = (pd.Timestamp(end) - pd.DateOffset(years=args.years)).date()
    log.info("period: %s to %s", start, end)

    df = fetch_all(start, end)

    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "outputs").mkdir(exist_ok=True)
    df.to_csv(ROOT / "data" / "rates.csv", index=False)

    result = answers(df)
    result.to_csv(ROOT / "outputs" / "answers.csv", index=False)
    print(result.to_string())

    plot_levels(df, ROOT / "outputs" / "levels.png", result)
    plot_indexed(df, ROOT / "outputs" / "indexed.png")


if __name__ == "__main__":
    main()