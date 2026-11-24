"""Turn the site's HTML into plain Python values. No network access here, so it is easy to test."""
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def money(text: str) -> float:
    """'£51.77' -> 51.77"""
    return float(re.sub(r"[^\d.]", "", text))


def parse_listing(html: str, page_url: str) -> tuple[list[str], str | None]:
    """Book links on one listing page, plus the next page's URL (None on the last page)."""
    soup = BeautifulSoup(html, "lxml")
    links = [urljoin(page_url, a["href"]) for a in soup.select("article.product_pod h3 a")]
    next_link = soup.select_one("li.next a")
    return links, (urljoin(page_url, next_link["href"]) if next_link else None)


def parse_result_count(html: str) -> int | None:
    """The site's own total, e.g. '1000 results - showing 1 to 20.' -> 1000. Used to prove nothing was missed."""
    strong = BeautifulSoup(html, "lxml").select_one("form.form-horizontal strong")
    return int(strong.get_text(strip=True)) if strong else None


def parse_categories(html: str, base_url: str) -> dict[str, str]:
    """Category name (lower case) -> category URL, from the home page sidebar."""
    soup = BeautifulSoup(html, "lxml")
    return {
        a.get_text(strip=True).lower(): urljoin(base_url, a["href"])
        for a in soup.select("div.side_categories ul li ul li a")
    }


def parse_book(html: str, url: str) -> dict:
    """All fields of one book page."""
    soup = BeautifulSoup(html, "lxml")
    main = soup.select_one("div.product_main")
    info = {
        row.th.get_text(strip=True): row.td.get_text(strip=True)
        for row in soup.select("table.table-striped tr")
    }
    rating_classes = main.select_one("p.star-rating")["class"]
    in_stock = re.search(r"\((\d+) available\)", info.get("Availability", ""))
    description_head = soup.select_one("#product_description")
    crumbs = [a.get_text(strip=True) for a in soup.select("ul.breadcrumb li a")]

    return {
        "upc": info.get("UPC", ""),
        "title": main.h1.get_text(strip=True),
        "category": crumbs[2] if len(crumbs) > 2 else "",
        "price_gbp": money(info["Price (incl. tax)"]),
        "price_excl_tax_gbp": money(info["Price (excl. tax)"]),
        "in_stock": int(in_stock.group(1)) if in_stock else 0,
        "rating": next((RATINGS[c] for c in rating_classes if c in RATINGS), None),
        "reviews": int(info.get("Number of reviews", "0") or 0),
        "description": description_head.find_next_sibling("p").get_text(strip=True) if description_head else "",
        "url": url,
    }
