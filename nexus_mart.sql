-- =====================================================================
--  NEXUS MART DATABASE (MySQL 8 / MariaDB 10.5+)
--  Tables: locations, sellers, customers, products, orders,
--          order_items, payments, shipping, returns
--
--  HOW TO RUN
--   1. Unzip data.zip somewhere and replace every  /PATH/TO/data/  below
--      with that folder (forward slashes, trailing slash, e.g. C:/data/).
--   2. Start the client with local-infile enabled:
--         mysql --local-infile=1 -u root -p < nexus_mart.sql
--      (MySQL Workbench: Edit Connection > Advanced > add
--       OPT_LOCAL_INFILE=1 to "Others", then run the script.)
-- =====================================================================

DROP DATABASE IF EXISTS nexus_mart;
CREATE DATABASE nexus_mart CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE nexus_mart;

SET GLOBAL local_infile = 1;
SET FOREIGN_KEY_CHECKS = 0;

-- ---------------------------------------------------------------------
--  1. SCHEMA
-- ---------------------------------------------------------------------

CREATE TABLE locations (
    city_id          INT           NOT NULL,
    city             VARCHAR(50)   NOT NULL,
    province         VARCHAR(50),
    region           VARCHAR(20),
    latitude         DECIMAL(9,4),
    longitude        DECIMAL(9,4),
    population_tier  VARCHAR(20),
    PRIMARY KEY (city_id)
);

CREATE TABLE sellers (
    seller_id    VARCHAR(10)   NOT NULL,
    seller_name  VARCHAR(100)  NOT NULL,
    join_date    DATE,
    seller_tier  VARCHAR(20),
    city_id      INT,
    rating       DECIMAL(2,1),
    PRIMARY KEY (seller_id),
    KEY idx_sellers_city (city_id),
    CONSTRAINT fk_sellers_city FOREIGN KEY (city_id) REFERENCES locations (city_id)
);

CREATE TABLE customers (
    customer_id        VARCHAR(10)   NOT NULL,
    full_name          VARCHAR(100)  NOT NULL,
    email              VARCHAR(100),
    phone              VARCHAR(20),
    gender             CHAR(1),
    registration_date  DATE,
    city_id            INT,
    birth_year         SMALLINT,
    PRIMARY KEY (customer_id),
    KEY idx_customers_city (city_id),
    CONSTRAINT fk_customers_city FOREIGN KEY (city_id) REFERENCES locations (city_id)
);

CREATE TABLE products (
    product_id    VARCHAR(10)   NOT NULL,
    product_name  VARCHAR(100)  NOT NULL,
    category      VARCHAR(50),
    sub_category  VARCHAR(50),
    brand         VARCHAR(50),
    list_price    DECIMAL(16,6),
    cost_price    DECIMAL(12,2),
    weight_kg     DECIMAL(8,2),
    seller_id     VARCHAR(10),
    PRIMARY KEY (product_id),
    KEY idx_products_seller (seller_id),
    KEY idx_products_category (category),
    CONSTRAINT fk_products_seller FOREIGN KEY (seller_id) REFERENCES sellers (seller_id)
);

CREATE TABLE orders (
    order_id       VARCHAR(10)   NOT NULL,
    customer_id    VARCHAR(10)   NOT NULL,
    order_date     DATE,
    order_status   VARCHAR(20),
    ship_city_id   INT,
    order_total    DECIMAL(16,6),
    discount_code  VARCHAR(20),
    channel        VARCHAR(20),
    PRIMARY KEY (order_id),
    KEY idx_orders_customer (customer_id),
    KEY idx_orders_date (order_date),
    KEY idx_orders_ship_city (ship_city_id),
    CONSTRAINT fk_orders_customer  FOREIGN KEY (customer_id)  REFERENCES customers (customer_id),
    CONSTRAINT fk_orders_ship_city FOREIGN KEY (ship_city_id) REFERENCES locations (city_id)
);

