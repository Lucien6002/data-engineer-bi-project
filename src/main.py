from etl.extract import load_raw_tables
from etl.load import initialize_schema, load_dim_customer, load_dim_date, load_dim_product, load_dim_seller, load_fact_sales
from etl.transform import build_dim_customer, build_dim_date, build_dim_product, build_dim_seller, build_fact_sales


def run_pipeline() -> None:
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

	load_dim_date(dim_date)
	load_dim_customer(dim_customer)
	load_dim_product(dim_product)
	load_dim_seller(dim_seller)
	load_fact_sales(fact_sales)


if __name__ == "__main__":
	run_pipeline()
