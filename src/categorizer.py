"""
Automatic categorisation.

Bank statements only say things like "UPI-SWIGGY-BLR" or "POS AMAZON". This
module guesses the category from keywords so the user doesn't have to label
every transaction by hand. A user's own choice always wins.
"""

import re

CATEGORIES = ["Food & Dining", "Groceries", "Transport", "Shopping", "Rent", "Bills & Utilities",
              "Entertainment", "Health", "Education", "Travel", "Others"]
INCOME_CATEGORIES = ["Salary", "Freelance", "Interest", "Refund", "Other Income"]

RULES = {
    "Food & Dining": ["swiggy", "zomato", "restaurant", "cafe", "coffee", "starbucks", "canteen", "dinner",
                      "lunch", "pizza", "domino", "kfc", "mcdonald", "truffles", "chai"],
    "Groceries": ["bigbasket", "blinkit", "zepto", "dmart", "grocery", "groceries", "supermarket", "more retail",
                  "jiomart", "vegetables"],
    "Transport": ["uber", "ola", "rapido", "metro", "petrol", "fuel", "diesel", "parking", "fastag", "auto"],
    "Shopping": ["amazon", "flipkart", "myntra", "ajio", "decathlon", "nykaa", "mall", "gift", "phone"],
    "Rent": ["rent", "pg ", "landlord", "maintenance"],
    "Bills & Utilities": ["electricity", "bescom", "airtel", "jio", "broadband", "recharge", "postpaid", "water bill",
                          "gas", "lic", "insurance", "premium"],
    "Entertainment": ["netflix", "spotify", "prime video", "hotstar", "bookmyshow", "movie", "pvr", "inox", "concert"],
    "Health": ["pharmacy", "apollo", "medplus", "hospital", "clinic", "doctor", "cult.fit", "gym", "lab test"],
    "Education": ["udemy", "coursera", "course", "book", "kindle", "tuition", "exam fee"],
    "Travel": ["flight", "indigo", "air india", "irctc", "train", "hotel", "resort", "makemytrip", "goibibo", "bus"],
}
INCOME_RULES = {"Salary": ["salary", "payroll"], "Freelance": ["freelance", "client payment"],
                "Interest": ["interest"], "Refund": ["refund", "cashback"]}


def _match(text: str, rules: dict[str, list[str]]) -> str | None:
    low = f" {text.lower()} "
    for category, words in rules.items():
        if any(re.search(r"(?<![a-z])" + re.escape(w.strip()) + r"(?![a-z])", low) for w in words):
            return category
    return None


def categorize(description: str, txn_type: str = "expense") -> str:
    if txn_type == "income":
        return _match(description, INCOME_RULES) or "Other Income"
    return _match(description, RULES) or "Others"
