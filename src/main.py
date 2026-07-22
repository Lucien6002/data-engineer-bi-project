from __future__ import annotations

import logging

from config.logging_config import setup_logging
from etl.extract import load_raw_tables
from etl.load import initialize_schema, load_dim_customer, load_dim_date, load_dim_product, load_dim_seller, load_fact_sales
from etl.transform import build_dim_customer, build_dim_date, build_dim_product, build_dim_seller, build_fact_sales
from etl.validation import validate_dim_customer, validate_dim_date, validate_dim_product, validate_dim_seller, validate_fact_sales


logger = logging.getLogger(__name__)


def _format_row_count(row_count: int) -> str:
	return f"{row_count:,}".replace(",", " ")


def run_pipeline() -> None:
	setup_logging()
	logger.info("Starting pipeline")
	raw_data = load_raw_tables()

	initialize_schema()

	dim_date = build_dim_date(
		[
			raw_data["orders"]["order_purchase_timestamp"],
			raw_data["orders"]["order_approved_at"],
			raw_data["orders"]["order_delivered_carrier_date"],
			raw_data["orders"]["order_delivered_customer_date"],
			raw_data["orders"]["order_estimated_delivery_date"],
			raw_data["order_items"]["shipping_limit_date"],
		]
	)
	dim_customer = build_dim_customer(raw_data["customers"])
	dim_product = build_dim_product(raw_data["products"], raw_data["product_category_translation"])
	dim_seller = build_dim_seller(raw_data["sellers"])
	fact_sales = build_fact_sales(raw_data["orders"], raw_data["order_items"], raw_data["customers"])

	logger.info("Loading dim_date")
	dim_date_rows = load_dim_date(dim_date)
	validate_dim_date(dim_date_rows)
	logger.info("%s rows inserted", _format_row_count(dim_date_rows))

	logger.info("Loading dim_customer")
	dim_customer_rows = load_dim_customer(dim_customer)
	validate_dim_customer(dim_customer_rows)
	logger.info("%s rows inserted", _format_row_count(dim_customer_rows))

	logger.info("Loading dim_product")
	dim_product_rows = load_dim_product(dim_product)
	validate_dim_product(dim_product_rows)
	logger.info("%s rows inserted", _format_row_count(dim_product_rows))

	logger.info("Loading dim_seller")
	dim_seller_rows = load_dim_seller(dim_seller)
	validate_dim_seller(dim_seller_rows)
	logger.info("%s rows inserted", _format_row_count(dim_seller_rows))

	logger.info("Loading fact_sales")
	fact_sales_rows = load_fact_sales(fact_sales)
	validate_fact_sales(fact_sales_rows)
	logger.info("%s rows inserted", _format_row_count(fact_sales_rows))

	logger.info("Pipeline completed")


if __name__ == "__main__":
	run_pipeline()
