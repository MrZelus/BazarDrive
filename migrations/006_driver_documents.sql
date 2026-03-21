CREATE TABLE IF NOT EXISTS driver_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL DEFAULT 'driver-main',
    type TEXT NOT NULL,
    number TEXT NOT NULL,
    valid_until DATE,
    file_url TEXT,
    status TEXT NOT NULL DEFAULT 'uploaded',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
