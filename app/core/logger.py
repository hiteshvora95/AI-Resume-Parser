import sys
from loguru import logger
from config.variables import LOG_LEVEL


logger.remove()

logger.add(
    sys.stdout,
    level=LOG_LEVEL,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    ),
    colorize=True,
)

logger.add(
    "logs/app.log",
    level=LOG_LEVEL,
    rotation="10 MB",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
)


def get_logger(name: str):
    """
    Return a logger instance.

    Pass __name__ from any module to get a logger that automatically
    includes the module name in every log line.

    Usage:
        logger = get_logger(__name__)
        logger.info("Something happened")
    """
    return logger.bind(name=name)
