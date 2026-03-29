CREATE TABLE IF NOT EXISTS driver_legal_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id TEXT NOT NULL UNIQUE,
    legal_entity_type TEXT NOT NULL DEFAULT 'individual',
    inn TEXT,
    ogrnip TEXT,
    company_name TEXT,
    tax_regime TEXT,
    registration_address TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    status_reason TEXT,
    approved_by TEXT,
    approved_at TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE driver_documents ADD COLUMN driver_id TEXT;
ALTER TABLE driver_documents ADD COLUMN series TEXT;
ALTER TABLE driver_documents ADD COLUMN expires_at TEXT;
ALTER TABLE driver_documents ADD COLUMN verification_status TEXT NOT NULL DEFAULT 'uploaded';
ALTER TABLE driver_documents ADD COLUMN file_id TEXT;

UPDATE driver_documents
SET driver_id = profile_id
WHERE COALESCE(driver_id, '') = '';

UPDATE driver_documents
SET expires_at = valid_until
WHERE COALESCE(expires_at, '') = '' AND COALESCE(valid_until, '') <> '';

UPDATE driver_documents
SET verification_status = status
WHERE COALESCE(verification_status, '') = '';

CREATE TABLE IF NOT EXISTS vehicle_compliance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id TEXT NOT NULL UNIQUE,
    vehicle_id TEXT,
    status TEXT NOT NULL DEFAULT 'pending_review',
    status_reason TEXT,
    inspection_expires_at TEXT,
    insurance_expires_at TEXT,
    permit_expires_at TEXT,
    verified_by TEXT,
    verified_at TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS compliance_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    driver_id TEXT NOT NULL,
    check_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    block_reason TEXT,
    details TEXT,
    checked_by TEXT,
    checked_at TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_driver_legal_profile_driver_id
ON driver_legal_profile(driver_id);

CREATE INDEX IF NOT EXISTS idx_driver_legal_profile_status
ON driver_legal_profile(status);

CREATE INDEX IF NOT EXISTS idx_driver_documents_driver_id
ON driver_documents(driver_id);

CREATE INDEX IF NOT EXISTS idx_driver_documents_status
ON driver_documents(status);

CREATE INDEX IF NOT EXISTS idx_driver_documents_expires_at
ON driver_documents(expires_at);

CREATE INDEX IF NOT EXISTS idx_driver_documents_driver_status_expires
ON driver_documents(driver_id, status, expires_at);

CREATE INDEX IF NOT EXISTS idx_vehicle_compliance_driver_id
ON vehicle_compliance(driver_id);

CREATE INDEX IF NOT EXISTS idx_vehicle_compliance_status
ON vehicle_compliance(status);

CREATE INDEX IF NOT EXISTS idx_vehicle_compliance_expires_at
ON vehicle_compliance(permit_expires_at);

CREATE INDEX IF NOT EXISTS idx_compliance_checks_driver_id
ON compliance_checks(driver_id);

CREATE INDEX IF NOT EXISTS idx_compliance_checks_status
ON compliance_checks(status);
