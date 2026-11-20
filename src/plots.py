"""Generate 4 publication-grade Matplotlib/Seaborn financial charts."""

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def generate_all_charts(df: pd.DataFrame, images_dir: Path) -> None:
    exp = df[df["amount"] < 0].copy()
    exp["spend"] = exp["amount"].abs()

    # 1. Category-wise Bar Chart
    cat_sum = exp.groupby("category")["spend"].sum().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    cat_sum.plot(kind="barh", color="#1565C0", ax=ax)
    ax.set_title("Spending by Category (INR)", fontweight="bold")
    ax.set_xlabel("Amount (INR)")
    plt.tight_layout()
    plt.savefig(images_dir / "category_spending_bar.png", dpi=150)
    plt.close(fig)

    # 2. Category Donut Chart
    fig, ax = plt.subplots(figsize=(6.5, 6.5))
    wedges, texts, autotexts = ax.pie(
        cat_sum.values, labels=cat_sum.index, autopct="%1.1f%%", pctdistance=0.8,
        wedgeprops=dict(width=0.45, edgecolor="w")
    )
    ax.set_title("Expense Distribution by Category", fontweight="bold")
    plt.tight_layout()
    plt.savefig(images_dir / "category_donut.png", dpi=150)
    plt.close(fig)

    # 3. Monthly Spending Trend Line Chart
    monthly = exp.groupby("month")["spend"].sum()
    fig, ax = plt.subplots(figsize=(7, 4))
    monthly.plot(kind="line", marker="o", color="#2E7D32", linewidth=2.2, ax=ax)
    ax.set_title("Monthly Spending Trend (INR)", fontweight="bold")
    ax.set_ylabel("Total Spend (INR)")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(images_dir / "monthly_trend_line.png", dpi=150)
    plt.close(fig)

    # 4. Payment Method Pie Chart
    pm_sum = exp.groupby("payment_method")["spend"].sum()
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(pm_sum.values, labels=pm_sum.index, autopct="%1.1f%%", startangle=140)
    ax.set_title("Spending Share by Payment Method", fontweight="bold")
    plt.tight_layout()
    plt.savefig(images_dir / "payment_method_pie.png", dpi=150)
    plt.close(fig)
