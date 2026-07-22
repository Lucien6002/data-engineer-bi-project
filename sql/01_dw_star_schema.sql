DROP SCHEMA IF EXISTS dw CASCADE;
CREATE SCHEMA dw;

CREATE TABLE IF NOT EXISTS dw.dim_date (
    date_key integer PRIMARY KEY,
    full_date date NOT NULL UNIQUE,
    day_of_month smallint NOT NULL,
    day_name text NOT NULL,
    day_of_week smallint NOT NULL,
    week_of_year smallint NOT NULL,
    month_number smallint NOT NULL,
    month_name text NOT NULL,
    quarter_number smallint NOT NULL,
    year_number integer NOT NULL,
    is_weekend boolean NOT NULL
);

CREATE TABLE IF NOT EXISTS dw.dim_customer (
    customer_key bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id text NOT NULL UNIQUE,
    customer_unique_id text NOT NULL,
    customer_zip_code_prefix integer NOT NULL,
    customer_city text NOT NULL,
    customer_state char(2) NOT NULL
);

CREATE TABLE IF NOT EXISTS dw.dim_product (
    product_key bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    product_id text NOT NULL UNIQUE,
    product_category_name text NOT NULL,
    product_category_name_english text NOT NULL,
    product_name_length numeric(10, 2),
    product_description_length numeric(10, 2),
    product_photos_qty integer,
    product_weight_g integer,
    product_length_cm integer,
    product_height_cm integer,
    product_width_cm integer
);

CREATE TABLE IF NOT EXISTS dw.dim_seller (
    seller_key bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    seller_id text NOT NULL UNIQUE,
    seller_zip_code_prefix integer NOT NULL,
    seller_city text NOT NULL,
    seller_state char(2) NOT NULL
);

CREATE TABLE IF NOT EXISTS dw.fact_sales (
    sales_key bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id text NOT NULL,
    order_item_id integer NOT NULL,
    customer_key bigint NOT NULL REFERENCES dw.dim_customer (customer_key),
    product_key bigint NOT NULL REFERENCES dw.dim_product (product_key),
    seller_key bigint NOT NULL REFERENCES dw.dim_seller (seller_key),
    purchase_date_key integer NOT NULL REFERENCES dw.dim_date (date_key),
    approved_date_key integer REFERENCES dw.dim_date (date_key),
    shipped_date_key integer REFERENCES dw.dim_date (date_key),
    delivered_date_key integer REFERENCES dw.dim_date (date_key),
    estimated_delivery_date_key integer REFERENCES dw.dim_date (date_key),
    shipping_limit_date_key integer REFERENCES dw.dim_date (date_key),
    price numeric(12, 2) NOT NULL,
    freight_value numeric(12, 2) NOT NULL,
    item_total_value numeric(12, 2) GENERATED ALWAYS AS (price + freight_value) STORED,
    UNIQUE (order_id, order_item_id)
);

CREATE INDEX IF NOT EXISTS idx_fact_sales_customer_key ON dw.fact_sales (customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_product_key ON dw.fact_sales (product_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_seller_key ON dw.fact_sales (seller_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_purchase_date_key ON dw.fact_sales (purchase_date_key);