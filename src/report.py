"""Export formatted Excel workbook and Markdown summary report."""

from pathlib import Path
import pandas as pd


def export_excel_report(df: pd.DataFrame, budget_df: pd.DataFrame, xlsx_path: Path) -> None:
    exp = df[df["amount"] < 0].copy()
    exp["spend"] = exp["amount"].abs()
    cat_summary = exp.groupby("category")["spend"].agg(["count", "sum", "mean"]).reset_index()

    with pd.ExcelWriter(xlsx_path, engine="xlsxwriter") as writer:
        df_out = df.copy()
        df_out["tx_date"] = df_out["tx_date"].dt.strftime("%Y-%m-%d")
        df_out.to_excel(writer, sheet_name="Transactions", index=False)
        cat_summary.to_excel(writer, sheet_name="Category Summary", index=False)
        budget_df.to_excel(writer, sheet_name="Budget Check", index=False)
