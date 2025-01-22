from api.config import settings

ROOT_LEVEL = "DEBUG" if settings.ENVIRONMENT == "local" else "INFO"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%SZ",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "formatter": "default",
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "api.log",
        },
        "file_access": {
            "formatter": "default",
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "access.log",
        },
    },
    "loggers": {
        "": {  # root logger
            "level": ROOT_LEVEL,
            "handlers": ["default", "file"],
        },
        "uvicorn.error": {
            "level": "DEBUG",
            "handlers": ["default", "file"],
            "propagate": False,
        },
        "uvicorn.access": {
            "level": "DEBUG",
            "handlers": ["default", "file_access"],
            "propagate": False,
        },
    },
}
