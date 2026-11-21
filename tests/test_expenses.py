"""Run with:  python -m pytest -q"""

from datetime import date

import pandas as pd
import pytest

from src import analysis as an
from src.categorizer import categorize
from src.report import excel_report, pdf_report
from src.storage import SAMPLE_CSV, ExpenseStore

TODAY = date(2026, 11, 21)


@pytest.fixture
def store(tmp_path):
    s = ExpenseStore(tmp_path / "test.db")
    yield s
    s.close()


@pytest.fixture
def df(store):
    return store.to_dataframe()


def test_sample_data_is_seeded_automatically(store):
    assert store.count() == len(pd.read_csv(SAMPLE_CSV))


def test_import_skips_duplicates(store):
    added, skipped = store.import_csv(SAMPLE_CSV)
    assert added == 0 and skipped == store.count()


@pytest.mark.parametrize("text,expected", [
    ("UPI-SWIGGY-BLR-1234", "Food & Dining"), ("POS AMAZON IN", "Shopping"), ("IRCTC train ticket", "Travel"),
    ("BESCOM bill", "Bills & Utilities"), ("Uber trip", "Transport"), ("Something random", "Others"),
    ("Autograph book", "Education"),  # "auto" must not match inside "autograph"
])
def test_categorizer(text, expected):
    assert categorize(text) == expected


def test_income_categorizer():
    assert categorize("Salary credit November", "income") == "Salary"


def test_add_update_delete_and_validation(store):
    txn = store.add("2026-11-20", "Zomato lunch", 300)
    row = store.to_dataframe().set_index("id").loc[txn]
    assert row["category"] == "Food & Dining" and row["type"] == "expense"
    store.update(txn, amount=350, category="Others")
    assert store.to_dataframe().set_index("id").loc[txn, "amount"] == 350
    store.delete(txn)
    assert txn not in store.to_dataframe()["id"].values
    with pytest.raises(ValueError):
        store.add("2026-11-20", "Bad", -5)


def test_summary_and_monthly_totals_agree(df):
    s = an.summary(df)
    m = an.monthly_totals(df)
    assert s["expense"] == pytest.approx(m["expense"].sum())
    assert s["savings"] == pytest.approx(s["income"] - s["expense"])
    assert list(m["month"]) == ["2026-06", "2026-07", "2026-08", "2026-09", "2026-10", "2026-11"]


def test_category_shares_add_up_to_100(df):
    assert an.category_breakdown(df)["share"].sum() == pytest.approx(100, abs=0.5)


def test_anomalies_find_exactly_the_planted_outliers(df):
    found = set(an.detect_anomalies(df)["description"])
    assert found == {"OnePlus phone - Amazon", "Manipal hospital bill"}


def test_budget_projection_ignores_fixed_costs(df):
    b = an.budget_status(df, "2026-11", {"Rent": 14000, "Food & Dining": 7000}, TODAY).set_index("category")
    assert b.loc["Rent", "status"] == "On track"            # rent is paid once, not extrapolated
    assert b.loc["Food & Dining", "status"] == "Will overspend"


def test_forecast_excludes_one_off_purchases(df):
    f = an.forecast_next_month(df, TODAY)
    assert f["excluded"] == 2 and 35000 < f["forecast"] < 70000


def test_insights_are_generated(df):
    lines = an.insights(df, "2026-09", an.load_budgets(), TODAY)
    assert any("OnePlus" in l for l in lines)
    assert any("Over budget" in l for l in lines)


def test_reports_are_valid_files(df):
    assert excel_report(df, an.load_budgets(), "2026-10", TODAY)[:2] == b"PK"   # xlsx is a zip file
    assert pdf_report(df, an.load_budgets(), "2026-10", TODAY)[:4] == b"%PDF"
