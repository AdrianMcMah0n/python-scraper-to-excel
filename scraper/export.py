"""Write the deliverables: an Excel workbook (data, summary, run report) and a CSV that opens in Google Sheets."""
from pathlib import Path

import pandas as pd
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

COLUMNS = ["upc", "title", "category", "price_gbp", "price_excl_tax_gbp", "in_stock",
           "rating", "reviews", "description", "url"]
WIDTHS = {"title": 45, "category": 18, "description": 60, "url": 55}


def _tidy(sheet, money_cols=()):
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    sheet.freeze_panes = "A2"
    for i, cell in enumerate(sheet[1], 1):
        letter = get_column_letter(i)
        sheet.column_dimensions[letter].width = WIDTHS.get(cell.value, max(12, len(str(cell.value)) + 2))
        if cell.value in money_cols:
            for c in sheet[letter][1:]:
                c.number_format = "£#,##0.00"


def write_outputs(books: list[dict], report: list[tuple[str, object]], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(books, columns=COLUMNS).sort_values(["category", "title"])

    summary = (
        df.groupby("category")
        .agg(books=("upc", "count"), avg_price_gbp=("price_gbp", "mean"),
             min_price_gbp=("price_gbp", "min"), max_price_gbp=("price_gbp", "max"),
             avg_rating=("rating", "mean"), units_in_stock=("in_stock", "sum"))
        .round(2)
        .sort_values("books", ascending=False)
        .reset_index()
    )

    paths = {"csv": out_dir / "books.csv", "xlsx": out_dir / "books.xlsx", "report": out_dir / "run_report.txt"}
    df.to_csv(paths["csv"], index=False, encoding="utf-8-sig")  # utf-8-sig: Excel shows the pound sign correctly
    with pd.ExcelWriter(paths["xlsx"], engine="openpyxl") as xl:
        df.to_excel(xl, sheet_name="Books", index=False)
        summary.to_excel(xl, sheet_name="By category", index=False)
        pd.DataFrame(report, columns=["Check", "Value"]).to_excel(xl, sheet_name="Run report", index=False)
        _tidy(xl.sheets["Books"], money_cols=("price_gbp", "price_excl_tax_gbp"))
        _tidy(xl.sheets["By category"], money_cols=("avg_price_gbp", "min_price_gbp", "max_price_gbp"))
        _tidy(xl.sheets["Run report"])
        xl.sheets["Run report"].column_dimensions["A"].width = 34
        xl.sheets["Run report"].column_dimensions["B"].width = 70
    paths["report"].write_text("\n".join(f"{k}: {v}" for k, v in report) + "\n", encoding="utf-8")
    return paths
