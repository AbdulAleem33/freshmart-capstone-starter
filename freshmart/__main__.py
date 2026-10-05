"""CLI: python -m freshmart report --store 3 --month 6"""
import argparse
from .loader import SalesLoader
from .cleaner import clean_sales, clean_products, QualityLog
from .report import top_margin, store_productivity, stockouts
def main():
    ap = argparse.ArgumentParser(prog="freshmart")
    sub = ap.add_subparsers(
        dest="cmd",
        required=True
    )
    # --------------------------------------------------------
    # REPORT COMMAND
    # --------------------------------------------------------
    r = sub.add_parser("report")
    r.add_argument(
        "--data",
        default="data",
        help="Folder containing FreshMart CSV files"
    )
    r.add_argument(
        "--store",
        type=int,
        help="Filter report to a specific store"
    )
    r.add_argument(
        "--month",
        type=int,
        help="Filter sales to a month number (1-12)"
    )
    args = ap.parse_args()
    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------
    loader = SalesLoader(args.data)
    data = loader.load_all()
    # --------------------------------------------------------
    # CLEAN DATA
    # --------------------------------------------------------
    log = QualityLog()
    products_clean = clean_products(
        data["products"],
        log
    )
    sales_clean = clean_sales(
        data["sales"],
        products_clean,
        data["stores"],
        log
    )
    # --------------------------------------------------------
    # VALIDATE MONTH
    # --------------------------------------------------------
    if args.month is not None:
        if not 1 <= args.month <= 12:
            ap.error("--month must be between 1 and 12")
        sales_clean = sales_clean[
            sales_clean["sale_date"].dt.month == args.month
        ].copy()
    # --------------------------------------------------------
    # FILTER STORE
    # --------------------------------------------------------
    if args.store is not None:
        sales_clean = sales_clean[
            sales_clean["store_id"] == args.store
        ].copy()
    # --------------------------------------------------------
    # REPORT 1: TOP MARGIN
    # --------------------------------------------------------
    print("\n" + "=" * 70)
    print("TOP MARGIN PRODUCTS")
    print("=" * 70)
    top = top_margin(
        sales_clean,
        products_clean,
        n=10
    )
    if top.empty:
        print("No matching sales found.")
    else:
        print(top.to_string(index=False))
    # --------------------------------------------------------
    # REPORT 2: STORE PRODUCTIVITY
    # --------------------------------------------------------
    print("\n" + "=" * 70)
    print("STORE PRODUCTIVITY")
    print("=" * 70)
    productivity = store_productivity(
        sales_clean,
        products_clean,
        data["stores"]
    )
    if args.store is not None:
        productivity = productivity[
            productivity["store_id"] == args.store
        ]
    if productivity.empty:
        print("No matching store data found.")
    else:
        print(
            productivity.to_string(index=False)
        )
    # --------------------------------------------------------
    # REPORT 3: STOCKOUTS
    # --------------------------------------------------------
    print("\n" + "=" * 70)
    print("STOCKOUTS")
    print("=" * 70)
    stock = stockouts(
        sales_clean
    )
    if args.store is not None:
        stock = stock[
            stock["store_id"] == args.store
        ]
    if stock.empty:
        print("No stockout candidates found.")
    else:
        print(
            stock.to_string(index=False)
        )
if __name__ == "__main__":
    main()
