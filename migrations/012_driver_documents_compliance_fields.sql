ALTER TABLE driver_documents ADD COLUMN verified_by TEXT;
ALTER TABLE driver_documents ADD COLUMN verified_at TEXT;
ALTER TABLE driver_documents ADD COLUMN rejection_reason TEXT;
ALTER TABLE driver_documents ADD COLUMN is_required INTEGER NOT NULL DEFAULT 1;
ALTER TABLE driver_documents ADD COLUMN issued_at TEXT;
ALTER TABLE driver_documents ADD COLUMN updated_by TEXT;
