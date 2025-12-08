import logging

def get_logger(name: str):
    # Create a custom logger
    logger = logging.getLogger(name)

    # Set the level for your custom logger
    logger.setLevel(logging.CRITICAL + 1)

    # Create handlers if they are not already created
    if not logger.handlers:
        # Create a file handler (or StreamHandler for console output)
        file_handler = logging.FileHandler('application.log')
        # file_handler = logging.StreamHandler()  # Use this for console output

        # Create a logging format
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        # Add the file handler to the logger
        logger.addHandler(file_handler)

    return logger


def set_logging_level(level_name: str):
    level_map = {
        "none": logging.CRITICAL + 1,
        "debug": logging.DEBUG,
        "all": logging.CRITICAL
    }
    level = level_map.get(level_name.lower(), logging.CRITICAL + 1)

    for logger_name in logging.root.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)

# # Initialize the logger
# logger = setup_logger()


