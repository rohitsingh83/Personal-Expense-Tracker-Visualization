"""Static Matplotlib charts used in the PDF report and the README."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from . import analysis as an

PALETTE = ["#0F766E", "#14B8A6", "#F59E0B", "#EF4444", "#6366F1", "#EC4899", "#84CC16", "#06B6D4", "#A855F7",
           "#F97316", "#64748B"]
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 10})


def _save(fig, path: Path) -> Path:
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def category_donut(df: pd.DataFrame, path: Path, title: str = "Where the money went") -> Path:
    c = an.category_breakdown(df)
    fig, ax = plt.subplots(figsize=(7, 5))
    wedges, *_ = ax.pie(c["total"], colors=PALETTE[:len(c)], startangle=90, wedgeprops={"width": 0.38},
                        autopct=lambda p: f"{p:.0f}%" if p >= 5 else "", pctdistance=0.81)
    ax.text(0, 0, f"₹{c['total'].sum():,.0f}\ntotal", ha="center", va="center", fontsize=13, weight="bold")
    ax.legend(wedges, c["category"], loc="center left", bbox_to_anchor=(1, 0.5), frameon=False)
    ax.set_title(title, weight="bold", fontsize=13)
    return _save(fig, path)


def monthly_income_vs_expense(df: pd.DataFrame, path: Path) -> Path:
    m = an.monthly_totals(df)
    labels = [an.month_label(x)[:3] for x in m["month"]]
    x = range(len(m))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar([i - 0.2 for i in x], m["income"], width=0.4, color="#14B8A6", label="Income")
    ax.bar([i + 0.2 for i in x], m["expense"], width=0.4, color="#EF4444", label="Expenses")
    ax2 = ax.twinx()
    ax2.plot(list(x), m["savings_rate"], color="#1E293B", marker="o", label="Savings rate %")
    ax2.axhline(0, color="#94A3B8", lw=0.8)
    ax2.set_ylabel("Savings rate (%)")
    ax2.spines["top"].set_visible(False)
    ax.set_xticks(list(x), labels)
    ax.set_ylabel("₹")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v / 1000:.0f}k"))
    ax.set_title("Income vs expenses by month", weight="bold", fontsize=13)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, loc="upper center", bbox_to_anchor=(0.5, -0.08), frameon=False, ncol=3)
    return _save(fig, path)


def budget_bars(df: pd.DataFrame, month: str, budgets: dict, path: Path) -> Path:
    b = an.budget_status(df, month, budgets).sort_values("used_pct")
    colours = ["#EF4444" if s == "Over budget" else "#F59E0B" if s in ("Will overspend", "Warning") else "#14B8A6"
               for s in b["status"]]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(b["category"], b["used_pct"].clip(upper=200), color=colours)
    ax.axvline(100, color="#1E293B", ls="--", lw=1)
    for i, (pct, spent, limit) in enumerate(zip(b["used_pct"], b["spent"], b["budget"])):
        ax.text(min(pct, 200) + 2, i, f"₹{spent:,.0f} / ₹{limit:,.0f}", va="center", fontsize=8)
    ax.set_xlim(0, 240)
    ax.set_xlabel("% of budget used")
    ax.set_title(f"Budget vs actual: {an.month_label(month)}", weight="bold", fontsize=13)
    return _save(fig, path)


def category_trend(df: pd.DataFrame, path: Path, top: int = 5) -> Path:
    t = an.category_by_month(df)
    cols = t.sum().sort_values(ascending=False).index[:top]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for c, colour in zip(cols, PALETTE):
        ax.plot([an.month_label(m)[:3] for m in t.index], t[c], marker="o", label=c, color=colour, lw=2)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"₹{v / 1000:.0f}k"))
    ax.legend(frameon=False, ncol=3, fontsize=8)
    ax.set_title(f"Top {top} categories over time", weight="bold", fontsize=13)
    return _save(fig, path)


def weekday_chart(df: pd.DataFrame, path: Path) -> Path:
    w = an.weekday_pattern(df)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(w["weekday"].str[:3], w["avg_per_week"], color=["#0F766E" if d < 5 else "#F59E0B" for d in range(7)])
    ax.set_ylabel("Average ₹ per week")
    ax.set_title("Spending by day of week", weight="bold", fontsize=13)
    return _save(fig, path)


def all_charts(df: pd.DataFrame, month: str, budgets: dict, folder: Path) -> dict[str, Path]:
    folder.mkdir(parents=True, exist_ok=True)
    return {
        "donut": category_donut(an.month_slice(df, month), folder / "category_donut.png",
                                f"Where the money went: {an.month_label(month)}"),
        "monthly": monthly_income_vs_expense(df, folder / "income_vs_expense.png"),
        "budget": budget_bars(df, month, budgets, folder / "budget_vs_actual.png"),
        "trend": category_trend(df, folder / "category_trend.png"),
        "weekday": weekday_chart(df, folder / "weekday_spending.png"),
    }
