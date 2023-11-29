import os
from config.logger import Logger


class ApiConfig:
    # API Config
    APP_NAME = os.environ["AZURE_ENV_NAME"]
    STATIC_DIR = os.getenv("STATIC_DIR", "static")
    LOG_TO_FILE = os.getenv("LOG_TO_FILE", False)
    USE_SEARCH = os.getenv("USE_SEARCH", False)
    TEMPERATURE = os.getenv("TEMPERATURE", 0.5)
    APP_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO")
