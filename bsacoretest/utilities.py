import sys
import time

from bsacoretest.bsacoretest_logging import logging
logger = logging.getLogger(__name__)


def convert_to_int(value):
    try:
        int_value = int(value)
        return int_value
    except Exception as err:
        logger.error("Cannot convert value '{0}' to int. The exception is '{1}".format(value, err))
        raise err


def count_down_sleep_status(sleep_secs):
    """
    Display a countdown of the remaining sleep seconds.

    Parameters
    ----------
    sleep_secs : int
        The number of seconds for sleep.
    """
    for i in range(sleep_secs, 0, -1):
        sys.stdout.write("\rSleeping for {0} seconds...".format(i))
        sys.stdout.flush()
        time.sleep(1)
