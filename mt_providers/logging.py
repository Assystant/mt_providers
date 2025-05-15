import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    """Configure package-level logging."""
    logger = logging.getLogger("mt_providers")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(level)
