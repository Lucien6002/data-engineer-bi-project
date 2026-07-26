from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def _to_date_series(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.date


def build_dim_date(date_sources: Iterable[pd.Series]) -> pd.DataFrame:
    date_series = []
    for source in date_sources:
        current_dates = pd.to_datetime(source, errors="coerce").dropna().dt.normalize()
        if not current_dates.empty:
            date_series.append(current_dates)

    if not date_series:
        return pd.DataFrame(
            columns=[
                "date_key",
                "full_date",
                "day_of_month",
                "day_name",
                "day_of_week",
                "week_of_year",
                "month_number",
                "month_name",
                "quarter_number",
                "year_number",
                "is_weekend",
            ]
        ).copy()

    all_dates = pd.concat(date_series, ignore_index=True).drop_duplicates().sort_values()
    calendar = pd.date_range(start=all_dates.min(), end=all_dates.max(), freq="D")
    dim_date = pd.DataFrame({"full_date": calendar.date})
    dim_date["date_key"] = pd.Series(calendar).dt.strftime("%Y%m%d").astype(int)

    full_datetime = pd.to_datetime(dim_date["full_date"])
    dim_date["day_of_month"] = full_datetime.dt.day.astype(int)
    dim_date["day_name"] = full_datetime.dt.day_name()
    dim_date["day_of_week"] = full_datetime.dt.dayofweek.add(1).astype(int)
    dim_date["week_of_year"] = full_datetime.dt.isocalendar().week.astype(int)
    dim_date["month_number"] = full_datetime.dt.month.astype(int)
    dim_date["month_name"] = full_datetime.dt.month_name()
    dim_date["quarter_number"] = full_datetime.dt.quarter.astype(int)
    dim_date["year_number"] = full_datetime.dt.year.astype(int)
    dim_date["is_weekend"] = full_datetime.dt.dayofweek.ge(5)

    return dim_date[
        [
            "date_key",
            "full_date",
            "day_of_month",
            "day_name",
            "day_of_week",
            "week_of_year",
            "month_number",
            "month_name",
            "quarter_number",
            "year_number",
            "is_weekend",
        ]
    ].copy()


def build_dim_customer(customers: pd.DataFrame) -> pd.DataFrame:
    dim_customer = customers[
        [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ]
    ].drop_duplicates(subset=["customer_id"]).copy()

    dim_customer["customer_zip_code_prefix"] = dim_customer["customer_zip_code_prefix"].astype("Int64")
    return dim_customer


def build_dim_product(products: pd.DataFrame, category_translation: pd.DataFrame) -> pd.DataFrame:
    dim_product = products.merge(category_translation, on="product_category_name", how="left")
    dim_product["product_category_name"] = dim_product["product_category_name"].fillna("unknown")
    dim_product["product_category_name_english"] = dim_product["product_category_name_english"].fillna(
        dim_product["product_category_name"]
    )

    dim_product = dim_product[
        [
            "product_id",
            "product_category_name",
            "product_category_name_english",
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ]
    ].drop_duplicates(subset=["product_id"]).copy()

    dim_product["product_category_name"] = dim_product["product_category_name"].fillna("unknown")
    dim_product["product_category_name_english"] = dim_product["product_category_name_english"].fillna("unknown")

    return dim_product.rename(
        columns={
            "product_name_lenght": "product_name_length",
            "product_description_lenght": "product_description_length",
        }
    )


def build_dim_seller(sellers: pd.DataFrame) -> pd.DataFrame:
    return sellers[
        ["seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"]
    ].drop_duplicates(subset=["seller_id"]).copy()


def build_fact_sales(orders: pd.DataFrame, order_items: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    fact_sales = order_items.merge(
        orders[
            [
                "order_id",
                "customer_id",
                "order_purchase_timestamp",
                "order_approved_at",
                "order_delivered_carrier_date",
                "order_delivered_customer_date",
                "order_estimated_delivery_date",
            ]
        ],
        on="order_id",
        how="left",
    )

    fact_sales = fact_sales.merge(
        customers[["customer_id", "customer_unique_id"]],
        on="customer_id",
        how="left",
    )

    fact_sales = fact_sales[
        [
            "order_id",
            "order_item_id",
            "customer_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
            "price",
            "freight_value",
        ]
    ].copy()

    fact_sales["item_total_value"] = fact_sales["price"] + fact_sales["freight_value"]
    return fact_sales
