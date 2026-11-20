"""Centralized configuration for Personal Expense Tracker."""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Settings:
    root_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_dir: Path = field(init=False)
    db_dir: Path = field(init=False)
    outputs_dir: Path = field(init=False)
    images_dir: Path = field(init=False)
    reports_dir: Path = field(init=False)
    
    db_path: Path = field(init=False)
    sample_csv_path: Path = field(init=False)
    excel_report_path: Path = field(init=False)
    budget_alerts_path: Path = field(init=False)

    def __post_init__(self):
        root = self.root_dir
        object.__setattr__(self, "data_dir", root / "data")
        object.__setattr__(self, "db_dir", root / "db")
        object.__setattr__(self, "outputs_dir", root / "outputs")
        object.__setattr__(self, "images_dir", root / "images")
        object.__setattr__(self, "reports_dir", root / "reports")
        
        object.__setattr__(self, "db_path", root / "db" / "expenses.db")
        object.__setattr__(self, "sample_csv_path", root / "data" / "sample_expenses.csv")
        object.__setattr__(self, "excel_report_path", root / "outputs" / "expense_report.xlsx")
        object.__setattr__(self, "budget_alerts_path", root / "reports" / "budget_alerts.csv")
        
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.db_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
