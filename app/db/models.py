"""
models.py — SQL schema cho SQLite
"""

CREATE_PRODUCTS_TABLE = """
CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    price       REAL    NOT NULL,          -- giá sau markup (đơn vị K)
    stock       INTEGER NOT NULL DEFAULT 0,
    raw_text    TEXT,                      -- nội dung gốc từ bot nguồn
    source_hash TEXT    UNIQUE,            -- hash để chống duplicate
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id    INTEGER PRIMARY KEY,
    username   TEXT,
    first_name TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_PAYMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS payments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_code  TEXT    NOT NULL UNIQUE,   -- mã đơn ngắn, VD: KLG123
    user_id     INTEGER NOT NULL,
    username    TEXT,
    product_id  INTEGER,
    status      TEXT    DEFAULT 'pending', -- pending | confirmed | rejected
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""
