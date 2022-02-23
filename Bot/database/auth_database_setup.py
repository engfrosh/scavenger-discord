from turtle import back
import sqlalchemy

import logging
import os

import auth_database

CURRENT_DIRECTORY = os.path.dirname(__file__)
LOG_LEVEL = logging.DEBUG

# region Logging Setup
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]

logger = logging.getLogger(SCRIPT_NAME)

if __name__ == "__main__":
    LOG_FILE = CURRENT_DIRECTORY + "/{}.log".format(SCRIPT_NAME)
    if os.path.exists(LOG_FILE):
        try:
            os.remove(LOG_FILE)
        except PermissionError:
            pass
    logging.basicConfig(level=LOG_LEVEL, filename=LOG_FILE)
    logger.debug("Module started.")
    logger.debug("Log file set as: %s", LOG_FILE)

logger.debug("Set current directory as: %s", CURRENT_DIRECTORY)
# endregion

if __name__ == "__main__":
    DATABASE = "sqlite:///test.db"
    engine = sqlalchemy.create_engine(DATABASE, echo=True, future=True)
    logger.debug("Attempting to create all tables.")
    auth_database.mapper_registry.metadata.create_all(engine)
    logger.info("All Tables Created")

