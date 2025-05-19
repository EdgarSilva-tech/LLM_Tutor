from loguru import logger

def add_logging(file: str):
    logger.remove(0)
    logger.add(f"logs/{file}", format="{time} | {level} | {message}")