# Python scraper to Excel / CSV

A complete, checked web-scraping job in plain Python. It reads every page of an online catalogue, captures each product's details, checks every record and delivers an Excel workbook, a CSV and a run report that shows nothing was missed.

Demo target: [books.toscrape.com](https://books.toscrape.com), a public sandbox site built for scraping practice.

## The problem

Anyone who needs data from a website wants three things:

1. **Every record**, not just the first page.
2. **Clean values** they can sort and filter straight away (numbers as numbers, not "£51.77" as text).
3. **Proof that nothing was missed.** A quick script silently skips whatever fails, and nobody finds out until the numbers look wrong.

## What it does

1. Walks every listing page (follows "next" to the end) and records the site's own total ("1000 results").
2. Opens every product page in parallel, with a shared polite delay and automatic retries.
3. Captures 10 fields per book: UPC, title, category, price incl. and excl. tax, units in stock, star rating, number of reviews, description and URL.
4. Saves each record to a checkpoint as it arrives, so an interrupted run carries on where it stopped.
5. Checks every record: required fields present, price above zero, rating 1 to 5, no duplicate products.
6. Delivers `books.xlsx` (Books, By category, Run report), `books.csv` and `run_report.txt`.

## Result of a full run

| Check | Result |
|---|---|
| Listing pages read | 50 |
| Books the site says it has | 1,000 |
| Books captured | 1,000 (complete) |
| Failed pages | 0 |
| Records with problems | 0 |
| Duplicate products | 0 |
| HTTP requests | 1,050 |
| Run time | about 4 minutes |
| Re-run after completion | 0 books fetched again, 50 requests |

The workbook's "By category" tab summarises 50 categories (count, average / min / max price, average rating, units in stock). Sample files are in [`sample_output/`](sample_output/).

## Run it

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows (macOS / Linux: source .venv/bin/activate)
pip install -r requirements.txt

python -m scraper                      # whole catalogue, about 4 minutes
python -m scraper --category travel    # one category
python -m scraper --max-pages 2        # quick test run
python -m scraper --fresh              # ignore the checkpoint and fetch everything again
pytest                                 # offline tests
```

Output goes to `./output` (change it with `--out`).

## How it is built

| File | Job |
|---|---|
| `scraper/fetch.py` | One shared HTTP session: retries with back-off, a delay shared by all threads, a clear User-Agent |
| `scraper/parse.py` | HTML to Python values. No network code, so it is tested offline against saved pages |
| `scraper/validate.py` | The checks run on every record before delivery |
| `scraper/run.py` | The job itself: collect links, fetch in parallel, checkpoint, validate, report |
| `scraper/export.py` | Excel (formatted, with summary and run report) and CSV |
| `tests/` | Parser, validation and checkpoint tests on saved copies of real pages |

## Design choices

- **Completeness is measured, not assumed.** The run compares what it captured with the site's own total and says "Complete: yes" or how many are missing. Every failed page is listed by URL.
- **Polite by default.** At most one request every 0.2 seconds across all threads, retries that back off (1, 2, 4 seconds) on errors such as 429 and 503, and a User-Agent that says who is calling.
- **Resumable.** Records go to a checkpoint file as they arrive. A re-run fetches only what is missing.
- **A real bug this caught.** Some book descriptions contain the Unicode line separator (U+2028). Reading the checkpoint with `str.splitlines()` split those records in half and the resume crashed. The loader now reads the file line by line and safely skips a half-written last line; `tests/test_checkpoint.py` covers both cases.
- **Built for the person receiving it.** Frozen header row, prices formatted as money, a summary tab, and a CSV saved so Excel and Google Sheets show the pound sign correctly.

## Adapting it to another site

Only `parse.py` (the selectors) and the start URL change. Fetching, checkpointing, validation, export and the run report stay the same.

## A note on responsible scraping

books.toscrape.com exists for practice. On a real site: read its terms and robots.txt, collect only public data, keep a delay between requests, and stop if the site asks you to.

## License

MIT
