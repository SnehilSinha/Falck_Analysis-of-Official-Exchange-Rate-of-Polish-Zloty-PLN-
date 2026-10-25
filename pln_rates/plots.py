import matplotlib.pyplot as plt


def plot_levels(df, path):
    codes = sorted(df["currency"].unique())
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    for ax, code in zip(axes.flat, codes):
        part = df[df["currency"] == code]
        ax.plot(part["date"], part["rate"])
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