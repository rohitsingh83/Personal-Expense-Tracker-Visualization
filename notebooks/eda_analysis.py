"""Exploratory Data Analysis script for Personal Expense Tracker."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
df = pd.read_csv(ROOT / "data" / "sample_expenses.csv")
print("Dataset shape:", df.shape)
print("Payment methods:\n", df["payment_method"].value_counts())
