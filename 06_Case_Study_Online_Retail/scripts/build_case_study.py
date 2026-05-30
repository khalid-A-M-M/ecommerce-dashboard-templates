from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ASSETS = ROOT / "assets"


def money(value: float) -> str:
    return f"${value:,.0f}"


def pct(value: float) -> str:
    return f"{value:.1f}%"


def load_data() -> pd.DataFrame:
    source = DATA / "extracted" / "Online Retail.xlsx"
    if not source.exists():
        source = DATA / "Online_Retail.xlsx"
    df = pd.read_excel(source, dtype={"InvoiceNo": str, "StockCode": str})
    df.columns = [c.strip() for c in df.columns]
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned = cleaned.dropna(subset=["InvoiceNo", "Description", "InvoiceDate"])
    cleaned["InvoiceNo"] = cleaned["InvoiceNo"].astype(str)
    cleaned["Description"] = cleaned["Description"].astype(str).str.strip()
    cleaned = cleaned[~cleaned["InvoiceNo"].str.startswith("C", na=False)]
    cleaned = cleaned[cleaned["Quantity"] > 0]
    cleaned = cleaned[cleaned["UnitPrice"] > 0]
    cleaned["InvoiceDate"] = pd.to_datetime(cleaned["InvoiceDate"])
    cleaned["Date"] = cleaned["InvoiceDate"].dt.date.astype(str)
    cleaned["Month"] = cleaned["InvoiceDate"].dt.to_period("M").astype(str)
    cleaned["Revenue"] = cleaned["Quantity"] * cleaned["UnitPrice"]
    cleaned["ProductName"] = (
        cleaned["Description"]
        .str.replace(r"\s+", " ", regex=True)
        .str.title()
    )
    return cleaned[
        [
            "InvoiceNo",
            "StockCode",
            "ProductName",
            "Quantity",
            "InvoiceDate",
            "Date",
            "Month",
            "UnitPrice",
            "Revenue",
            "CustomerID",
            "Country",
        ]
    ]


def build_outputs(cleaned: pd.DataFrame) -> dict:
    DATA.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)

    monthly = (
        cleaned.groupby("Month", as_index=False)
        .agg(
            revenue=("Revenue", "sum"),
            quantity=("Quantity", "sum"),
            orders=("InvoiceNo", "nunique"),
            customers=("CustomerID", "nunique"),
        )
        .sort_values("Month")
    )
    monthly["aov"] = monthly["revenue"] / monthly["orders"]

    products = (
        cleaned.groupby("ProductName", as_index=False)
        .agg(
            revenue=("Revenue", "sum"),
            quantity=("Quantity", "sum"),
            orders=("InvoiceNo", "nunique"),
        )
        .sort_values("revenue", ascending=False)
        .head(20)
    )

    countries = (
        cleaned.groupby("Country", as_index=False)
        .agg(revenue=("Revenue", "sum"), orders=("InvoiceNo", "nunique"))
        .sort_values("revenue", ascending=False)
        .head(15)
    )

    invoice_revenue = cleaned.groupby("InvoiceNo")["Revenue"].sum()
    kpis = {
        "source_rows": int(541909),
        "clean_rows": int(len(cleaned)),
        "date_start": str(cleaned["Date"].min()),
        "date_end": str(cleaned["Date"].max()),
        "total_revenue": float(cleaned["Revenue"].sum()),
        "orders": int(cleaned["InvoiceNo"].nunique()),
        "customers": int(cleaned["CustomerID"].nunique()),
        "countries": int(cleaned["Country"].nunique()),
        "products": int(cleaned["StockCode"].nunique()),
        "average_order_value": float(invoice_revenue.mean()),
        "top_country": str(countries.iloc[0]["Country"]),
        "top_product": str(products.iloc[0]["ProductName"]),
    }

    cleaned.sample(min(10000, len(cleaned)), random_state=7).to_csv(
        DATA / "dashboard_ready_sample.csv", index=False
    )
    monthly.to_csv(DATA / "monthly_summary.csv", index=False)
    products.to_csv(DATA / "top_products.csv", index=False)
    countries.to_csv(DATA / "country_summary.csv", index=False)
    (DATA / "kpi_summary.json").write_text(
        json.dumps(kpis, indent=2), encoding="utf-8"
    )

    return {
        "kpis": kpis,
        "monthly": monthly,
        "products": products,
        "countries": countries,
    }


