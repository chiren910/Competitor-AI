# utils/logger.py
import logging

def setup_logger():
    logging.basicConfig(
        filename='logs/extractor.log',
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
    )
    return logging.getLogger(__name__)
