from __future__ import annotations

import argparse
import csv
import re
from datetime import datetime
from pathlib import Path


DATE_FORMATS = (
    "%Y-%m-%d",
    "%m/%d/%Y",
    "%Y/%m/%d",
    "%d-%m-%Y",
)

PRODUCT_NAME_MAP = {
    "salla starter kit": "Salla Starter Kit",
    "premium abaya": "Premium Abaya",
    "leather wallet": "Leather Wallet",
    "smart watch": "Smart Watch",
    "kids backpack": "Kids Backpack",
}


def parse_money(value: str) -> float:
    cleaned = re.sub(r"[^0-9.\-]", "", value or "")
    return round(float(cleaned), 2) if cleaned else 0.0


def parse_date(value: str) -> str:
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"Unsupported date format: {value}")


def normalize_product_name(value: str) -> str:
    key = " ".join((value or "").strip().lower().split())
    return PRODUCT_NAME_MAP.get(key, value.strip().title())


def clean_orders(input_path: Path, output_path: Path) -> dict[str, int]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows_read = 0
    rows_written = 0
    rows_skipped = 0

    with input_path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        fieldnames = [
            "order_id",
            "date",
            "product_name",
            "revenue",
            "cost",
            "profit",
            "quantity",
            "ad_spend",
            "status",
        ]

        with output_path.open("w", newline="", encoding="utf-8") as target:
            writer = csv.DictWriter(target, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                rows_read += 1
                revenue = parse_money(row["revenue"])
                status = (row.get("status") or "").strip().lower()

                if revenue <= 0 or status in {"cancelled", "refunded"}:
                    rows_skipped += 1
                    continue

                cost = parse_money(row["cost"])
                cleaned_row = {
                    "order_id": row["order_id"].strip(),
                    "date": parse_date(row["date"]),
                    "product_name": normalize_product_name(row["product_name"]),
                    "revenue": f"{revenue:.2f}",
                    "cost": f"{cost:.2f}",
                    "profit": f"{revenue - cost:.2f}",
                    "quantity": int(parse_money(row.get("quantity", "1"))),
                    "ad_spend": f"{parse_money(row.get('ad_spend', '0')):.2f}",
                    "status": status,
                }
                writer.writerow(cleaned_row)
                rows_written += 1

    return {
        "rows_read": rows_read,
        "rows_written": rows_written,
        "rows_skipped": rows_skipped,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean ecommerce order data for Power BI.")
    parser.add_argument("--input", required=True, type=Path, help="Path to raw orders CSV.")
    parser.add_argument("--output", required=True, type=Path, help="Path for cleaned CSV output.")
    args = parser.parse_args()

    stats = clean_orders(args.input, args.output)
    print(
        "Cleaned orders: "
        f"{stats['rows_written']} written, "
        f"{stats['rows_skipped']} skipped, "
        f"{stats['rows_read']} read."
    )


if __name__ == "__main__":
    main()

