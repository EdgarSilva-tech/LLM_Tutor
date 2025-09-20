import logging
import sys
from pythonjsonlogger import jsonlogger


def get_logger(name: str):
    """
    Configures and returns a logger that outputs logs in JSON format.
    """
    # Get the existing logger instance
    logger = logging.getLogger(name)

    # Check if the logger already has handlers
    # to avoid adding them multiple times
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        logHandler = logging.StreamHandler(sys.stdout)

        # Define the format of the JSON logs.
        # You can add more fields from the LogRecord object if needed.
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s'
        )

        logHandler.setFormatter(formatter)
        logger.addHandler(logHandler)
        # Prevent logs from propagating to the root
        # logger in case it's configured elsewhere
        logger.propagate = False

    return logger
