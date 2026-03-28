MAX_GUEST_FEED_IMAGE_URL_LENGTH = 2048
MAX_GUEST_FEED_IMAGE_DATA_URL_LENGTH = 4_500_000
LOCAL_IMAGE_PATH_PREFIX = "/uploads/feed/"

AUTHOR_MIN_LEN = 2
AUTHOR_MAX_LEN = 40
TEXT_MIN_LEN = 5
TEXT_MAX_LEN = 500

DISPLAY_NAME_MIN_LEN = 2
DISPLAY_NAME_MAX_LEN = 60
EMAIL_MAX_LEN = 254
PHONE_MAX_LEN = 32
ABOUT_MAX_LEN = 400

ALLOWED_PROFILE_ROLES = {"guest_author", "guest_reader"}
ALLOWED_PROFILE_STATUSES = {"active", "blocked", "pending_moderation"}


ALLOWED_DRIVER_DOCUMENT_TYPES = {
    'passport',
    'inn',
    'ogrnip',
    'taxi_license',
    'waybill',
    'driver_license',
    'sts',
    'osago',
    'osgop',
    'diagnostic_card',
    'self_employed_certificate',
}

ALLOWED_DRIVER_DOCUMENT_STATUSES = {'uploaded', 'checking', 'approved', 'rejected', 'expired', 'open', 'closed'}
DRIVER_DOCUMENT_NUMBER_MIN_LEN = 3
DRIVER_DOCUMENT_NUMBER_MAX_LEN = 64
DRIVER_DOCUMENT_FILE_URL_MAX_LEN = 2048

DRIVER_WAYBILL_MED_RESULT_MIN_LEN = 2
DRIVER_WAYBILL_MED_RESULT_MAX_LEN = 128
DRIVER_WAYBILL_VEHICLE_CONDITION_MIN_LEN = 2
DRIVER_WAYBILL_VEHICLE_CONDITION_MAX_LEN = 256
DRIVER_WAYBILL_STOPS_INFO_MAX_LEN = 1000
DRIVER_COMPLIANCE_STATUSES = {
    "profile_incomplete",
    "docs_under_review",
    "expired_documents",
    "waybill_required",
    "restricted",
    "ready_for_orders",
}

DRIVER_EMPLOYMENT_TYPES = {
    "employee",
    "individual_entrepreneur",
    "self_employed",
    "individual_with_permit",
}

DRIVER_TAX_REGIMES = {
    "usn_income",
    "usn_income_expense",
    "npd",
    "other",
}

REQUIRED_DRIVER_DOCUMENT_TYPES = {
    "driver_license",
    "sts",
    "osago",
    "osgop",
    "taxi_license",
}

DRIVER_DOCUMENT_APPROVED_STATUSES = {"approved"}
DRIVER_DOCUMENT_PENDING_STATUSES = {"checking"}
DRIVER_DOCUMENT_REJECTED_STATUSES = {"rejected"}
DRIVER_DOCUMENT_EXPIRED_STATUSES = {"expired"}

DRIVER_REQUIRED_CATEGORY = "B"
DRIVER_MIN_EXPERIENCE_YEARS = 3
DRIVER_MAX_UNPAID_FINES = 3

COMPLIANCE_REASON_MAX_LEN = 500
