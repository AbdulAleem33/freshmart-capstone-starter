"""Analysis functions. Each returns a DataFrame; each is timed."""
import time, functools
import numpy as np, pandas as pd
def timed(fn):
    """TODO: decorator that prints how long fn took. Use functools.wraps."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(
            f"{fn.__name__} took {elapsed:.4f} seconds"
        )
        return result
    return wrapper
@timed
def top_margin(sales, products, store_id=None, n=10):
    """Top n products by (net_price - cost_price) * qty. Exclude rows where margin_ok is False."""
    df = sales.copy()
    p = products.copy()
    # Optional store filter
    if store_id is not None:
        df = df[df["store_id"] == store_id].copy()
    # Keep only valid-margin products
    valid_products = p[p["margin_ok"] == True].copy()
    # Join sales with product information
    df = df.merge(
        valid_products[
            ["product_id", "product_name", "category", "cost_price"]
        ],
        on="product_id",
        how="inner"
    )
    # Calculate margin per unit
    df["margin_per_unit"] = (
        df["net_price"] - df["cost_price"]
    )
    # Calculate total margin
    df["margin"] = (
        df["margin_per_unit"] * df["qty"]
    )
    # Aggregate by product
    result = (
        df.groupby(
            ["product_id", "product_name", "category"],
            as_index=False
        )
        .agg(
            units=("qty", "sum"),
            revenue=("revenue", "sum"),
            margin=("margin", "sum")
        )
        .sort_values(
            "margin",
            ascending=False
        )
        .head(n)
        .reset_index(drop=True)
    )
    return result
    raise NotImplementedError
@timed
def promo_lift(sales, promotions, rng=None, n_perm=1000):
    """For each promotion: qty/day in the promo window vs same weekdays in the 8 weeks before; permutation p-value."""
    if rng is None:
        rng = np.random.default_rng(42)
    df = sales.copy()
    promos = promotions.copy()
    # Make sure dates are datetime
    df["sale_date"] = pd.to_datetime(
        df["sale_date"],
        errors="coerce"
    )
    promos["start_date"] = pd.to_datetime(
        promos["start_date"],
        errors="coerce"
    )
    promos["end_date"] = pd.to_datetime(
        promos["end_date"],
        errors="coerce"
    )
    # Aggregate quantity by product/store/day
    daily = (
        df.groupby(
            ["product_id", "store_id", "sale_date"],
            as_index=False
        )["qty"]
        .sum()
    )
    results = []
    for _, promo in promos.iterrows():

        product_id = promo["product_id"]
        store_id = promo["store_id"]
        start = promo["start_date"]
        end = promo["end_date"]
        # ----------------------------------------------------
        # Promotion period
        # ----------------------------------------------------
        promo_dates = pd.date_range(
            start=start,
            end=end,
            freq="D"
        )
        promo_daily = daily[
            (daily["product_id"] == product_id)
            & (daily["store_id"] == store_id)
            & (daily["sale_date"].isin(promo_dates))
        ].copy()
        # Include zero-sale days
        promo_full = pd.DataFrame({
            "sale_date": promo_dates
        })
        promo_full = promo_full.merge(
            promo_daily[["sale_date", "qty"]],
            on="sale_date",
            how="left"
        )
        promo_full["qty"] = promo_full["qty"].fillna(0)
        # ----------------------------------------------------
        # Previous 8 weeks
        # ----------------------------------------------------
        baseline_start = start - pd.Timedelta(weeks=8)
        baseline_end = start - pd.Timedelta(days=1)
        baseline_dates = pd.date_range(
            start=baseline_start,
            end=baseline_end,
            freq="D"
        )
        # Keep only same weekdays as promotion dates
        promo_weekdays = set(
            promo_dates.dayofweek
        )
        baseline_dates = baseline_dates[
            baseline_dates.dayofweek.isin(promo_weekdays)
        ]
        baseline_daily = daily[
            (daily["product_id"] == product_id)
            & (daily["store_id"] == store_id)
            & (daily["sale_date"].isin(baseline_dates))
        ].copy()
        baseline_full = pd.DataFrame({
            "sale_date": baseline_dates
        })
        baseline_full = baseline_full.merge(
            baseline_daily[["sale_date", "qty"]],
            on="sale_date",
            how="left"
        )
        baseline_full["qty"] = baseline_full["qty"].fillna(0)
        treatment = promo_full["qty"].to_numpy()
        control = baseline_full["qty"].to_numpy()
        promo_mean = (
            treatment.mean()
            if len(treatment) > 0
            else np.nan
        )
        baseline_mean = (
            control.mean()
            if len(control) > 0
            else np.nan
        )
        lift = promo_mean - baseline_mean
        if baseline_mean != 0 and not np.isnan(baseline_mean):
            lift_pct = (
                lift / baseline_mean * 100
            )
        else:
            lift_pct = np.nan
        # ----------------------------------------------------
        # Permutation test
        # ----------------------------------------------------
        p_value = np.nan
        if len(treatment) > 0 and len(control) > 0:
            combined = np.concatenate(
                [treatment, control]
            )
            observed = abs(
                treatment.mean() - control.mean()
            )
            count = 0
            for _ in range(n_perm):
                shuffled = rng.permutation(
                    combined
                )
                perm_treatment = shuffled[
                    :len(treatment)
                ]
                perm_control = shuffled[
                    len(treatment):
                ]
                perm_difference = abs(
                    perm_treatment.mean()
                    - perm_control.mean()
                )
                if perm_difference >= observed:
                    count += 1
            p_value = (
                (count + 1)
                / (n_perm + 1)
            )
        results.append({
            "promo_id": promo["promo_id"],
            "product_id": product_id,
            "store_id": store_id,
            "start_date": start,
            "end_date": end,
            "promo_qty_per_day": promo_mean,
            "baseline_qty_per_day": baseline_mean,
            "lift_qty_per_day": lift,
            "lift_pct": lift_pct,
            "p_value": p_value
        })
    return pd.DataFrame(results)
    raise NotImplementedError
@timed
def patterns(sales, products):
    """Return two pivot tables: category x weekday units, category x month units."""
    df = sales.copy()
    df["sale_date"] = pd.to_datetime(
        df["sale_date"],
        errors="coerce"
    )
    # Add weekday
    df["weekday"] = df["sale_date"].dt.day_name()
    # Add month
    df["month"] = df["sale_date"].dt.month
    # Join category
    df = df.merge(
        products[
            ["product_id", "category"]
        ],
        on="product_id",
        how="left"
    )
    # Desired weekday order
    weekday_order = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday"
    ]
    weekday_table = pd.pivot_table(
        df,
        index="category",
        columns="weekday",
        values="qty",
        aggfunc="sum",
        fill_value=0
    )
    weekday_table = weekday_table.reindex(
        columns=weekday_order,
        fill_value=0
    )
    # Month table
    month_table = pd.pivot_table(
        df,
        index="category",
        columns="month",
        values="qty",
        aggfunc="sum",
        fill_value=0
    )
    month_table = month_table.reindex(
        columns=range(1, 13),
        fill_value=0
    )
    return weekday_table, month_table
    raise NotImplementedError
@timed
def stockouts(sales, min_rate=1.5, min_run=6):
    """
    Find product-store pairs that:
    - normally sell at least min_rate receipts/day
    - have a consecutive zero-sales run of at least min_run days
    """
@timed
def stockouts(sales, min_rate=1.5, min_run=6):
    """Find product-store pairs with normal sales and long zero-sale runs."""
    df = sales.copy()
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    results = []
    for (product_id, store_id), group in df.groupby(
        ["product_id", "store_id"]
    ):
        # Daily receipt count 
        daily = (
            group.groupby("sale_date")["receipt_id"]
            .nunique()
        )
        # Complete date range
        dates = pd.date_range(
            df["sale_date"].min(),
            df["sale_date"].max(), 
            freq="D"
        )
        daily = daily.reindex(dates, fill_value=0)
        # Normal selling rate
        avg_rate = daily.mean()
        if avg_rate < min_rate:
            continue
        # Find longest consecutive zero-sales run
        zero = daily.eq(0)
        current_run = 0
        max_run = 0
        run_start = None
        best_start = None
        best_end = None
        for date, is_zero in zero.items():
            if is_zero:
                if current_run == 0:
                    run_start = date
                current_run += 1
                if current_run > max_run:
                    max_run = current_run
                    best_start = run_start
                    best_end = date
            else:
                current_run = 0
        if max_run >= min_run:
            results.append({
                "product_id": product_id,
                "store_id": store_id,
                "avg_receipts_per_day": avg_rate,
                "zero_run_days": max_run,
                "stockout_start": best_start,
                "stockout_end": best_end
            })
    # IMPORTANT:
    # Always return the expected columns, even when no stock-outs exist.
    return pd.DataFrame(
        results,
        columns=[
            "product_id",
            "store_id",
            "avg_receipts_per_day",
            "zero_run_days",
            "stockout_start",
            "stockout_end"
        ]
    )
@timed
def store_productivity(sales, products, stores):
    """Revenue, margin, receipts and margin per sq ft per store."""
    df = sales.copy()
    p = products.copy()
    st = stores.copy()
    # --------------------------------------------------------
    # Join cost price
    # --------------------------------------------------------
    df = df.merge(
        p[
            ["product_id", "cost_price", "margin_ok"]
        ],
        on="product_id",
        how="left"
    )
    # --------------------------------------------------------
    # Margin
    # --------------------------------------------------------
    df["margin"] = (
        (df["net_price"] - df["cost_price"])
        * df["qty"]
    )
    # Only valid-margin products
    df.loc[
        df["margin_ok"] == False,
        "margin"
    ] = 0
    # --------------------------------------------------------
    # Store aggregation
    # --------------------------------------------------------
    result = (
        df.groupby("store_id")
        .agg(
            revenue=("revenue", "sum"),
            margin=("margin", "sum"),
            receipts=("receipt_id", "nunique")
        )
        .reset_index()
    )
    # --------------------------------------------------------
    # Add store information
    # --------------------------------------------------------
    result = result.merge(
        st[
            ["store_id", "store_name", "city", "floor_area_sqft"]
        ],
        on="store_id",
        how="left"
    )
    # --------------------------------------------------------
    # Margin per square foot
    # --------------------------------------------------------
    result["margin_per_sqft"] = (
        result["margin"]
        / result["floor_area_sqft"]
    )
    return (
        result[
            [
                "store_id",
                "store_name",
                "city",
                "floor_area_sqft",
                "revenue",
                "margin",
                "receipts",
                "margin_per_sqft"
            ]
        ]
        .sort_values(
            "revenue",
            ascending=False
        )
        .reset_index(drop=True)
    )
    raise NotImplementedError
