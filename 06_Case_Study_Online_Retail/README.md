# Online Retail Dashboard Case Study

This case study uses a real open ecommerce dataset from the UCI Machine Learning Repository.

## Source

- Dataset: Online Retail
- Provider: UCI Machine Learning Repository
- License: CC BY 4.0
- Rows in source: 541,909
- Date range after cleaning: 2010-12-01 to 2011-12-09
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
| Revenue | $10,666,685 |
| Orders | 19,960 |
| Customers | 4,338 |
| Countries | 38 |
| Products | 3,922 |
| Average Order Value | $534 |
| Top Country | United Kingdom |
| Top Product | Dotcom Postage |

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
