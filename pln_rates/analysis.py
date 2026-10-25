import pandas as pd


def add_changes(df):
    df = df.sort_values(["currency", "date"]).copy()
    # groupby so one currency's first day is not compared with another currency's last day
    df["change_pln"] = df.groupby("currency")["rate"].diff()
    df["change_pct"] = df.groupby("currency")["rate"].pct_change() * 100
    return df


def answers(df):
    df = add_changes(df)
    rows = []
    for code, part in df.groupby("currency"):
        part = part.reset_index(drop=True)
        low = part.loc[part["rate"].idxmin()]    # idxmin/idxmax return the first match, so ties give the earliest date
        high = part.loc[part["rate"].idxmax()]
        fall = part.loc[part["change_pct"].idxmin()]
        rise = part.loc[part["change_pct"].idxmax()]

        rows.append({"question": "lowest", "currency": code, "date": low["date"].date(), "rate": low["rate"]})
        rows.append({"question": "highest", "currency": code, "date": high["date"].date(), "rate": high["rate"]})
        for name, row in [("biggest one-day fall", fall), ("biggest one-day rise", rise)]:
            rows.append({"question": name, "currency": code, "date": row["date"].date(), "rate": row["rate"],
                         "change_pln": row["change_pln"], "change_pct": row["change_pct"]})
    return pd.DataFrame(rows)