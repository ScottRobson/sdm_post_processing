"""
Script to collect UE Feature support
"""
import logging
import json
import sys
import os
import re
from datetime import datetime
from pathlib import Path
from parsers.lassen_parser import (get_unique_log_files_capinfo_from_log_folder,
                                   get_signalling_log_from_sdm_file,
                                   get_instances_of_log_by_print_from_lines,
                                   get_list_of_enclosed_ie,
                                   get_ie_info_from_name_lassen)


UE_CAPINFO_JSON = Path('fta_selectors/UECapinfo_parameters.json')


# set up the get_capinfo logger
Path(os.getcwd() + '/logs/').mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s '
                           '%(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='./logs/tool_log.log',
                    filemode='w')
log = logging.getLogger('get_capinfo')



def get_combos_from_string(endc_combo_string):
  """Takes the 3GPP string form of a ENDC combo and returns a tuple of lists of the LTE and NR section of the combo

    Args:
      endc_combo_string (str): 3GPP formatted string of a ENDC combo

    Returns:
      lte_bands_in_combo (list), nr_bands_in_combo (list)
  """
  log.info('checking {}'.format(endc_combo_string))
  lte_string = re.search('_(.*)_', endc_combo_string)
  lte_string = lte_string.group(0)[1:-1]
  log.info(lte_string)
  lte_bands_in_combo = []
  if '-' not in lte_string:
    lte_bands_in_combo.append(lte_string)
  else:
    lte_bands_in_combo = lte_string.split('-')
  log.info('LTE bands in combo: {}'.format(lte_bands_in_combo))
  endc_string = endc_combo_string[endc_combo_string.rindex('_') + 1: ]
  log.info(endc_string)
  nr_bands_in_combo = []
  if '-' not in endc_string:
    nr_bands_in_combo.append(endc_string)
  else:
    nr_bands_in_combo = endc_string.split('-')
  log.info('NR bands in combo: {}'.format(nr_bands_in_combo))
  return lte_bands_in_combo, nr_bands_in_combo


def get_endc_combos_from_capinfo_lines(capinfo_lines):
  """Get a list of ENDC combos from a capinfo."""
  instances_of_cap_info_endc = get_instances_of_log_by_print_from_lines(capinfo_lines,
                                                                        "rf-ParametersMRDC")
  if not instances_of_cap_info_endc:
    print('The NW is not asking for eutra-nr UE capability info. Please get a log with the UE attaching to a 5G cell')
    exit()

  log.info('instances of frequency bands in log length: {}: {}'.format(str(len(instances_of_cap_info_endc)),
                                                                       instances_of_cap_info_endc))
  capinfo_lists = []
  for ota_log in instances_of_cap_info_endc:
    tmp = get_ie_info_from_name_lassen(ota_log, 'supportedBandCombinationList')
    if not tmp:
      print('There is no supportedBandCombinationList indicated in the log. Please get a new log with 5G attach')
      exit()
    # print(tmp[0])
    log.info(tmp[0])
    if tmp[0] not in capinfo_lists:
      capinfo_lists.append(tmp[0])

  log.info('capinfo logs: {}'.format(capinfo_lists))
  # Search for all the ENDC combos listed in all of the entries of UECapinfo and write them to 3GPP format
  endc_combo_strings  = []
  for capinfo in capinfo_lists:
    combo_lists = get_list_of_enclosed_ie(capinfo)
    log.info('Band strings: {}'.format(combo_lists))

    for endc_combo in combo_lists:
      current_line = 0
      endc_combo_string = 'DC_'

      for line in endc_combo:
        if 'bandEUTRA' in line:
          tmp = line.split()
          endc_combo_string = endc_combo_string + tmp[-1]
          tmp = endc_combo[current_line + 1].split()
          endc_combo_string = endc_combo_string + tmp[-2].capitalize() + '-'
        if 'bandNR' in line:
          if 'n' not in endc_combo_string:
            endc_combo_string = endc_combo_string[:-1] + '_'
          tmp = line.split()
          endc_combo_string = endc_combo_string + 'n' + tmp[-1]
          tmp = endc_combo[current_line + 1].split()
          endc_combo_string = endc_combo_string + tmp[-2].capitalize() + '-'
        current_line += 1

      endc_combo_string = endc_combo_string[ : -1]
      log.info(endc_combo_string)
      endc_combo_strings.append(endc_combo_string)
      # print(endc_combo_string)

  # We only need the set() of the endc combos, duplicates are not needed beyond here (for downlink CA)
  endc_combo_strings = list((set(endc_combo_strings)))
  log.info('EN-DC combos: {}'.format(endc_combo_strings))
  # print('EN-DC combos declared: {}'.format(endc_combo_strings))

  return endc_combo_strings


