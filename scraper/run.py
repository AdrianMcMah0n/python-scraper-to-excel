"""The whole job: walk the listing pages, fetch every book (resumable), validate, export, report."""
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from .export import write_outputs
from .fetch import PoliteSession
from .parse import parse_book, parse_categories, parse_listing, parse_result_count
from .validate import duplicate_keys, problems

BASE_URL = "https://books.toscrape.com/"
ALL_BOOKS_URL = BASE_URL + "catalogue/page-1.html"


def load_checkpoint(path: Path) -> dict[str, dict]:
    """Books already captured in an earlier (possibly interrupted) run, by URL."""
    if not path.exists():
        return {}
    done = {}
    # iterate the file, not str.splitlines(): splitlines() also breaks on characters such as
    # U+2028 that appear inside some book descriptions, which would cut a record in half
    with path.open(encoding="utf-8") as f:
        for line in f:
            try:
                book = json.loads(line)
            except json.JSONDecodeError:
                continue  # e.g. the last line of a run that was killed mid-write: it is fetched again
            done[book["url"]] = book
    return done


def collect_links(session: PoliteSession, start_url: str, max_pages: int | None) -> tuple[list[str], int | None, int]:
    links, expected, pages, url = [], None, 0, start_url
    while url and (max_pages is None or pages < max_pages):
        html = session.get(url)
        if expected is None:
            expected = parse_result_count(html)
        found, url = parse_listing(html, url)
        links.extend(found)
        pages += 1
    return list(dict.fromkeys(links)), expected, pages  # de-duplicate, keep order


def run(out_dir: Path, category: str | None = None, max_pages: int | None = None,
        workers: int = 4, delay: float = 0.2, fresh: bool = False) -> dict:
    started, t0 = datetime.now(), time.monotonic()
    session = PoliteSession(delay=delay)
    out_dir.mkdir(parents=True, exist_ok=True)

    start_url = ALL_BOOKS_URL
    if category:
        categories = parse_categories(session.get(BASE_URL), BASE_URL)
        if category.lower() not in categories:
            raise SystemExit(f"Unknown category '{category}'. Options: {', '.join(sorted(categories))}")
        start_url = categories[category.lower()]

    links, expected, pages = collect_links(session, start_url, max_pages)

    checkpoint = out_dir / "checkpoint.jsonl"
    if fresh and checkpoint.exists():
        checkpoint.unlink()
    done = load_checkpoint(checkpoint)
    todo = [u for u in links if u not in done]
    print(f"{len(links)} book links on {pages} pages; {len(done)} already captured, {len(todo)} to fetch")

    failures = []
    with ThreadPoolExecutor(max_workers=workers) as pool, checkpoint.open("a", encoding="utf-8") as cp:
        futures = {pool.submit(lambda u: parse_book(session.get(u), u), u): u for u in todo}
        for i, future in enumerate(as_completed(futures), 1):
            url = futures[future]
            try:
                book = future.result()
            except Exception as exc:  # keep going; every failure is listed in the report
                failures.append(f"{url} ({exc})")
                continue
            done[url] = book
            cp.write(json.dumps(book, ensure_ascii=False) + "\n")
            if i % 100 == 0:
                print(f"  {i}/{len(todo)} fetched")

    books = [done[u] for u in links if u in done]
    issues = {b["url"]: p for b in books if (p := problems(b))}
    dupes = duplicate_keys(books)
    complete = expected is None or len(books) == expected or max_pages is not None

    report = [
        ("Started", started.strftime("%d-%b-%Y %H:%M:%S")),
        ("Scope", f"category '{category}'" if category else "whole catalogue"),
        ("Listing pages read", pages),
        ("Books the site says it has", expected if expected is not None else "not shown"),
        ("Book links found", len(links)),
        ("Books captured", len(books)),
        ("Complete", "yes" if complete else f"NO: {expected - len(books)} missing"),
        ("Failed pages", len(failures)),
        ("Records with problems", len(issues)),
        ("Duplicate UPCs", len(dupes)),
        ("HTTP requests made", session.requests_made),
        ("Run time (s)", round(time.monotonic() - t0, 1)),
    ]
    report += [("Failed: " + str(i + 1), f) for i, f in enumerate(failures)]
    report += [("Problem: " + url, "; ".join(p)) for url, p in issues.items()]
    report += [("Duplicate UPC", d) for d in dupes]

    paths = write_outputs(books, report, out_dir)
    for k, v in report[:12]:
        print(f"{k}: {v}")
    print(f"Saved {paths['xlsx']} and {paths['csv']}")
    return {"books": books, "report": report, "paths": paths}
