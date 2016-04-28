# -*- coding: utf-8
import logging
from config import LOG_PATH
from config import LOG_LEVEL

logger = logging.getLogger('watcher')
if LOG_LEVEL == "INFO":
    logger.setLevel(logging.INFO)
elif LOG_LEVEL == "DEBUG":
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
# create file handler which logs even debug messages
fh = logging.FileHandler(LOG_PATH + '/watcher.log')
fh.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
