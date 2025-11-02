import logging
from .config import args

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(args.log),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TinnitusDB")

def log(msg):
    """Улучшенное логгирование с уровнями"""
    logger.info(msg)

def error(msg):
    """Логирование ошибок"""
    logger.error(msg)
