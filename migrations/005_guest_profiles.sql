CREATE TABLE IF NOT EXISTS guest_profiles (
    id TEXT PRIMARY KEY,
    role TEXT NOT NULL DEFAULT 'guest_author',
    display_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    about TEXT,
    is_verified INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen_at DATETIME
);
