from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sqlalchemy import text

from config.database import get_engine


class ValidationError(RuntimeError):
	"""Raised when a loaded table does not match the expected shape or constraints."""


@dataclass(frozen=True)
class TableValidationSpec:
	table_name: str
	expected_rows: int
	required_columns: tuple[str, ...] = ()
	unique_columns: tuple[str, ...] = ()


def _get_table_statistics(table_name: str, required_columns: tuple[str, ...], unique_columns: tuple[str, ...]) -> dict[str, int]:
	engine = get_engine()
	select_parts = ["COUNT(*) AS total_rows"]

	for column in required_columns:
		select_parts.append(f"COUNT(*) FILTER (WHERE {column} IS NULL) AS null_{column}")

	if unique_columns:
		key_expression = ", ".join(unique_columns)
		select_parts.append(
			f"COUNT(*) - COUNT(DISTINCT ({key_expression})) AS duplicate_rows"
		)

	query = text(f"SELECT {', '.join(select_parts)} FROM dw.{table_name}")
	with engine.connect() as connection:
		stats = pd.read_sql_query(query, connection).iloc[0].to_dict()

	return {key: int(value or 0) for key, value in stats.items()}


def validate_table(spec: TableValidationSpec) -> None:
	stats = _get_table_statistics(spec.table_name, spec.required_columns, spec.unique_columns)

	if stats["total_rows"] != spec.expected_rows:
		raise ValidationError(
			f"{spec.table_name}: expected {spec.expected_rows} rows, found {stats['total_rows']}"
		)

	for column in spec.required_columns:
		null_key = f"null_{column}"
		if stats.get(null_key, 0) != 0:
			raise ValidationError(
				f"{spec.table_name}: column {column} contains {stats[null_key]} null value(s)"
			)

	if spec.unique_columns and stats.get("duplicate_rows", 0) != 0:
		unique_label = ", ".join(spec.unique_columns)
		raise ValidationError(
			f"{spec.table_name}: duplicate rows detected for unique key(s) {unique_label}"
		)


def validate_dim_date(expected_rows: int) -> None:
	validate_table(
		TableValidationSpec(
			table_name="dim_date",
			expected_rows=expected_rows,
			required_columns=("date_key", "full_date"),
			unique_columns=("date_key", "full_date"),
		)
	)


def validate_dim_customer(expected_rows: int) -> None:
	validate_table(
		TableValidationSpec(
			table_name="dim_customer",
			expected_rows=expected_rows,
			required_columns=("customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city", "customer_state"),
			unique_columns=("customer_id",),
		)
	)


def validate_dim_product(expected_rows: int) -> None:
	validate_table(
		TableValidationSpec(
			table_name="dim_product",
			expected_rows=expected_rows,
			required_columns=("product_id", "product_category_name", "product_category_name_english"),
			unique_columns=("product_id",),
		)
	)


def validate_dim_seller(expected_rows: int) -> None:
	validate_table(
		TableValidationSpec(
			table_name="dim_seller",
			expected_rows=expected_rows,
			required_columns=("seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"),
			unique_columns=("seller_id",),
		)
	)


def validate_fact_sales(expected_rows: int) -> None:
	validate_table(
		TableValidationSpec(
			table_name="fact_sales",
			expected_rows=expected_rows,
			required_columns=(
				"order_id",
				"order_item_id",
				"customer_key",
				"product_key",
				"seller_key",
				"purchase_date_key",
				"price",
				"freight_value",
			),
			unique_columns=("order_id", "order_item_id"),
		)
	)