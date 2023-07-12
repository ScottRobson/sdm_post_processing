"""Get KIPs form sdm log file."""

import re
import os
import csv
import logging
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from parsers.lassen_parser import LassenParser, get_signalling_log_from_sdm_file


# set up the get_log_metrics logger
Path(os.getcwd() + '/logs/').mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='./logs/tool_log.log',
                    filemode='w')
log = logging.getLogger('get_log_metrics')


PARSED_LOG_TEMPORARY_STORAGE = Path(os.getcwd() + '/current_parsed_logs')

def validate_log_file(log_file):
    """Validate that the input is a valid .sdm file"""
    if not 'sdm' in log_file.suffix:
        raise FileNotFoundError('The inputted file is not a .sdm file')

    if not Path(log_file).is_file():
        raise FileNotFoundError('The inputted path is not a file')


def get_log_metadata(infoexport, parsed_signalling_log, log_file):
    """Take in a log file and output a dict with the log metadata"""
    log_metadata = {}
    log_metadata['log_directory'] = log_file.parent
    log_metadata['log_name'] = log_file.name
    for line in infoexport:
        line = line.decode('ascii')
        if 'FW Version' in line:
            tmp = line.split()[-1]
            tmp = tmp.split(';')
            log_metadata['radio_firmware'] = tmp[0]
            log_metadata['chipset_sub-version'] = tmp[0].split('-')[0]
            log_metadata['carrier_config'] = tmp[3]
            break
    for line in infoexport:
        line = line.decode('ascii')
        if 'Build Date' in line:
            tmp = line.split()[-1]
            tmp_date = datetime.strptime(tmp[0:9], '%Y-%m-%d')
            log_metadata['sw_build_date'] = tmp_date
            break
    for line in infoexport:
        line = line.decode('ascii')
        if 'Logging Time' in line:
            tmp = line.split()
            log_metadata['log_start_time'] = datetime.strptime(tmp[-5] + ' ' + tmp[-4] + '000', '%Y-%m-%d %H:%M:%S.%f')
            log_metadata['log_end_time'] = datetime.strptime(tmp[-2] + ' ' + tmp[-1] + '000', '%Y-%m-%d %H:%M:%S.%f')

    # get the camped MCC and MNC
    for line in parsed_signalling_log:
        if 'Mobile Country Code (MCC)' in line:
            log_metadata['camped_mcc'] = line.split()[-1][1:-1]
            log_metadata['camped_country'] = line.split(':')[-1]
        if 'Mobile Network Code (MNC)' in line:
            log_metadata['camped_mnc'] = line.split()[-1][1:-1]
            log_metadata['network_name'] = line.split(':')[-1]
            break
    # get the 5G enabled or disabled
    endc_enabled = True
    for line in parsed_signalling_log:
        if 'estrictDCNR' in line:
            endc_enabled = False
    log_metadata['5G_provisioned'] = str(endc_enabled)
    return log_metadata


def main():
    # First delete any existing parsed log file
    for file in PARSED_LOG_TEMPORARY_STORAGE.iterdir():
        os.remove(file)

    log_file = input('No script input. Please copy and paste the path of a log file to generate the KPIs?\n')
    log_file = Path(log_file)
    validate_log_file(log_file)

    lassen_parser = LassenParser()
    infoexport = lassen_parser.get_infoexport(log_file)
    infoexport = infoexport.stdout.splitlines()

    parsed_signaling_log = get_signalling_log_from_sdm_file(log_file, False,
                                                            str(PARSED_LOG_TEMPORARY_STORAGE) + '/signaling.txt')

    log_metadata = get_log_metadata(infoexport, parsed_signaling_log, log_file)
    print(log_metadata)




if __name__ == '__main__':
    main()
