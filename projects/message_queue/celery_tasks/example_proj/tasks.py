import time
from celery import group
from celery.utils.log import get_task_logger
from .celery import app


# mock dict with filename/content
FILE_DICT = {
    'f_1': 1,
    'f_2': 3,
    'f_3': 5
}

LOGGER = get_task_logger(__name__)

# TODO: for db-stuff maybe have a separate consumer for the queue?

# x [preprocessing]
#   - 
#   - check db if task family is running
#   - update db to re-run / chain task depending
#   - raise error if db is running to prevent other tasks
@app.task()
def x_():
    LOGGER.info('get files: {}'.format(FILE_DICT.keys()))
    time.sleep(3)
    return list(FILE_DICT.keys())

# y [postprocessing]
#   - consolidate results from db
#   - update task state
@app.task()
def y_(x):
    LOGGER.info('input: {}'.format(x))
    time.sleep(3)
    return sum(x)

# d [download]
#   - update progress if possible
@app.task()
def d_(x):
    LOGGER.info('downloading file: {}'.format(x))
    time.sleep(7)
    return FILE_DICT[x]

# p [process]
#   - update progress if possible
@app.task()
def p_(x):
    LOGGER.info('file input: {}'.format(x))
    time.sleep(3)
    return x * 2

