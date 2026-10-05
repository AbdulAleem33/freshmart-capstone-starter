"""Every cleaning rule as a function; QualityLog records what each one did."""
"""Every cleaning rule as a function; QualityLog records what each one did."""
import pandas as pd
class QualityLog:
    def __init__(self):
        self.rows = []
    def add(self, problem, affected, fix, why):
        self.rows.append({
            "problem": problem,
            "rows_affected": int(affected),
            "fix": fix,
            "why": why
        })
    def to_frame(self):
        return pd.DataFrame(self.rows)
def clean_products(products, log):
    """Clean product reference data."""
    p = products.copy()
    # ========================================================
    # RULE 1: Product name whitespace
    # ========================================================
    before = p["product_name"].copy()
    p["product_name"] = (
        p["product_name"]
        .astype("string")
        .str.strip()
    )
    affected = (
        before.fillna("").astype(str)
        != p["product_name"].fillna("").astype(str)
    ).sum()
    log.add(
        "Product name has leading/trailing whitespace",
        affected,
        "Strip whitespace from product_name",
        "Keeps product names consistent for reporting and joins"
    )
    # ========================================================
    # RULE 2: Invalid product margin
    # cost_price > unit_price
    # ========================================================
    invalid_margin = (
        p["cost_price"] > p["unit_price"]
    )
    affected = invalid_margin.sum()
    p["margin_ok"] = ~invalid_margin
    log.add(
        "Product cost price is greater than selling price",
        affected,
        "Flag these products with margin_ok=False",
        "Do not silently change reference prices; exclude unreliable margins"
    )
    return p
def clean_sales(sales, products, stores, log):
    """
    Clean sales data in the required order:
    duplicates
    -> unit_price text to number
    -> dates
    -> negative qty
    -> unknown product_id
    -> unknown store_id
    -> missing discount_pct
    Then derive:
        net_price
        revenue
    """
    df = sales.copy()
    # ========================================================
    # RULE 1: Remove duplicates
    # ========================================================
    duplicate_mask = df.duplicated()
    affected = duplicate_mask.sum()
    df = df.drop_duplicates()
    log.add(
        "Duplicate sales rows",
        affected,
        "Remove exact duplicate rows",
        "Prevents the same transaction from being counted twice"
    )
    # ========================================================
    # RULE 2: Convert unit_price to numeric
    # ========================================================
    original_price = df["unit_price"].copy()
    df["unit_price"] = pd.to_numeric(
        df["unit_price"],
        errors="coerce"
    )
    affected = (
        original_price.notna()
        & df["unit_price"].isna()
    ).sum()
    log.add(
        "unit_price contains text/non-numeric values",
        affected,
        "Convert unit_price to numeric; invalid values become NaN",
        "Revenue calculations require numeric prices"
    )
    # Remove rows where unit_price could not be converted
    invalid_price = df["unit_price"].isna()
    affected = invalid_price.sum()
    df = df.loc[~invalid_price].copy()
    log.add(
        "Rows with invalid unit_price",
        affected,
        "Remove rows with unusable unit_price",
        "A sale cannot produce reliable revenue without a valid price"
    )
    # ========================================================
    # RULE 3: Convert dates
    # Handles multiple date formats
    # ========================================================
    original_dates = df["sale_date"].copy()
    # First attempt: normal datetime parsing
    parsed_dates = pd.to_datetime(
        df["sale_date"],
        errors="coerce",
        format="mixed"
    )
    df["sale_date"] = parsed_dates
    affected = (
        original_dates.notna()
        & df["sale_date"].isna()
    ).sum()
    log.add(
        "Invalid or inconsistent sale_date formats",
        affected,
        "Parse sale_date using mixed date-format handling",
        "Creates a consistent datetime field for time-based analysis"
    )
    # Remove invalid dates
    invalid_dates = df["sale_date"].isna()
    affected = invalid_dates.sum()
    df = df.loc[~invalid_dates].copy()
    log.add(
        "Rows with invalid sale_date",
        affected,
        "Remove rows with unusable dates",
        "Time-based sales analysis requires valid dates"
    )
    # ========================================================
    # RULE 4: Negative quantity
    # ========================================================
    negative_qty = df["qty"] < 0
    affected = negative_qty.sum()
    df = df.loc[~negative_qty].copy()
    log.add(
        "Negative quantity",
        affected,
        "Remove rows with negative qty",
        "Negative sales quantities are invalid for this sales dataset"
    )
    # ========================================================
    # RULE 5: Unknown product_id
    # ========================================================
    valid_products = set(
        products["product_id"]
    )
    unknown_product = ~df["product_id"].isin(
        valid_products
    )
    affected = unknown_product.sum()
    df = df.loc[~unknown_product].copy()
    log.add(
        "Unknown product_id",
        affected,
        "Remove sales rows whose product_id is not in products.csv",
        "Ensures every sale can be matched to product information"
    )
    # ========================================================
    # RULE 6: Unknown store_id
    # ========================================================
    valid_stores = set(
        stores["store_id"]
    )
    unknown_store = ~df["store_id"].isin(
        valid_stores
    )
    affected = unknown_store.sum()
    df = df.loc[~unknown_store].copy()
    log.add(
        "Unknown store_id",
        affected,
        "Remove sales rows whose store_id is not in stores.csv",
        "Ensures every sale belongs to a known store"
    )
    # ========================================================
    # RULE 7: Missing discount_pct
    # ========================================================
    missing_discount = df["discount_pct"].isna()
    affected = missing_discount.sum()
    df.loc[
        missing_discount,
        "discount_pct"
    ] = 0
    log.add(
        "Missing discount_pct",
        affected,
        "Replace missing discount_pct with 0",
        "A missing promotion discount is treated as no discount"
    )
    # ========================================================
    # DERIVED COLUMN 1: net_price
    # ========================================================
    df["net_price"] = (
        df["unit_price"]
        * (1 - df["discount_pct"] / 100)
    )
    # ========================================================
    # DERIVED COLUMN 2: revenue
    # ========================================================
    df["revenue"] = (
        df["net_price"]
        * df["qty"]
    )
    # ========================================================
    # Final index
    # ========================================================
    return df.reset_index(drop=True)