CREATE TABLE order_items (
    order_item_id    VARCHAR(15)   NOT NULL,
    order_id         VARCHAR(10)   NOT NULL,
    product_id       VARCHAR(10)   NOT NULL,
    seller_id        VARCHAR(10)   NOT NULL,
    quantity         INT           NOT NULL,
    unit_price       DECIMAL(16,6) NOT NULL,
    discount_amount  DECIMAL(12,2) NOT NULL DEFAULT 0,
    total_price      DECIMAL(15,2) NOT NULL,
    PRIMARY KEY (order_item_id),
    KEY idx_oi_order (order_id),
    KEY idx_oi_product (product_id),
    KEY idx_oi_seller (seller_id),
    CONSTRAINT fk_oi_order   FOREIGN KEY (order_id)   REFERENCES orders (order_id),
    CONSTRAINT fk_oi_product FOREIGN KEY (product_id) REFERENCES products (product_id),
    CONSTRAINT fk_oi_seller  FOREIGN KEY (seller_id)  REFERENCES sellers (seller_id)
);

CREATE TABLE payments (
    payment_id      VARCHAR(15)   NOT NULL,
    order_id        VARCHAR(10)   NOT NULL,
    payment_method  VARCHAR(30),
    payment_status  VARCHAR(20),
    amount          DECIMAL(16,6),
    payment_date    DATE,
    PRIMARY KEY (payment_id),
    KEY idx_payments_order (order_id),
    CONSTRAINT fk_payments_order FOREIGN KEY (order_id) REFERENCES orders (order_id)
);

CREATE TABLE shipping (
    shipment_id      VARCHAR(15)   NOT NULL,
    order_id         VARCHAR(10)   NOT NULL,
    courier          VARCHAR(30),
    shipped_date     DATE,
    delivered_date   DATE,
    shipping_fee     DECIMAL(12,2),
    delivery_status  VARCHAR(30),
    PRIMARY KEY (shipment_id),
    KEY idx_shipping_order (order_id),
    CONSTRAINT fk_shipping_order FOREIGN KEY (order_id) REFERENCES orders (order_id)
);

CREATE TABLE returns (
    return_id      VARCHAR(10)   NOT NULL,
    order_item_id  VARCHAR(15)   NOT NULL,
    return_date    DATE,
    return_reason  VARCHAR(50),
    return_status  VARCHAR(20),
    refund_amount  DECIMAL(16,6),
    PRIMARY KEY (return_id),
    KEY idx_returns_item (order_item_id),
    CONSTRAINT fk_returns_item FOREIGN KEY (order_item_id) REFERENCES order_items (order_item_id)
);

-- ---------------------------------------------------------------------
--  2. LOAD DATA  (parents first, children last)
--     Empty CSV cells are loaded as NULL.
--     Money columns use 6 decimals because the source data has up to
--     6 decimal places; nothing is rounded on load.
-- ---------------------------------------------------------------------

LOAD DATA LOCAL INFILE '/PATH/TO/data/locations.csv'
INTO TABLE locations
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    city_id,
    city,
    @province,
    @region,
    @latitude,
    @longitude,
    @population_tier
)
SET
    province = NULLIF(@province, ''),
    region = NULLIF(@region, ''),
    latitude = NULLIF(@latitude, ''),
    longitude = NULLIF(@longitude, ''),
    population_tier = NULLIF(@population_tier, '');

LOAD DATA LOCAL INFILE '/PATH/TO/data/sellers.csv'
INTO TABLE sellers
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    seller_id,
    seller_name,
    @join_date,
    @seller_tier,
    @city_id,
    @rating
)
SET
    join_date = NULLIF(@join_date, ''),
    seller_tier = NULLIF(@seller_tier, ''),
    city_id = NULLIF(@city_id, ''),
    rating = NULLIF(@rating, '');

LOAD DATA LOCAL INFILE '/PATH/TO/data/customers.csv'
INTO TABLE customers
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    customer_id,
    full_name,
    @email,
    @phone,
    @gender,
    @registration_date,
    @city_id,
    @birth_year
)
SET
    email = NULLIF(@email, ''),
    phone = NULLIF(@phone, ''),
    gender = NULLIF(@gender, ''),
    registration_date = NULLIF(@registration_date, ''),
    city_id = NULLIF(@city_id, ''),
    birth_year = NULLIF(@birth_year, '');

