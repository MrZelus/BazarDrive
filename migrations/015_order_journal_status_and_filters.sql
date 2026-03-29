ALTER TABLE order_journal_records ADD COLUMN order_status TEXT NOT NULL DEFAULT 'accepted';
ALTER TABLE order_journal_records ADD COLUMN event_at TEXT;

CREATE INDEX IF NOT EXISTS idx_order_journal_records_status
ON order_journal_records(order_status);

CREATE INDEX IF NOT EXISTS idx_order_journal_records_event_at
ON order_journal_records(event_at);
