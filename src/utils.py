import logging

def get_logger(name: str, log_file: str = 'logs/log.txt') -> logging.Logger:
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # Console Handler
        c_handler = logging.StreamHandler()
        c_handler.setFormatter(formatter)

        # File Handler
        f_handler = logging.FileHandler(log_file)
        f_handler.setFormatter(formatter)

        # Add them
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)

    return logger