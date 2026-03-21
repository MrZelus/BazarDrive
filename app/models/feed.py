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
    'driver_license',
    'sts',
    'osago',
    'diagnostic_card',
    'self_employed_certificate',
}

ALLOWED_DRIVER_DOCUMENT_STATUSES = {'uploaded', 'checking', 'approved', 'rejected', 'expired'}
DRIVER_DOCUMENT_NUMBER_MIN_LEN = 3
DRIVER_DOCUMENT_NUMBER_MAX_LEN = 64
DRIVER_DOCUMENT_FILE_URL_MAX_LEN = 2048
