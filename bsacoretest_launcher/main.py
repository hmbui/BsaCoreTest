import os
import traceback
import argparse

import bsacoretest
from bsacoretest.basecoretest_runner import BsaCoreTestRunner

from bsacoretest.bsacoretest_logging import logging
logger = logging.getLogger(__name__)


def _parse_arguments():
    """
    Parse the command arguments.

    Returns
    -------
    The command arguments as a dictionary : dict
    """
    parser = argparse.ArgumentParser(description="Testing BsaCore")

    parser.add_argument("test_pv_name", help="The name of the PV to test data acquisition")
    parser.add_argument("test_edef_name", help="The name of the EDEF to reserve for testing")

    parser.add_argument(
        '--log_level',
        help='Configure level of log display',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO'
    )

    parser.add_argument("--version", action="version", version="BsaCore Test {version}".
                        format(version=bsacoretest.__version__))

    args, extra_args = parser.parse_known_args()
    return args, extra_args


def _run_test_case_0(test_pv_name, base_pv_name, environment, edef_name):
    bsacore_test_runner = BsaCoreTestRunner("Test Case 0", test_pv_name, base_pv_name, environment, edef_name)
    # Test Case 0: 120Hz source, 120Hz acquisition with average 3 samples
    bsacore_test_runner.setup_masking(
        [0x0, 0x0, 0x0, 0x0, 0x0],
        [0x0, 0x0, 0x0, 0x0, 0x36]
    )

    bsacore_test_runner.setup_measurement_count_and_average_samples(2800, 3)
    try:
        stdout_data, stderr_data = bsacore_test_runner.run_test(sleep_time_before_result=90)
    except RuntimeError as err:
        logger.error("Test run error. Exception: {}".format(err))
    else:
        result = stdout_data.split(' ')
        if bsacore_test_runner.verify_result(result[2:], expected_interval=9):
            logger.info("Test Case 0 SUCCESSFUL.")
        else:
            logger.error("Test Case 0 FAILED.")


def _run_test_case_1(test_pv_name, base_pv_name, environment, edef_name):
    bsacore_test_runner = BsaCoreTestRunner("Test Case 1", test_pv_name, base_pv_name, environment, edef_name)
    # Test Case 0: 120Hz source, 120Hz acquisition with average 3 samples
    bsacore_test_runner.setup_masking(
        [0x0, 0x0, 0x0, 0x0, 0x0],
        [0x0, 0x0, 0x0, 0x0, 0x36]
    )

    bsacore_test_runner.setup_measurement_count_and_average_samples(2800, 1)
    try:
        stdout_data, stderr_data = bsacore_test_runner.run_test(sleep_time_before_result=30)
    except RuntimeError as err:
        logger.error("Test run error. Exception: {}".format(err))
    else:
        result = stdout_data.split(' ')
        if bsacore_test_runner.verify_result(result[2:], expected_interval=3):
            bsacore_test_runner.run_test_case_1_special_tests()
            logger.info("Test Case 0 SUCCESSFUL.")
        else:
            logger.error("Test Case 0 FAILED.")


def main():
    args, extra_args = _parse_arguments()
    if args.log_level:
        logger.setLevel(args.log_level)

    test_pv_name = args.test_pv_name
    edef_name = args.test_edef_name
    base_pv_name = "EDEF:SYS0"

    environment = os.environ.copy()

    #_run_test_case_0(test_pv_name, base_pv_name, environment, edef_name)
    _run_test_case_1(test_pv_name, base_pv_name, environment, edef_name)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        logger.error("\nUnexpected exception while running the test. Exception type: {0}. Exception: {1}"
                     .format(type(error), error))
        traceback.print_exc()
        for h in logger.handlers:
            h.flush()
