ALTER TABLE guest_profiles ADD COLUMN verification_state TEXT NOT NULL DEFAULT 'unverified';
ALTER TABLE guest_profiles ADD COLUMN verification_rejection_reason TEXT;
ALTER TABLE guest_profiles ADD COLUMN verification_decided_at DATETIME;
ALTER TABLE guest_profiles ADD COLUMN verification_decided_by TEXT;
UPDATE guest_profiles
SET verification_state = 'verified'
WHERE is_verified = 1;

CREATE TABLE IF NOT EXISTS guest_profile_verification_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    from_state TEXT,
    to_state TEXT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT,
    actor TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES guest_profiles(id)
);

CREATE INDEX IF NOT EXISTS idx_guest_profile_verification_history_profile_id
    ON guest_profile_verification_history(profile_id, id DESC);
