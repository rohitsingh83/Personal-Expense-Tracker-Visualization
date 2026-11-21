"""
Generate six months of realistic personal-finance data for a young professional
in Bengaluru (June to November 2026).

Real bank statements are private, so we simulate one: salary on the 1st, rent on
the 5th, frequent small food and travel spends, monthly bills, weekend shopping,
and two unusual large expenses so the anomaly detector has something to find.

Run:  python scripts/generate_sample_data.py
"""

import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent.parent / "data" / "expenses.csv"
random.seed(42)

START, END = date(2026, 6, 1), date(2026, 11, 21)

# category: [(description, min, max, payment methods)], average times per month, weekend bias
SPEND = {
    "Food & Dining": ([("Swiggy order", 180, 650, ["UPI"]), ("Zomato order", 200, 700, ["UPI", "Credit Card"]),
                       ("Starbucks coffee", 250, 450, ["Credit Card"]), ("Office canteen", 80, 160, ["UPI"]),
                       ("Dinner at Truffles", 900, 2200, ["Credit Card"])], 11, 1.6),
    "Groceries": ([("BigBasket groceries", 600, 2200, ["UPI", "Debit Card"]), ("Zepto quick delivery", 150, 700, ["UPI"]),
                   ("DMart shopping", 1200, 3200, ["Debit Card"])], 4, 1.3),
    "Transport": ([("Uber ride", 140, 520, ["UPI"]), ("Ola auto", 70, 220, ["UPI", "Cash"]),
                   ("Namma Metro recharge", 500, 500, ["UPI"]), ("HP petrol pump", 700, 1600, ["Credit Card"])], 9, 1.0),
    "Shopping": ([("Amazon order", 350, 3500, ["Credit Card"]), ("Myntra fashion", 800, 3000, ["Credit Card"]),
                  ("Decathlon sports", 600, 2500, ["Debit Card"])], 2, 1.8),
    "Entertainment": ([("BookMyShow movie", 300, 900, ["UPI"]), ("Spotify Premium", 119, 119, ["Credit Card"]),
                       ("PVR snacks", 250, 600, ["UPI"])], 3, 2.0),
    "Health": ([("Apollo Pharmacy", 150, 900, ["UPI"]), ("Cult.fit session", 499, 499, ["UPI"])], 2, 1.0),
    "Education": ([("Udemy course", 449, 799, ["Credit Card"]), ("Kindle book", 199, 499, ["Credit Card"])], 1, 1.0),
}

FIXED = [  # (day of month, description, category, amount, payment method)
    (5, "House rent - Koramangala PG", "Rent", 14000, "Net Banking"),
    (7, "BESCOM electricity bill", "Bills & Utilities", None, "UPI"),
    (10, "Airtel postpaid + broadband", "Bills & Utilities", 1299, "Credit Card"),
    (12, "Netflix subscription", "Entertainment", 649, "Credit Card"),
    (15, "LIC premium", "Bills & Utilities", 2100, "Net Banking"),
]


def daterange():
    d = START
    while d <= END:
        yield d
        d += timedelta(days=1)


def main() -> None:
    rows = []
    for d in daterange():
        if d.day == 1:
            rows.append((d, "Salary - CloudNest Technologies", "Salary", 58000, "Net Banking", "income"))
        for day, desc, cat, amount, method in FIXED:
            if d.day == day:
                amt = amount if amount else random.randint(780, 1650)  # electricity varies with season
                rows.append((d, desc, cat, amt, method, "expense"))
        weekend = d.weekday() >= 5
        for cat, (items, per_month, weekend_bias) in SPEND.items():
            p = per_month / 30 * (weekend_bias if weekend else 1)
            if random.random() < p:
                desc, lo, hi, methods = random.choice(items)
                rows.append((d, desc, cat, round(random.uniform(lo, hi) / 10) * 10 if hi > lo else lo,
                             random.choice(methods), "expense"))

    # occasional extra income and travel
    rows += [
        (date(2026, 7, 18), "Freelance website project", "Freelance", 12000, "Net Banking", "income"),
        (date(2026, 10, 9), "Freelance data dashboard", "Freelance", 8500, "Net Banking", "income"),
        (date(2026, 8, 14), "IndiGo flight to Goa", "Travel", 6400, "Credit Card", "expense"),
        (date(2026, 8, 15), "Goa beach resort", "Travel", 7800, "Credit Card", "expense"),
        (date(2026, 10, 24), "Diwali gifts and sweets", "Shopping", 4200, "UPI", "expense"),
        # two unusual expenses for the anomaly detector
        (date(2026, 9, 21), "OnePlus phone - Amazon", "Shopping", 27999, "Credit Card", "expense"),
        (date(2026, 11, 3), "Manipal hospital bill", "Health", 9800, "Debit Card", "expense"),
    ]

    df = pd.DataFrame(rows, columns=["date", "description", "category", "amount", "payment_method", "type"])
    df = df.sort_values("date").reset_index(drop=True)
    OUT.parent.mkdir(exist_ok=True)
    df.to_csv(OUT, index=False)
    spend = df[df.type == "expense"]
    print(f"wrote {len(df)} transactions ({len(spend)} expenses, total Rs {spend.amount.sum():,.0f}) to {OUT.name}")


if __name__ == "__main__":
    main()
