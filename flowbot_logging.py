import logging


def get_logger(name: str):
    # # Create a custom logger
    # logger = logging.getLogger(name)

    # # Set the level for your custom logger
    # logger.setLevel(logging.DEBUG)

    # # Create a file handler (or StreamHandler for console output)
    # file_handler = logging.FileHandler('application.log')
    # # file_handler = logging.StreamHandler()  # Use this for console output

    # # Create a logging format
    # formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    # file_handler.setFormatter(formatter)

    # # Add the file handler to the logger
    # logger.addHandler(file_handler)
    # Create a custom logger
    logger = logging.getLogger(name)

    # Set the level for your custom logger
    logger.setLevel(logging.DEBUG)

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


# # Initialize the logger
# logger = setup_logger()