def write_dashboard_html(outputs: dict) -> None:
    k = outputs["kpis"]
    monthly = outputs["monthly"].tail(12)
    products = outputs["products"].head(5)
    countries = outputs["countries"].head(3)

    max_rev = monthly["revenue"].max()
    monthly_rows = "\n".join(
        f"<div class='bar-row'><span>{row.Month}</span><div class='track'><div class='bar' style='width:{row.revenue / max_rev * 100:.1f}%'></div></div><b>{money(row.revenue)}</b></div>"
        for row in monthly.itertuples()
    )
    product_rows = "\n".join(
        f"<tr><td>{row.ProductName[:42]}</td><td>{money(row.revenue)}</td><td>{int(row.quantity):,}</td><td>{int(row.orders):,}</td></tr>"
        for row in products.itertuples()
    )
    country_rows = "\n".join(
        f"<tr><td>{row.Country}</td><td>{money(row.revenue)}</td><td>{int(row.orders):,}</td></tr>"
        for row in countries.itertuples()
    )

    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Online Retail Dashboard Case Study</title>
<style>
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: Arial, Segoe UI, sans-serif; background: #f4f7fb; color: #142033; overflow: hidden; }}
.wrap {{ width: 1500px; height: 900px; margin: 0 auto; padding: 34px 42px; overflow: hidden; }}
header {{ display: flex; justify-content: space-between; align-items: end; margin-bottom: 20px; }}
h1 {{ font-size: 38px; margin: 0; letter-spacing: 0; }}
.sub {{ font-size: 18px; color: #5f6e83; margin-top: 7px; }}
.badge {{ background: #fff; border: 1px solid #d8e1ec; border-radius: 8px; padding: 12px 16px; font-size: 18px; }}
.kpis {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 18px; margin-bottom: 18px; }}
.card, .panel {{ background: #fff; border: 1px solid #dce5ef; border-radius: 8px; box-shadow: 0 10px 26px rgba(29, 45, 68, .06); }}
.card {{ padding: 18px 21px; height: 124px; }}
.label {{ color: #66758a; font-size: 17px; margin-bottom: 10px; }}
.value {{ font-size: 34px; font-weight: 800; }}
.note {{ color: #0f766e; font-size: 16px; margin-top: 8px; }}
.grid {{ display: grid; grid-template-columns: 1.35fr 1fr; gap: 22px; }}
.panel {{ padding: 20px 22px; margin-bottom: 18px; }}
.panel h2 {{ margin: 0 0 13px; font-size: 23px; }}
.bars {{ display: grid; gap: 7px; }}
.bar-row {{ display: grid; grid-template-columns: 90px 1fr 120px; align-items: center; gap: 12px; font-size: 15px; }}
.track {{ height: 16px; background: #edf2f8; border-radius: 4px; overflow: hidden; }}
.bar {{ height: 100%; background: #2563eb; }}
table {{ width: 100%; border-collapse: collapse; font-size: 16px; }}
td, th {{ padding: 9px 8px; border-bottom: 1px solid #e7edf5; text-align: left; }}
th {{ color: #64748b; background: #f8fafc; }}
.source {{ color: #64748b; font-size: 16px; margin-top: 4px; }}
</style>
</head>
<body>
<main class="wrap">
  <header>
    <div>
      <h1>Online Retail Dashboard Case Study</h1>
      <div class="sub">Open-source ecommerce transactions cleaned and prepared for Power BI</div>
    </div>
    <div class="badge">UCI Online Retail Dataset | {k["date_start"]} to {k["date_end"]}</div>
  </header>
  <section class="kpis">
    <div class="card"><div class="label">Revenue</div><div class="value">{money(k["total_revenue"])}</div><div class="note">{k["orders"]:,} orders</div></div>
    <div class="card"><div class="label">Customers</div><div class="value">{k["customers"]:,}</div><div class="note">{k["countries"]} countries</div></div>
    <div class="card"><div class="label">Avg Order Value</div><div class="value">{money(k["average_order_value"])}</div><div class="note">Invoice-level average</div></div>
    <div class="card"><div class="label">Clean Rows</div><div class="value">{k["clean_rows"]:,}</div><div class="note">from {k["source_rows"]:,} raw rows</div></div>
    <div class="card"><div class="label">Products</div><div class="value">{k["products"]:,}</div><div class="note">unique stock codes</div></div>
  </section>
  <section class="grid">
    <div>
      <div class="panel" style="height: 346px;">
        <h2>Monthly Revenue Trend</h2>
        <div class="bars">{monthly_rows}</div>
      </div>
      <div class="panel" style="height: 222px;">
        <h2>Top Countries</h2>
        <table><thead><tr><th>Country</th><th>Revenue</th><th>Orders</th></tr></thead><tbody>{country_rows}</tbody></table>
      </div>
    </div>
    <div>
      <div class="panel" style="height: 346px;">
        <h2>Top Products by Revenue</h2>
        <table><thead><tr><th>Product</th><th>Revenue</th><th>Qty</th><th>Orders</th></tr></thead><tbody>{product_rows}</tbody></table>
      </div>
      <div class="panel" style="height: 222px;">
        <h2>Client Outcome</h2>
        <table><tbody>
          <tr><td>Problem</td><td>Raw transaction file with cancellations and invalid rows</td></tr>
          <tr><td>Work</td><td>Cleaned, modeled, summarized, and made dashboard-ready</td></tr>
          <tr><td>Output</td><td>CSV tables, KPI summary, Power BI measures, portfolio visuals</td></tr>
        </tbody></table>
        <div class="source">Source: UCI Machine Learning Repository, Online Retail dataset, CC BY 4.0.</div>
      </div>
    </div>
  </section>
</main>
</body>
</html>"""
    (ASSETS / "online_retail_dashboard.html").write_text(html, encoding="utf-8")


def write_case_readme(outputs: dict) -> None:
    k = outputs["kpis"]
    readme = f"""# Online Retail Dashboard Case Study

This case study uses a real open ecommerce dataset from the UCI Machine Learning Repository.

## Source

- Dataset: Online Retail
- Provider: UCI Machine Learning Repository
- License: CC BY 4.0
- Rows in source: {k["source_rows"]:,}
- Date range after cleaning: {k["date_start"]} to {k["date_end"]}
- Source page: https://archive.ics.uci.edu/dataset/352/online+retail

## Client Problem

The client has raw ecommerce transaction data and needs a clear dashboard for revenue, orders, customers, countries, and product performance.

## Work Performed

1. Removed cancelled invoices.
2. Removed invalid rows with negative quantity or zero price.
3. Standardized product names and dates.
4. Calculated revenue.
5. Created dashboard-ready CSV outputs.
6. Built a visual dashboard image for portfolio use.

## KPI Summary

| Metric | Value |
| --- | ---: |
| Revenue | {money(k["total_revenue"])} |
| Orders | {k["orders"]:,} |
| Customers | {k["customers"]:,} |
| Countries | {k["countries"]:,} |
| Products | {k["products"]:,} |
| Average Order Value | {money(k["average_order_value"])} |
| Top Country | {k["top_country"]} |
| Top Product | {k["top_product"]} |

## Outputs

| File | Purpose |
| --- | --- |
| `data/dashboard_ready_sample.csv` | Sample of cleaned line-level transactions for Power BI |
| `data/monthly_summary.csv` | Monthly revenue, orders, customers, and AOV |
| `data/top_products.csv` | Top products by revenue |
| `data/country_summary.csv` | Revenue and orders by country |
| `data/kpi_summary.json` | KPI values used in the portfolio dashboard |
| `assets/online_retail_dashboard.png` | Client-facing portfolio image |

## Power BI Pages To Build

1. Executive overview.
2. Monthly sales trend.
3. Top products.
4. Country performance.
5. Customer/order summary.
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    raw = load_data()
    cleaned = clean_data(raw)
    outputs = build_outputs(cleaned)
    write_dashboard_html(outputs)
    write_case_readme(outputs)
    print(json.dumps(outputs["kpis"], indent=2))


if __name__ == "__main__":
    main()
