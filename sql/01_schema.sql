-- EAIDA MVP — raw loading layer schema
-- Day 3: flat schema, no medallion layers yet (see ADR-0002 once written).
-- Column order and types match data/raw/*.csv exactly — the loader depends on this.

DROP TABLE IF EXISTS returns CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS inventory CASCADE;
DROP TABLE IF EXISTS marketing_campaigns CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS stores CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id     INTEGER PRIMARY KEY,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    email           TEXT NOT NULL,
    city            TEXT NOT NULL,
    segment         TEXT NOT NULL,
    signup_date     DATE NOT NULL
);

CREATE TABLE stores (
    store_id        INTEGER PRIMARY KEY,
    store_name      TEXT NOT NULL,
    city            TEXT NOT NULL,
    state           TEXT NOT NULL,
    region          TEXT NOT NULL,
    open_date       DATE NOT NULL
);

CREATE TABLE products (
    product_id      INTEGER PRIMARY KEY,
    product_name    TEXT NOT NULL,
    category        TEXT NOT NULL,
    unit_price      NUMERIC(10, 2) NOT NULL,
    unit_cost       NUMERIC(10, 2) NOT NULL
);

CREATE TABLE orders (
    order_id        INTEGER PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES customers(customer_id),
    store_id        INTEGER NOT NULL REFERENCES stores(store_id),
    order_date      DATE NOT NULL,
    channel         TEXT NOT NULL,
    order_status    TEXT NOT NULL
);

CREATE TABLE order_items (
    order_item_id   INTEGER PRIMARY KEY,
    order_id        INTEGER NOT NULL REFERENCES orders(order_id),
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    quantity        INTEGER NOT NULL,
    unit_price      NUMERIC(10, 2) NOT NULL,
    line_total      NUMERIC(12, 2) NOT NULL
);

CREATE TABLE inventory (
    inventory_id    INTEGER PRIMARY KEY,
    store_id        INTEGER NOT NULL REFERENCES stores(store_id),
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    snapshot_date   DATE NOT NULL,
    stock_level     INTEGER NOT NULL,
    reorder_level   INTEGER NOT NULL
);

CREATE TABLE returns (
    return_id       INTEGER PRIMARY KEY,
    order_id        INTEGER NOT NULL REFERENCES orders(order_id),
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    return_date     DATE NOT NULL,
    return_reason   TEXT NOT NULL
);

CREATE TABLE marketing_campaigns (
    campaign_id     INTEGER PRIMARY KEY,
    campaign_name   TEXT NOT NULL,
    city_target     TEXT NOT NULL,
    channel         TEXT NOT NULL,
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    budget          NUMERIC(12, 2) NOT NULL,
    spend           NUMERIC(12, 2) NOT NULL
);

-- Indexes on the columns every analytical view below joins or filters on.
-- Small dataset today, but this is the habit that matters at scale.
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_store ON orders(store_id);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);
CREATE INDEX idx_inventory_store_date ON inventory(store_id, snapshot_date);
CREATE INDEX idx_returns_order ON returns(order_id);
CREATE INDEX idx_marketing_city_start ON marketing_campaigns(city_target, start_date);
