-- Schema definition for the transactions table

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day DATE NOT NULL,
    entity TEXT NOT NULL,
    product TEXT NOT NULL,
    price_tier TEXT NOT NULL,
    anticipation_method TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    installments INTEGER NOT NULL CHECK (installments > 0),
    amount_transacted REAL NOT NULL CHECK (amount_transacted >= 0),
    quantity_transactions INTEGER NOT NULL CHECK (quantity_transactions >= 0),
    quantity_of_merchants INTEGER NOT NULL CHECK (quantity_of_merchants >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);