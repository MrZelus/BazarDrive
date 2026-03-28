CREATE TABLE IF NOT EXISTS order_journal_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT NOT NULL,
    source_request_id INTEGER,

    accepted_at TEXT,
    completed_at TEXT,

    pickup_address TEXT NOT NULL,
    dropoff_address TEXT NOT NULL,

    vehicle_make TEXT,
    vehicle_model TEXT,
    vehicle_license_plate TEXT,
    driver_full_name TEXT,

    eta_planned TEXT,
    arrived_at_actual TEXT,
    ride_completed_at_actual TEXT,

    order_source TEXT,
    passenger_phone TEXT,
    passenger_requirements TEXT,

    profile_id TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_order_journal_records_order_number
ON order_journal_records(order_number);

CREATE INDEX IF NOT EXISTS idx_order_journal_records_profile_id
ON order_journal_records(profile_id);
