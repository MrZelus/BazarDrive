CREATE TABLE IF NOT EXISTS driver_compliance_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL UNIQUE,

    last_name TEXT,
    first_name TEXT,
    middle_name TEXT,

    phone TEXT,
    email TEXT,

    driver_license_category TEXT NOT NULL DEFAULT 'B',
    driving_experience_years INTEGER NOT NULL DEFAULT 0,

    has_medical_contraindications INTEGER NOT NULL DEFAULT 0,
    criminal_record_cleared INTEGER NOT NULL DEFAULT 0,
    unpaid_fines_count INTEGER NOT NULL DEFAULT 0,

    employment_type TEXT NOT NULL DEFAULT 'employee',
    inn TEXT,
    ogrnip TEXT,
    registration_date TEXT,
    tax_regime TEXT,
    activity_region TEXT,

    vehicle_make TEXT,
    vehicle_model TEXT,
    vehicle_license_plate TEXT,

    has_checker_pattern INTEGER NOT NULL DEFAULT 0,
    has_roof_light INTEGER NOT NULL DEFAULT 0,
    has_taximeter INTEGER NOT NULL DEFAULT 0,

    two_factor_enabled INTEGER NOT NULL DEFAULT 0,

    compliance_status TEXT NOT NULL DEFAULT 'profile_incomplete',
    compliance_reason TEXT,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_driver_compliance_profiles_profile_id
ON driver_compliance_profiles(profile_id);

CREATE INDEX IF NOT EXISTS idx_driver_compliance_profiles_compliance_status
ON driver_compliance_profiles(compliance_status);
