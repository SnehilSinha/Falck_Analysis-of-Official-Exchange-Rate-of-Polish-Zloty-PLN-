import matplotlib

matplotlib.use("Agg")  # only saves files, so no window (and no Tk) is needed
import matplotlib.pyplot as plt
import pandas as pd


def mark_extremes(ax, answers, code):
    # a dot and a label on the lowest and highest rate, the points the brief asks about
    for question, colour, offset in [("lowest", "tab:red", -16), ("highest", "tab:green", 8)]:
        row = answers[(answers["currency"] == code) & (answers["question"] == question)].iloc[0]
        when = pd.Timestamp(row["date"])
        ax.margins(y=0.15)  # room so the labels do not hit the title or axis
        ax.scatter([when], [row["rate"]], color=colour, zorder=3)
        ax.annotate(f"{row['rate']} ({when:%d %b %Y})", (when, row["rate"]), xytext=(0, offset),
                    textcoords="offset points", ha="left" if when < pd.Timestamp("2024-06-01") else "right", fontsize=8, color=colour)


def plot_levels(df, path, answers=None):
    codes = sorted(df["currency"].unique())
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    for ax, code in zip(axes.flat, codes):
        part = df[df["currency"] == code]
        ax.plot(part["date"], part["rate"])
        if answers is not None:
            mark_extremes(ax, answers, code)
        ax.set_title(f"{code}/PLN")
        ax.set_ylabel(f"PLN per 1 {code}")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def plot_indexed(df, path):
    fig, ax = plt.subplots(figsize=(10, 5))
    for code, part in df.groupby("currency"):
        ax.plot(part["date"], part["rate"] / part["rate"].iloc[0] * 100, label=code)
    ax.axhline(100, color="grey", linewidth=0.5)
    ax.set_title("Rates indexed to 100 at the start of the period")
    ax.set_ylabel("index (start = 100)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)