import logging
import sys
import json
from pathlib import Path


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logger(name: str, log_file: str = "service.log", level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JsonFormatter())
    logger.addHandler(console_handler)

    # File Handler
    # Ensure logs dir exists
    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)

    file_handler = logging.FileHandler(log_path / log_file)
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)

    return logger
