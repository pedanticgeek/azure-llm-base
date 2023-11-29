# Imports for local logging
import os
import logging
import traceback


class CustomFormatter(logging.Formatter):
    """Logging colored formatter, adapted from https://stackoverflow.com/a/56944256/3638629"""

    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset,
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def create_logger(name, file, level):
    """Creates a logger"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    # Create formatter and apply it to both handlers
    fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    if bool(file):
        if not os.path.exists(os.getcwd() + "/logs"):
            os.mkdir(os.getcwd() + "/logs")
            # Create a log file handler to write all logs
        try:
            os.remove(os.getcwd() + f"/logs/{name}.log")
        except:
            pass
        file_logger = logging.FileHandler(os.getcwd() + f"/logs/{name}.log")
        file_logger.setLevel(getattr(logging, level))
        file_logger.setFormatter(CustomFormatter(fmt))
        logger.addHandler(file_logger)
    # Create a console log handler to handle only ERROR level logs
    console_logger = logging.StreamHandler()
    console_logger.setLevel(logging.INFO)
    console_logger.setFormatter(CustomFormatter(fmt))
    logger.addHandler(console_logger)

    return logger


class Logger:
    def __init__(self, name: str, file: bool | str, level: str):
        self.logger = create_logger(name, file, level)
        self.logger.setLevel(level)

    def log(self, exception):
        getattr(self.logger, exception["level"])(exception["message"])
        return exception["message"]

    def info(self, text):
        return self.log(
            {
                "message": text,
                "level": "info",
            }
        )

    def debug(self, text):
        return self.log({"message": text, "level": "debug"})

    def warning(self, text):
        return self.log({"message": text, "level": "warning"})

    def error(self, text):
        tb = traceback.format_exc()
        return self.log({"message": str(text) + f"\nTraceback: {tb}", "level": "error"})

    def exception(self, text):
        return self.error(text)

    def embedding_limit_reached(self, retry_state):
        self.warning(
            "Rate limited on the OpenAI embeddings API, sleeping before retrying..."
        )

    def vision_limit_reached(self, retry_state):
        self.warning(
            "Rate limited on the OpenAI vision API, sleeping before retrying..."
        )
