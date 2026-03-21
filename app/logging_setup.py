import logging
import os
from logging.handlers import RotatingFileHandler


class _DefaultFieldsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        if not hasattr(record, "client_ip"):
            record.client_ip = "-"
        return True


def configure_logging(service_name: str) -> None:
    root_logger = logging.getLogger()
    if getattr(root_logger, "_bazar_logging_configured", False):
        return

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s ip=%(client_ip)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )

    handlers: list[logging.Handler] = [logging.StreamHandler()]

    log_file = os.getenv("LOG_FILE")
    if log_file:
        max_bytes = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))
        backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
        handlers.append(RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"))

    default_fields_filter = _DefaultFieldsFilter()
    for handler in handlers:
        handler.setFormatter(formatter)
        handler.addFilter(default_fields_filter)

    root_logger.handlers.clear()
    root_logger.setLevel(level)
    for handler in handlers:
        root_logger.addHandler(handler)

    root_logger._bazar_logging_configured = True
    logging.getLogger(__name__).info("Logging configured for %s", service_name)
