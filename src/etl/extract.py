from __future__ import annotations

from pathlib import Path

import pandas as pd


RAW_FILE_NAMES = {
	"customers": "olist_customers_dataset.csv",
	"orders": "olist_orders_dataset.csv",
	"order_items": "olist_order_items_dataset.csv",
	"products": "olist_products_dataset.csv",
	"sellers": "olist_sellers_dataset.csv",
	"product_category_translation": "product_category_name_translation.csv",
}


def get_raw_data_dir() -> Path:
	return Path(__file__).resolve().parents[2] / "data" / "raw"


def load_raw_tables(data_dir: Path | None = None) -> dict[str, pd.DataFrame]:
	raw_dir = data_dir or get_raw_data_dir()

	datasets: dict[str, pd.DataFrame] = {}
	for name, file_name in RAW_FILE_NAMES.items():
		file_path = raw_dir / file_name
		if not file_path.exists():
			raise FileNotFoundError(f"Missing raw file: {file_path}")
		datasets[name] = pd.read_csv(file_path)

	return datasets
