from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import text

from config.database import get_engine


SCHEMA_SQL_PATH = Path(__file__).resolve().parents[2] / "sql" / "01_dw_star_schema.sql"


def initialize_schema() -> None:
    engine = get_engine()
    sql_content = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
    statements = [statement.strip() for statement in sql_content.split(";") if statement.strip()]

    with engine.begin() as connection:
        for statement in statements:
            connection.exec_driver_sql(statement)


def reset_tables() -> None:
    engine = get_engine()
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE TABLE dw.fact_sales, dw.dim_seller, dw.dim_product, dw.dim_customer, dw.dim_date RESTART IDENTITY CASCADE"
            )
        )


def write_dataframe(table_name: str, dataframe: pd.DataFrame) -> int:
    engine = get_engine()
    dataframe.to_sql(table_name, con=engine, schema="dw", if_exists="append", index=False, chunksize=500)
    return len(dataframe)


def _load_key_map(table_name: str, natural_key: str, surrogate_key: str) -> pd.Series:
    engine = get_engine()
    query = text(f"SELECT {surrogate_key}, {natural_key} FROM dw.{table_name}")
    with engine.connect() as connection:
        mapping = pd.read_sql_query(query, connection)
    if natural_key == "full_date":
        mapping[natural_key] = pd.to_datetime(mapping[natural_key], errors="coerce").dt.date
    return mapping.set_index(natural_key)[surrogate_key]


def load_dim_date(dim_date: pd.DataFrame) -> int:
    return write_dataframe("dim_date", dim_date)


def load_dim_customer(dim_customer: pd.DataFrame) -> int:
    return write_dataframe("dim_customer", dim_customer)


def load_dim_product(dim_product: pd.DataFrame) -> int:
    return write_dataframe("dim_product", dim_product)


def load_dim_seller(dim_seller: pd.DataFrame) -> int:
    return write_dataframe("dim_seller", dim_seller)


def load_fact_sales(fact_sales: pd.DataFrame) -> int:
    purchase_date = pd.to_datetime(fact_sales["order_purchase_timestamp"], errors="coerce").dt.date
    approved_date = pd.to_datetime(fact_sales["order_approved_at"], errors="coerce").dt.date
    shipped_date = pd.to_datetime(fact_sales["order_delivered_carrier_date"], errors="coerce").dt.date
    delivered_date = pd.to_datetime(fact_sales["order_delivered_customer_date"], errors="coerce").dt.date
    estimated_date = pd.to_datetime(fact_sales["order_estimated_delivery_date"], errors="coerce").dt.date
    shipping_limit_date = pd.to_datetime(fact_sales["shipping_limit_date"], errors="coerce").dt.date

    customer_map = _load_key_map("dim_customer", "customer_id", "customer_key")
    product_map = _load_key_map("dim_product", "product_id", "product_key")
    seller_map = _load_key_map("dim_seller", "seller_id", "seller_key")
    date_map = _load_key_map("dim_date", "full_date", "date_key")

    fact_ready = pd.DataFrame(
        {
            "order_id": fact_sales["order_id"],
            "order_item_id": fact_sales["order_item_id"],
            "customer_key": fact_sales["customer_id"].map(customer_map),
            "product_key": fact_sales["product_id"].map(product_map),
            "seller_key": fact_sales["seller_id"].map(seller_map),
            "purchase_date_key": purchase_date.map(date_map),
            "approved_date_key": approved_date.map(date_map),
            "shipped_date_key": shipped_date.map(date_map),
            "delivered_date_key": delivered_date.map(date_map),
            "estimated_delivery_date_key": estimated_date.map(date_map),
            "shipping_limit_date_key": shipping_limit_date.map(date_map),
            "price": fact_sales["price"],
            "freight_value": fact_sales["freight_value"],
        }
    )

    missing_key_columns = [
        column
        for column in [
            "customer_key",
            "product_key",
            "seller_key",
            "purchase_date_key",
        ]
        if fact_ready[column].isna().any()
    ]
    if missing_key_columns:
        raise ValueError(f"Unable to resolve surrogate keys for columns: {', '.join(missing_key_columns)}")

    return write_dataframe("fact_sales", fact_ready)
