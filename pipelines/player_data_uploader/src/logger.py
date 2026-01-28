import logging
import sys


def get_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)

    # Only add handlers if none exist to avoid duplicate logs
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)

    return logger
