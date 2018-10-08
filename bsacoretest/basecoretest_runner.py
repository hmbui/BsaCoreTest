from subprocess import Popen, PIPE

from bsacoretest.bsacoretest_logging import logging
logger = logging.getLogger(__name__)

from bsacoretest.utilities import convert_to_int, count_down_sleep_status


CAPUT = "$EPICS_BASE_RELEASE/bin/rhel6-x86_64/caput"
CAGET = "$EPICS_BASE_RELEASE/bin/rhel6-x86_64/caget"

PULSE_ID_HISTORY = "PULSEIDHST"
PULSE_ID_COUNT_HISTORY = "PULSEIDCNTHST"

MEASUREMENT_COUNT = "MEASCNT"
AVERAGE_COUNT = "AVGCNT"
CONTROL = "CTRL"

MAX_SLOT_COUNT = 20
MAX_INCLUSION_MASKS_COUNT = 5
MAX_EXCLUSION_MASKS_COUNT = 5


class BsaCoreTestRunner:
    def __init__(self, test_name, test_pv_name, base_pv_name, environment, edef_name):
        self._test_name = test_name
        self._test_pv_name = test_pv_name
        self._base_pv_name = base_pv_name
        self._edef_name = edef_name
        self._env = environment

        #self._reserve_bsa_slot()
        try:
            self._slot_number = str(self._detect_test_edef_slot_number())
        except RuntimeError as err:
            logger.error("Cannot find the slot number of EDEF '{0}'.".format(self._edef_name))
            raise err

    def _reserve_bsa_slot(self):
        """
        Reserve a slot for the BsaCore test
        """
        self._run_cmd(CAPUT + " IOC:IN20:EV01:EDEFNAME " + '"' + self._edef_name + '"')

    def _detect_test_edef_slot_number(self):
        """
        Detect the slot number assigned to the EDEF.

        This is done by checking for the name of each EDEF until a match is found.

        Raises: RuntimeError

        Returns : int
        -------
        The slot number assigned to the current BsaCore Test EDEF.
        """
        for slot_number in range(1, MAX_SLOT_COUNT + 1):
            edef_name = self._run_cmd(CAGET + " EDEF:SYS0:" + str(slot_number) + ":NAME")[0]
            if self._edef_name in edef_name:
                return slot_number
        raise RuntimeError

    def setup_masking(self, inclusion_masks, exclusion_masks):
        """
        Set up the masking for the EDEF.

        Parameters
        ----------
        inclusion_masks : list
            A list of inclusion masks to set for the EDEF's inclusion mask list.

        exclusion_masks : list
            A list of exclusion masks to set for the EDEF's exclusion mask list.

        Raises: ValueError

        """
        if len(inclusion_masks) != MAX_INCLUSION_MASKS_COUNT:
            raise ValueError("The inclusion mask list has {0} masks. That exceeds the expected maximum mask count of "
                             "{1}.".format(len(inclusion_masks), MAX_INCLUSION_MASKS_COUNT))

        if len(exclusion_masks) != MAX_EXCLUSION_MASKS_COUNT:
            raise ValueError("The exclusion mask list has {0} masks. That exceeds the expected maximum mask count of "
                             "{1}.".format(len(exclusion_masks), MAX_EXCLUSION_MASKS_COUNT))

        masking_prefix = self._base_pv_name + ":" + self._slot_number
        for i in range(MAX_INCLUSION_MASKS_COUNT):
            self._run_cmd(CAPUT + " " + masking_prefix + ":INCLUSION" + str(i + 1) + " " +
                          str(inclusion_masks[i]))

        for i in range(MAX_EXCLUSION_MASKS_COUNT):
            self._run_cmd(CAPUT + " " + masking_prefix + ":EXCLUSION" + str(i + 1) + " " + str(exclusion_masks[i]))

    def setup_measurement_count_and_average_samples(self, measurement_count, average_samples):
        """
        Set up the measurement count, i.e. how many times to provide a measurement, and the average samples, i.e.
        the number of measurements for each averaging.

        Parameters
        ----------
        measurement_count : int
            The number of measurements to perform
        average_samples : int
            How many numbers to use for each averaging of the measurements.
        """
        measurement_count_prefix = self._base_pv_name + ":" + self._slot_number + ":" + MEASUREMENT_COUNT
        self._run_cmd(CAPUT + " " + str(measurement_count_prefix) + " " + str(measurement_count))

        average_sample_prefix = self._base_pv_name + ":" + self._slot_number + ":" + AVERAGE_COUNT
        self._run_cmd(CAPUT + " " + str(average_sample_prefix) + " " + str(average_samples))

    def run_test(self, sleep_time_before_result=30):
        start_run_prefix = self._base_pv_name + ":" + self._slot_number + ":" + CONTROL
        stdout_data, stderr_data = self._run_cmd(CAPUT + " " + start_run_prefix + " 1")
        if stderr_data:
            raise RuntimeError

        count_down_sleep_status(sleep_time_before_result)

        obtain_result_prefix = self._test_pv_name + ":0:" + PULSE_ID_HISTORY + self._slot_number
        stdout_data, stderr_data = self._run_cmd(CAGET + " " + obtain_result_prefix)
        return stdout_data, stderr_data

    def run_test_case_1_special_tests(self):
        obtain_history_count_prefix = self._test_pv_name + ":1:" + PULSE_ID_COUNT_HISTORY + self._slot_number
        stdout_data, stderr_data = self._run_cmd(CAGET + " " + obtain_history_count_prefix)
        if stderr_data:
            raise RuntimeError

    def _run_cmd(self, cmd, log_level_debug=False):
        """
        Run a test command, log the command's stdout and stderr data, and then return these output data

        Parameters
        ----------
        cmd : str
            The test command to run
        log_level_debug : bool
            True if to force the log level to DEBUG; False if to keep the current log level
        """
        logger.info("## Running command: ##")
        logger.info(cmd)

        proc = Popen(cmd, env=self._env, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        return_code = proc.returncode

        logger.info("Return Code: {0}\n".format(return_code))

        if log_level_debug:
            logger.setLevel(logging.DEBUG)

        stdout_data = stdout.decode()
        if len(stdout_data):
            logger.debug("### stdout ###")
            logger.debug("{0}".format(stdout_data))

        stderr_data = stderr.decode()
        if len(stderr_data):
            logger.debug("### stderr ###")
            logger.debug("{0}".format(stderr.decode()))

        return stdout_data, stderr_data

    def verify_result(self, result, expected_interval=1):
        """
        Verify the result of a test. In most cases, the two verifications are

        1. The next value must be larger than the previous value
        2. The difference between the current value than its immediate previous value is a constant interval, to be
           provided by the caller.

        Parameters
        ----------
        result : list
            A list of returned data values to verify.

        expected_interval : int
            The constant difference between each returned data value to its immediate previous.

        Returns : bool
            True if the verifications are successful and the result is as expected; False otherwise
        """
        if len(result):
            try:
                prev_result = convert_to_int(result[0])
                for i in range(1, len(result)):
                    current_result = convert_to_int(result[i])

                    if current_result < prev_result:
                        logger.error("Test '{0}' FAILED at index {1}: current value {2} is less than the previous "
                                     "value {3}".format(self._test_name, i, current_result, prev_result))
                        return False
                    elif current_result - prev_result != expected_interval:
                        logger.error(
                            "Test '{0}' FAILED at index {1}: the interval between current value {2} and the previous "
                            "value {3} is less than the expected interval of {4}."
                            .format(self._test_name, i, current_result, prev_result, expected_interval))
                        return False
                    prev_result = current_result
                return True
            except Exception as err:
                logger.error("Test '{0}' fails result verifications. Exception: {1}".format(self._test_name, err))
                return False

        logger.error("Test '{0}' FAILED: Empty result.".format(self._test_name))
        return False
