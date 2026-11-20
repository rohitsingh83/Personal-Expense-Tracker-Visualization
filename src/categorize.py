"""Rule-based regex auto-categorization for bank & UPI transactions."""

import re

CATEGORY_RULES = [
    ("Income", r"stipend|salary|freelance|refund|cashback|dividend"),
    ("Groceries", r"dmart|bigbasket|reliance fresh|vegetables|grocery|supermarket"),
    ("Food & Dining", r"swiggy|zomato|cafe|coffee|restaurant|biryani|pizza"),
    ("Transport", r"metro|uber|ola|rapido|petrol|fuel|irctc"),
    ("Bills & Utilities", r"electricity|tsspdcl|airtel|jiofiber|internet|recharge|water bill"),
    ("Shopping", r"amazon|flipkart|myntra|ajio|shopping|mouse|kurta"),
    ("Entertainment", r"bookmyshow|netflix|spotify|movie|prime video"),
]


def categorize_transaction(description: str, amount: float) -> str:
    if amount > 0:
        return "Income"
    desc = description.lower()
    for category, pattern in CATEGORY_RULES:
        if re.search(pattern, desc):
            return category
    return "Uncategorized"
