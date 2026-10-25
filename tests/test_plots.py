import pandas as pd

from pln_rates.plots import plot_indexed, plot_levels


def test_plots_create_files(tmp_path):
    rows = []
    for code in ["EUR", "GBP", "JPY", "USD"]:
        for i in range(3):
            rows.append((f"2026-01-0{i + 1}", code, 1.0 + i))
    df = pd.DataFrame(rows, columns=["date", "currency", "rate"])
    df["date"] = pd.to_datetime(df["date"])

    plot_levels(df, tmp_path / "levels.png")
    plot_indexed(df, tmp_path / "indexed.png")

    assert (tmp_path / "levels.png").exists()
    assert (tmp_path / "indexed.png").exists()