def get_single_line_feature_support_by_rat(rat):
  """Returns a list of the features in capinfo we can retrieve
     in one line from the UECapinfoS string (meaning we
     don't need any further logic to get the capinfo

    rat (str): the name of the RAT we are interrogating
      (i.e. eutran, eutran-nr geran-cs etc)
  """
  # Open the UECapinfo_parameters json and get the fixed feature names
  with open(UE_CAPINFO_JSON, 'r', encoding='utf-8') as json_file:
    capinfo_features = json.load(json_file)
    log.info('The capinfo json file: {}'.format(str(capinfo_features)))
    capinfo_features = capinfo_features['one_line_parameters'][rat]
  log.info('single line capinfo by RAT {}: {}'.format(str(rat), capinfo_features))
  return capinfo_features


def get_multiple_line_feature_support_by_rat(rat):
  """Returns a list of the features in capinfo that are nested

    rat (str): the name of the RAT we are interrogating
      (i.e. eutran, eutran-nr geran-cs etc)
  """
  # Open the UECapinfo_parameters.json file and get the list of nested IEs
  with open(UE_CAPINFO_JSON, 'r', encoding='utf-8') as json_file:
    capinfo_features = json.load(json_file)
    log.info('The capinfo json file: {}'.format(str(capinfo_features)))
    capinfo_features = capinfo_features['multiple_line_paremeters'][rat]
  log.info('multiple line capinfo by RAT {}: {}'.format(str(rat), capinfo_features))
  return capinfo_features


def get_as_feature_support_single_line_feature(feature_support_dict,
                                               capinfo_lines, rat):
  """Returns the AS features that are single line parameters.

    Args: 
      feature_support_dict (dict): feature support dict
      capinfo_lines (list): the capinfo log lines
      rat (string): the RAT we are selecting
  """
  capinfo_features = get_single_line_feature_support_by_rat(rat)
  if capinfo_features:
    for feature in capinfo_features:
      feature_found = False
      for line in capinfo_lines:
        if feature in line:
          feature_found = True
          line = line.rstrip()
          if line[-1] == ')':
            feature_support_dict[feature] = line.split()[-2]
          else:
            feature_support_dict[feature] = line.split()[-1]
          break
      if not feature_found:
        feature_support_dict[feature] = False
  log.info('AS feature supprot dict for RAT {}: {}'.format(str(rat), feature_support_dict))
  return feature_support_dict


def get_as_feature_support_multiple_line_feature(feature_support_dict,
                                                 capinfo_lines, rat):
  """Returns the AS features that are multiple line parameters.

    Args: 
      feature_support_dict (dict): feature support dict
      capinfo_lines (list): the capinfo log lines
      rat (string): the RAT we are selecting
  """
  capinfo_features = get_multiple_line_feature_support_by_rat(rat)
  if capinfo_features:
    for feature in capinfo_features:
      try:
        feature_ies = get_ie_info_from_name_lassen(capinfo_lines, feature)[0]
      except IndexError:
        break
      if len(feature_ies) < 2:
        feature_support_dict[feature] = False
        break
      for sub_feature in feature_ies:
        sub_feature = sub_feature.rstrip()
        if sub_feature[-1] == ')':
          feature_support_dict[feature] = {sub_feature.split()[0]: sub_feature.split()[-2]}
        else:
          feature_support_dict[feature] = {sub_feature.split()[0]: sub_feature.split()[-1]}
  log.info('AS feature support dict multiple line for RAT {}: {}'.format(str(rat), feature_support_dict))
  return feature_support_dict


