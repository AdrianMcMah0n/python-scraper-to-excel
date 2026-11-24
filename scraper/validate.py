"""Checks every record before delivery, so problems are reported instead of silently shipped."""
from collections import Counter

REQUIRED = ("upc", "title", "category", "price_gbp", "url")


def problems(book: dict) -> list[str]:
    """Everything wrong with one record (an empty list means it is clean)."""
    found = [f"missing {field}" for field in REQUIRED if book.get(field) in (None, "")]
    if isinstance(book.get("price_gbp"), (int, float)) and book["price_gbp"] <= 0:
        found.append("price is not positive")
    if book.get("rating") not in (1, 2, 3, 4, 5):
        found.append("rating outside 1-5")
    if book.get("in_stock", 0) < 0:
        found.append("negative stock")
    return found


def duplicate_keys(books: list[dict], key: str = "upc") -> list[str]:
    """Keys that appear more than once (the same product captured twice)."""
    counts = Counter(b.get(key) for b in books)
    return sorted(k for k, n in counts.items() if k and n > 1)
