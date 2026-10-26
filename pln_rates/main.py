import argparse
from datetime import date, datetime, timedelta
from pathlib import Path

from pln_rates.analysis import answers
from pln_rates.fetch import default_end_date, fetch_all
from pln_rates.plots import plot_indexed, plot_levels

YEARS = 5


def main():
    parser = argparse.ArgumentParser(description="Download NBP rates for EUR, USD, GBP, JPY and analyse them")
    parser.add_argument("--end-date", type=date.fromisoformat,
                        help="last day to include, YYYY-MM-DD (default: latest published day)")
    args = parser.parse_args()

    end = args.end_date or default_end_date(datetime.now().astimezone())
    start = end - timedelta(days=365 * YEARS)
    print(f"period: {start} to {end}")

    df = fetch_all(start, end)

    Path("data").mkdir(exist_ok=True)
    Path("outputs").mkdir(exist_ok=True)
    df.to_csv("data/rates.csv", index=False)

    result = answers(df)
    result.to_csv("outputs/answers.csv", index=False)
    print(result.to_string())

    plot_levels(df, "outputs/levels.png")
    plot_indexed(df, "outputs/indexed.png")


if __name__ == "__main__":
    main()