"""Command line: python -m scraper [--category travel] [--max-pages 3] [--out output]"""
import argparse
from pathlib import Path

from .run import run


def main() -> None:
    p = argparse.ArgumentParser(description="Scrape books.toscrape.com into a validated Excel/CSV file.")
    p.add_argument("--category", help="only one category, e.g. 'travel' (default: whole catalogue)")
    p.add_argument("--max-pages", type=int, help="stop after this many listing pages (for a quick test)")
    p.add_argument("--workers", type=int, default=4, help="parallel downloads (default 4)")
    p.add_argument("--delay", type=float, default=0.2, help="minimum seconds between requests (default 0.2)")
    p.add_argument("--out", type=Path, default=Path("output"), help="output folder (default ./output)")
    p.add_argument("--fresh", action="store_true", help="ignore the checkpoint and fetch everything again")
    a = p.parse_args()
    run(a.out, category=a.category, max_pages=a.max_pages, workers=a.workers, delay=a.delay, fresh=a.fresh)


if __name__ == "__main__":
    main()