def get_eutran_as_feature_support(eutra_capinfo_lines):
  """get a dictionary of EUTRAN AS feature support from list of strings
     of the UECapabilityInfo RRC OTA Message

    eutra_capinfo_lines (list): A list of strings taken from the
      UECapinfo log of the eutran rat type
  """
  eutra_feature_support_dict = get_as_feature_support_single_line_feature({}, eutra_capinfo_lines, 'eutra')
  eutra_feature_support_dict = get_as_feature_support_multiple_line_feature(eutra_feature_support_dict,
                                                                            eutra_capinfo_lines, 'eutra')
  eutra_feature_support_dict = get_eutra_bands_supported_by_ue(eutra_feature_support_dict,
                                                               eutra_capinfo_lines)

  return eutra_feature_support_dict


def get_NW_from_log(parsed_log_lines):
  """."""
  # MCC is the Mobile Country Code and MNC is the Mobile Network Code
  mcc = None
  mnc = None
  for line in parsed_log_lines:
    if not mcc:
      if 'Mobile Country Code' in line:
        mcc = line.split()[-1]
        mcc = mcc[1:-1]
    if not mnc:
      if 'Mobile Network Code' in line:
        mnc = line.split()[-1]
        mnc = mnc[1:-1]
    if mcc and mnc:
      break
  log.info('log does not contain 2G MCC or MNC')
  if not mcc:
    for line in parsed_log_lines:
      if 'ims.mnc' in line:
        log.info('line contains ims.mnc: {}'.format(line))
        tmp = line.split('.')
        mcc = tmp[2][3:]
        mnc = tmp[1][3:]
        break

  log.debug('The log has MCC: {}, MNC: {}'.format(mcc, mnc))
  print('The log has MCC: {}, MNC: {}'.format(mcc, mnc))
  return mcc, mnc


def get_eutra_bands_supported_by_ue(return_dict, eutra_capinfo_lines):
  """Gets the LTE bands supported by the UE and NW."""
  lte_bands = []
  band_list = get_ie_info_from_name_lassen(eutra_capinfo_lines,
                                           'supportedBandListEUTRA:')
  log.info('lte_band_list: {}'.format(band_list))
  #band_list = get_list_of_enclosed_ie(band_list)
  band_list = band_list[0]

  for line in band_list:
    if 'bandEUTRA' in line:
      lte_bands.append('B' + line.split()[-1])
  log.info('LTE bands: {}'.format(lte_bands))
  return_dict['LTE bands'] = lte_bands

  return return_dict


def check_for_issues(ue_capinfo):
  """Does a check of the UE Capinfo to check if there are any issues."""
  pass


def get_utran_as_feature_support(utra_capinfo_lines):
  """get a dictionary of UTRAN AS feature support from list of strings
     of the UECapabilityInfo RRC OTA Message

    utra_capinfo_lines (list): A list of strings taken from the
      UECapinfo log of the eutran rat type
  """
  utra_feature_support_dict = get_as_feature_support_single_line_feature({}, utra_capinfo_lines, 'utra')
  utra_feature_support_dict = get_as_feature_support_multiple_line_feature(utra_feature_support_dict,
                                                                           utra_capinfo_lines, 'utra')

  return utra_feature_support_dict


