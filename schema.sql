-- Database Schema for Macadamia – Warehouse Control

-- Warehouses Table
CREATE TABLE IF NOT EXISTS warehouses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Roles Table
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL -- ADMIN, WAREHOUSE_USER
);

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role_id INTEGER NOT NULL,
    warehouse_id INTEGER, -- Assigned warehouse
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
);

-- Products Table
CREATE TABLE IF NOT EXISTS products (
    barcode TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    photo_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inventory Table (Current Stock per Warehouse)
CREATE TABLE IF NOT EXISTS inventory (
    warehouse_id INTEGER NOT NULL,
    product_barcode TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (warehouse_id, product_barcode),
    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (product_barcode) REFERENCES products(barcode),
    CONSTRAINT positive_stock CHECK (quantity >= 0)
);

-- Movement Types
CREATE TABLE IF NOT EXISTS movement_types (
    id TEXT PRIMARY KEY, -- ENTRY, EXIT, TRANSFER, ADJUSTMENT, INITIAL_INVENTORY
    prefix TEXT NOT NULL
);

-- Movements Table (Documents)
CREATE TABLE IF NOT EXISTS movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_number TEXT UNIQUE, -- Generated only upon confirmation (e.g., ENT-00001)
    type_id TEXT NOT NULL,
    source_warehouse_id INTEGER,
    target_warehouse_id INTEGER,
    status TEXT DEFAULT 'DRAFT', -- DRAFT, CONFIRMED
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP,
    FOREIGN KEY (type_id) REFERENCES movement_types(id),
    FOREIGN KEY (source_warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (target_warehouse_id) REFERENCES warehouses(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT valid_status CHECK (status IN ('DRAFT', 'CONFIRMED'))
);

-- Movement Items
CREATE TABLE IF NOT EXISTS movement_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movement_id INTEGER NOT NULL,
    product_barcode TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (movement_id) REFERENCES movements(id),
    FOREIGN KEY (product_barcode) REFERENCES products(barcode),
    CONSTRAINT positive_quantity CHECK (quantity > 0)
);

-- Initial Movement Types Seed
INSERT OR IGNORE INTO movement_types (id, prefix) VALUES 
('ENTRY', 'ENT'), 
('EXIT', 'SAL'), 
('TRANSFER', 'TRA'), 
('ADJUSTMENT', 'AJU'), 
('INITIAL_INVENTORY', 'INI');

-- Initial Data Seed
INSERT OR IGNORE INTO roles (name) VALUES ('ADMIN'), ('WAREHOUSE_USER');
