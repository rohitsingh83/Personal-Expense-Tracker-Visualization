"""
All the number-crunching: summaries, trends, budgets, unusual spending,
a simple forecast, and plain-English insights.

Every function takes the transactions DataFrame from ExpenseStore and
returns a DataFrame or dict, so the CLI, dashboard and reports all reuse it.
"""

import calendar
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

BUDGET_FILE = Path(__file__).resolve().parent.parent / "data" / "budgets.json"
# Paid once a month, so their spend is not extrapolated across the month.
FIXED_CATEGORIES = {"Rent", "Bills & Utilities", "Education", "Travel"}


def load_budgets(path: Path = BUDGET_FILE) -> dict[str, float]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_budgets(budgets: dict[str, float], path: Path = BUDGET_FILE) -> None:
    path.write_text(json.dumps(budgets, indent=2), encoding="utf-8")


def expenses(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["type"] == "expense"]


def month_slice(df: pd.DataFrame, month: str) -> pd.DataFrame:
    """month = 'YYYY-MM'"""
    return df[df["date"].dt.strftime("%Y-%m") == month]


def months_available(df: pd.DataFrame) -> list[str]:
    return sorted(df["date"].dt.strftime("%Y-%m").unique())


def summary(df: pd.DataFrame) -> dict:
    exp, inc = expenses(df), df[df["type"] == "income"]
    total_exp, total_inc = exp["amount"].sum(), inc["amount"].sum()
    days = max((df["date"].max() - df["date"].min()).days + 1, 1) if not df.empty else 1
    by_cat = exp.groupby("category")["amount"].sum()
    return {
        "income": float(total_inc),
        "expense": float(total_exp),
        "savings": float(total_inc - total_exp),
        "savings_rate": float((total_inc - total_exp) / total_inc * 100) if total_inc else 0.0,
        "transactions": int(len(exp)),
        "avg_daily_spend": float(total_exp / days),
        "biggest_expense": float(exp["amount"].max()) if not exp.empty else 0.0,
        "top_category": by_cat.idxmax() if not by_cat.empty else "-",
    }


def monthly_totals(df: pd.DataFrame) -> pd.DataFrame:
    m = df.assign(month=df["date"].dt.strftime("%Y-%m")).pivot_table(
        index="month", columns="type", values="amount", aggfunc="sum", fill_value=0)
    m = m.reindex(columns=["income", "expense"], fill_value=0)
    m["savings"] = m["income"] - m["expense"]
    m["savings_rate"] = np.where(m["income"] > 0, m["savings"] / m["income"] * 100, 0).round(1)
    return m.reset_index()


def category_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    c = expenses(df).groupby("category")["amount"].agg(total="sum", count="count", average="mean")
    c["share"] = (c["total"] / c["total"].sum() * 100).round(1)
    return c.sort_values("total", ascending=False).reset_index()


def category_by_month(df: pd.DataFrame) -> pd.DataFrame:
    e = expenses(df)
    return e.assign(month=e["date"].dt.strftime("%Y-%m")).pivot_table(
        index="month", columns="category", values="amount", aggfunc="sum", fill_value=0)


def month_over_month(df: pd.DataFrame, month: str) -> pd.DataFrame:
    table = category_by_month(df)
    months = list(table.index)
    if month not in months or months.index(month) == 0:
        return pd.DataFrame(columns=["category", "this_month", "last_month", "change", "change_pct"])
    prev = months[months.index(month) - 1]
    out = pd.DataFrame({"this_month": table.loc[month], "last_month": table.loc[prev]})
    out["change"] = out["this_month"] - out["last_month"]
    out["change_pct"] = np.where(out["last_month"] > 0, out["change"] / out["last_month"] * 100, np.nan).round(1)
    return out.sort_values("change", ascending=False).reset_index(names="category")


def month_progress(month: str, today: date | None = None) -> float:
    """Fraction of the month that has passed (1.0 for past months)."""
    today = today or date.today()
    y, m = map(int, month.split("-"))
    days = calendar.monthrange(y, m)[1]
    if (today.year, today.month) == (y, m):
        return today.day / days
    return 1.0 if (y, m) < (today.year, today.month) else 0.0


def budget_status(df: pd.DataFrame, month: str, budgets: dict[str, float], today: date | None = None) -> pd.DataFrame:
    spent = expenses(month_slice(df, month)).groupby("category")["amount"].sum()
    progress = month_progress(month, today) or 1.0
    rows = []
    for cat, limit in budgets.items():
        s = float(spent.get(cat, 0))
        projected = s / progress if progress < 1 and cat not in FIXED_CATEGORIES else s
        pct = s / limit * 100 if limit else 0
        if s > limit:
            status = "Over budget"
        elif projected > limit:
            status = "Will overspend"
        elif pct >= 80 and cat not in FIXED_CATEGORIES:
            status = "Warning"
        else:
            status = "On track"
        rows.append({"category": cat, "budget": limit, "spent": s, "remaining": limit - s,
                     "used_pct": round(pct, 1), "projected": round(projected), "status": status})
    return pd.DataFrame(rows).sort_values("used_pct", ascending=False)


