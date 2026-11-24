"""Offline tests: saved copies of real pages, so they run without the network."""
from pathlib import Path

from scraper.parse import money, parse_book, parse_listing, parse_result_count
from scraper.validate import duplicate_keys, problems

FIX = Path(__file__).parent / "fixtures"
LIST_URL = "https://books.toscrape.com/catalogue/page-1.html"
BOOK_URL = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"


def read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def test_money():
    assert money("£51.77") == 51.77


def test_listing_page():
    links, next_url = parse_listing(read("catalogue_page_1.html"), LIST_URL)
    assert len(links) == 20
    assert links[0] == BOOK_URL
    assert next_url == "https://books.toscrape.com/catalogue/page-2.html"


def test_result_count():
    assert parse_result_count(read("catalogue_page_1.html")) == 1000


def test_book_page():
    book = parse_book(read("book_a_light_in_the_attic.html"), BOOK_URL)
    assert book["title"] == "A Light in the Attic"
    assert book["upc"] == "a897fe39b1053632"
    assert book["category"] == "Poetry"
    assert book["price_gbp"] == 51.77
    assert book["in_stock"] == 22
    assert book["rating"] == 3
    assert book["description"].startswith("It's hard to imagine a world without A Light in the Attic.")
    assert problems(book) == []


def test_validation_catches_bad_records():
    bad = {"upc": "", "title": "X", "category": "Y", "price_gbp": 0, "url": "u", "rating": 7, "in_stock": -1}
    assert problems(bad) == ["missing upc", "price is not positive", "rating outside 1-5", "negative stock"]


def test_duplicates():
    assert duplicate_keys([{"upc": "a"}, {"upc": "b"}, {"upc": "a"}]) == ["a"]