def get_ue_capinfo(parsed_log):
  """Gets the UE Capinfo of one parsed log file.
  Args:
      parsed_log (list): A list of strings of a post-processed modem log
  """
  instances_of_capinfo_requests = get_instances_of_log_by_print_from_lines(parsed_log,
                                                                'ue-CapabilityRequest')
  if not instances_of_capinfo_requests:
    print('The log does not have any instances of ue-CapabilityRequest.'
          'Try again with a log containing a fresh attach.')
    sys.exit()
  log.info('capinfo request: {}'.format(instances_of_capinfo_requests))

  capinfo_rats_requested = []
  lte_ca_bands = []
  lte_mrdc_bands = []
  nr_mrdc_bands = []
  # Get the network requested capinfo
  for ota_log in instances_of_capinfo_requests:
    for line in ota_log:
      if 'RAT-Type' in line:
        if line.split()[1] not in capinfo_rats_requested:
          capinfo_rats_requested.append(line.split()[1])
      if 'FreqBandIndicator' in line:
        if int(line.split()[-1]) not in lte_ca_bands:
          lte_ca_bands.append(int(line.split()[-1]))
      if 'bandEUTRA' in line:
        if int(line.split()[-1]) not in lte_mrdc_bands:
          lte_mrdc_bands.append(int(line.split()[-1]))
      if 'bandNR' in line:
        if int(line.split()[-1]) not in nr_mrdc_bands:
          nr_mrdc_bands.append(int(line.split()[-1]))

  print('NW is requesitng these RATs capinfo in the log: {}'.format(capinfo_rats_requested))
  print('NW is requesting these LTE bands: {}'.format(lte_ca_bands))
  print('NW is requesting these LTE MRDC bands: {}'.format(lte_mrdc_bands))
  print('NW is requesting these NR MRDC bands: {}'.format(nr_mrdc_bands))

  # Get the log metadata to give the capinfo some context
  ue_capinfo = {}
  ue_capinfo['nw_request'] = capinfo_rats_requested
  # ue_capinfo['nw_request']['LTE']['Bands'] = lte_ca_bands
  ue_capinfo['nw_request_lte_ca_bands'] = lte_ca_bands
  ue_capinfo['nw_request_lte_mrdc_bands'] = lte_mrdc_bands
  ue_capinfo['nw_request_nr_mrdc_bands'] = nr_mrdc_bands

  log_capinfo_responses = get_instances_of_log_by_print_from_lines(parsed_log,
                                                        'ueCapabilityInformation')
  # print(len(log_capinfo_responses))
  # print(log_capinfo_responses[0][0:10])
  capinfo_responses = []

  for ue_capinfo_response in log_capinfo_responses:
    log.info('is a UE Capinfo: {}'.format(ue_capinfo_response[9]))
    if not 'RAT-ContainerList' in ue_capinfo_response:
      log.info('not a valid capinfo... {}'.format(ue_capinfo_response))
    # print('ue-CapabilityRAT-ContainerList is present')
    tmp = get_ie_info_from_name_lassen(ue_capinfo_response,
                                      'ue-CapabilityRAT-ContainerList')
    log.info('tmp: {}'.format(tmp))
    try:
      tmp = get_list_of_enclosed_ie(tmp[0])
      log.info(tmp)
    except IndexError:
      log.info('meh something failed :( ')
      continue
    for ota in tmp:
      try:
        if ota[2:] not in capinfo_responses:
          capinfo_responses.append(ota[2:])
      except IndexError:
        log.info('there was an error in the capinfo_responses tracking')
  log.info(capinfo_responses)
  if capinfo_responses:
    for rat_capinfo_strings in capinfo_responses:
      if '(0)' in rat_capinfo_strings[0]:
        ue_capinfo['eutra'] = get_eutran_as_feature_support(rat_capinfo_strings)
      if '(1)' in rat_capinfo_strings[0]:
        ue_capinfo['utra'] = get_utran_as_feature_support(rat_capinfo_strings)

  return ue_capinfo


def main():
  """Main function to get the capinfo"""

  task = input('This script can get the UE Capability and feature support '
               'from an existing log or it can collect new logs automatically'
               ' and gather the data from that.\n'
               'Select from the following options:\n'
               '1 - Gather UE Capability from existing log\n'
               '2 - Gather UE Capability from USB connected device(s): ')

  if task == '1':
    log_folder = input('What is the directory of the folder?\n')
    log_files = get_unique_log_files_capinfo_from_log_folder(log_folder)
    log.info('log files: {}'.format(log_files))
    for file in log_files:
      potential_issues_to_investigate = []
      parsed_log = get_signalling_log_from_sdm_file(file)
      file_mcc, file_mnc = get_NW_from_log(parsed_log)
      ue_capinfo = get_ue_capinfo(parsed_log)
      ue_capinfo['mcc'] = file_mcc
      ue_capinfo['mnc'] = file_mnc
      ue_capinfo['eutra']['EN-DC Combos'] = sorted(get_endc_combos_from_capinfo_lines(parsed_log))
      print(ue_capinfo)
      output_file_name = '/UECapinfo_MCC-{}_MNC-{}_{}.json'.format(ue_capinfo['mcc'],
                                                                   ue_capinfo['mnc'],
                                                                   datetime.today().strftime('%Y-%m-%d'))
      with open(Path(log_folder + output_file_name), 'w', encoding='utf-8') as output_json:
        json.dump(ue_capinfo, output_json)


  elif task == '2':
    print('Just Kidding, this part is not ready yet!')


if __name__ == "__main__":
  main()