LOAD DATA LOCAL INFILE '/PATH/TO/data/products.csv'
INTO TABLE products
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    product_id,
    product_name,
    @category,
    @sub_category,
    @brand,
    @list_price,
    @cost_price,
    @weight_kg,
    @seller_id
)
SET
    category = NULLIF(@category, ''),
    sub_category = NULLIF(@sub_category, ''),
    brand = NULLIF(@brand, ''),
    list_price = NULLIF(@list_price, ''),
    cost_price = NULLIF(@cost_price, ''),
    weight_kg = NULLIF(@weight_kg, ''),
    seller_id = NULLIF(@seller_id, '');

LOAD DATA LOCAL INFILE '/PATH/TO/data/orders.csv'
INTO TABLE orders
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    order_id,
    customer_id,
    @order_date,
    @order_status,
    @ship_city_id,
    @order_total,
    @discount_code,
    @channel
)
SET
    order_date = NULLIF(@order_date, ''),
    order_status = NULLIF(@order_status, ''),
    ship_city_id = NULLIF(@ship_city_id, ''),
    order_total = NULLIF(@order_total, ''),
    discount_code = NULLIF(@discount_code, ''),
    channel = NULLIF(@channel, '');

LOAD DATA LOCAL INFILE '/PATH/TO/data/order_items.csv'
INTO TABLE order_items
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    order_item_id,
    order_id,
    product_id,
    seller_id,
    quantity,
    unit_price,
    discount_amount,
    total_price
);

LOAD DATA LOCAL INFILE '/PATH/TO/data/payments.csv'
INTO TABLE payments
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    payment_id,
    order_id,
    @payment_method,
    @payment_status,
    @amount,
    @payment_date
)
SET
    payment_method = NULLIF(@payment_method, ''),
    payment_status = NULLIF(@payment_status, ''),
    amount = NULLIF(@amount, ''),
    payment_date = NULLIF(@payment_date, '');

LOAD DATA LOCAL INFILE '/PATH/TO/data/shipping.csv'
INTO TABLE shipping
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    shipment_id,
    order_id,
    @courier,
    @shipped_date,
    @delivered_date,
    @shipping_fee,
    @delivery_status
)
SET
    courier = NULLIF(@courier, ''),
    shipped_date = NULLIF(@shipped_date, ''),
    delivered_date = NULLIF(@delivered_date, ''),
    shipping_fee = NULLIF(@shipping_fee, ''),
    delivery_status = NULLIF(@delivery_status, '');

LOAD DATA LOCAL INFILE '/PATH/TO/data/returns.csv'
INTO TABLE returns
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(
    return_id,
    order_item_id,
    @return_date,
    @return_reason,
    @return_status,
    @refund_amount
)
SET
    return_date = NULLIF(@return_date, ''),
    return_reason = NULLIF(@return_reason, ''),
    return_status = NULLIF(@return_status, ''),
    refund_amount = NULLIF(@refund_amount, '');

SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------
--  3. QUICK CHECK  (row counts)
-- ---------------------------------------------------------------------
SELECT 'locations'   AS tbl, COUNT(*) AS row_count FROM locations   UNION ALL
SELECT 'sellers',            COUNT(*) FROM sellers     UNION ALL
SELECT 'customers',          COUNT(*) FROM customers   UNION ALL
SELECT 'products',           COUNT(*) FROM products    UNION ALL
SELECT 'orders',             COUNT(*) FROM orders      UNION ALL
SELECT 'order_items',        COUNT(*) FROM order_items UNION ALL
SELECT 'payments',           COUNT(*) FROM payments    UNION ALL
SELECT 'shipping',           COUNT(*) FROM shipping    UNION ALL
SELECT 'returns',            COUNT(*) FROM returns;
