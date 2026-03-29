CREATE TABLE IF NOT EXISTS driver_reminder_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    reminder_type TEXT NOT NULL,
    entity_key TEXT NOT NULL,
    threshold_key TEXT NOT NULL,
    last_notified_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(profile_id, reminder_type, entity_key, threshold_key)
);

CREATE INDEX IF NOT EXISTS idx_driver_reminder_notifications_profile
    ON driver_reminder_notifications(profile_id);