def detect_anomalies(df: pd.DataFrame, threshold: float = 3.5, min_amount: float = 2500,
                     min_ratio: float = 3.0) -> pd.DataFrame:
    """
    Flag unusually large expenses using a robust z-score per category:
        z = 0.6745 * (amount - median) / MAD
    The median and MAD (median absolute deviation) are not pulled up by the
    outliers themselves, unlike mean and standard deviation. We also require
    the amount to be at least 3x the typical spend and above Rs 2,500, so
    small or fixed bills (e.g. an insurance premium) are not flagged.
    """
    cols = ["date", "description", "category", "amount", "typical", "times_typical", "z_score"]
    frames = []
    for _, g in expenses(df).groupby("category"):
        if len(g) < 4:
            continue
        g = g.copy()
        median = g["amount"].median()
        mad = (g["amount"] - median).abs().median()
        if mad == 0:  # most amounts identical (e.g. a fixed subscription): use 10% of the median
            mad = 0.1 * median or 1.0
        g["typical"] = median
        g["times_typical"] = (g["amount"] / median).round(1)
        g["z_score"] = (0.6745 * (g["amount"] - median) / mad).round(1)
        frames.append(g[(g["z_score"] > threshold) & (g["amount"] >= min_amount) & (g["times_typical"] >= min_ratio)])
    found = pd.concat(frames) if frames else pd.DataFrame(columns=cols)
    return found.sort_values("amount", ascending=False)[cols].reset_index(drop=True)


def forecast_next_month(df: pd.DataFrame, today: date | None = None) -> dict:
    """
    Forecast next month's spending: a linear trend over complete months,
    blended 50/50 with the 3-month average. One-off anomalies (like a new
    phone) are removed first so a single purchase doesn't distort the forecast.
    """
    anomalies = detect_anomalies(df)
    clean = df[~df.index.isin(df.reset_index().merge(
        anomalies[["date", "description", "amount"]], on=["date", "description", "amount"])["index"])]
    totals = monthly_totals(clean)
    complete = totals[[month_progress(m, today) >= 1 for m in totals["month"]]]
    if len(complete) < 3:
        return {"forecast": None, "trend_per_month": 0.0, "based_on": len(complete), "excluded": len(anomalies)}
    y = complete["expense"].to_numpy()
    x = np.arange(len(y))
    slope, intercept = np.polyfit(x, y, 1)
    trend = slope * len(y) + intercept
    forecast = 0.5 * trend + 0.5 * y[-3:].mean()
    return {"forecast": round(float(forecast)), "trend_per_month": round(float(slope)), "based_on": len(y),
            "excluded": len(anomalies)}


def weekday_pattern(df: pd.DataFrame) -> pd.DataFrame:
    e = expenses(df)
    order = list(calendar.day_name)
    days = e.assign(weekday=e["date"].dt.day_name()).groupby("weekday")["amount"].agg(total="sum", count="count")
    weeks = max(e["date"].dt.isocalendar().week.nunique(), 1)
    days["avg_per_week"] = (days["total"] / weeks).round()
    return days.reindex(order).fillna(0).reset_index()


def top_merchants(df: pd.DataFrame, n: int = 8) -> pd.DataFrame:
    e = expenses(df)
    return (e.groupby("description")["amount"].agg(total="sum", visits="count")
            .sort_values("total", ascending=False).head(n).reset_index())


def payment_split(df: pd.DataFrame) -> pd.DataFrame:
    return expenses(df).groupby("payment_method")["amount"].sum().sort_values(ascending=False).reset_index()


def insights(df: pd.DataFrame, month: str, budgets: dict[str, float], today: date | None = None) -> list[str]:
    """Plain-English observations, like a finance app would show."""
    out = []
    m = month_slice(df, month)
    s = summary(m)
    if s["income"]:
        tone = "great" if s["savings_rate"] >= 30 else "okay" if s["savings_rate"] >= 10 else "low"
        out.append(f"💰 You saved {s['savings_rate']:.0f}% of your income in {month_label(month)} ({tone}; "
                   f"a common target is 20-30%).")
    mom = month_over_month(df, month)
    progress = month_progress(month, today)
    if not mom.empty and progress >= 1:
        up = mom[(mom["change_pct"] > 25) & (mom["change"] > 1000)]
        for _, r in up.head(2).iterrows():
            out.append(f"📈 {r['category']} spending rose {r['change_pct']:.0f}% vs last month "
                       f"(₹{r['last_month']:,.0f} → ₹{r['this_month']:,.0f}).")
        down = mom[(mom["change_pct"] < -25) & (mom["change"] < -1000) & (mom["this_month"] > 0)]
        for _, r in down.head(1).iterrows():
            out.append(f"📉 Nice: {r['category']} spending fell {abs(r['change_pct']):.0f}% vs last month.")
    bs = budget_status(df, month, budgets, today)
    over = bs[bs["status"] == "Over budget"]
    if not over.empty:
        out.append("🚨 Over budget in " + ", ".join(f"{r.category} (+₹{-r.remaining:,.0f})" for r in over.itertuples()) + ".")
    soon = bs[bs["status"] == "Will overspend"]
    if not soon.empty:
        out.append("⚠️ At the current pace you will overspend on " + ", ".join(soon["category"]) + " this month.")
    anomalies = detect_anomalies(df)
    if not anomalies.empty:
        a = anomalies[anomalies["date"].dt.strftime("%Y-%m") == month]
        for r in a.head(2).itertuples():
            out.append(f"🔍 Unusual: {r.description} (₹{r.amount:,.0f}) is {r.times_typical}× your typical "
                       f"{r.category} spend.")
    week = weekday_pattern(m)
    if week["total"].sum():
        busiest = week.loc[week["total"].idxmax()]
        out.append(f"📅 You spend the most on {busiest['weekday']}s.")
    food = m[(m["type"] == "expense") & m["description"].str.contains("swiggy|zomato", case=False)]
    if len(food) >= 4:
        out.append(f"🍔 {len(food)} food-delivery orders this month (₹{food['amount'].sum():,.0f}). "
                   f"Cooking twice a week could save about ₹{food['amount'].mean() * 8:,.0f}/month.")
    return out


def month_label(month: str) -> str:
    y, m = map(int, month.split("-"))
    return f"{calendar.month_name[m]} {y}"
