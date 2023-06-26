"""
A script to parse and use parsed .sdm log files
"""
from pathlib import Path
# from constructors.log_construct import SignalingLog
from datetime import datetime
from sys import platform
import subprocess
import logging
import csv
import os
import datetime

# set up the compare_ca_combos logger
Path(os.getcwd() + '/logs/').mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='./logs/tool_log.log',
                    filemode='w')
log = logging.getLogger('lassen_parser')


DM_CONSOLE_LOCATION = Path('/Applications/Uni-DM.app/Contents/MacOS/') # Add the location of your ShannonDM
MODEM_BIN_LOCATION = Path('/Users/scottrobson/Downloads/modem.bin')
FILTER = Path(Path.cwd() / 'parsers/ENDC.met')


class LassenParser:
  """
  A class to handle debugging Lassen logs.

  To use:
  >>>lp = LassenParser(Path('directory containing the DMConsole.exe'))
  >>>lp.parse_log_signalling_txt(Path('path to log file'), concatenate_logs(True/False),
                              output(Path('output path'))
  >>>lp.parse_log_signalling_csv(Path('path to log file'), concatenate_logs(True/False),
                              output(Path('output path'))
  """
  def __init__(self, dm_console_location=DM_CONSOLE_LOCATION):
    """
    Args:
      dm_console_location (Path): The location of the folder containing the DMConsole.exe
    """
    if platform == "win32":
      log.info(platform)
      try:
        dm_console_location = Path(str(dm_console_location) + '\\DMConsole.exe')
        output = subprocess.run([dm_console_location, 'help'], capture_output=True)
        # print(output)
      except FileNotFoundError:
        raise FileNotFoundError('DMConsole.exe file not found!')
    elif platform == "darwin":
      dm_console_location = '/Applications/Uni-DM.app/Contents/MacOS//./DMConsole'
      output = subprocess.run([dm_console_location, 'help'], capture_output=True)
      log.info(str(output))

    self.dm_console_location = dm_console_location

  def modify_file_for_mac_os_unidm(self, log_path):
    """Uni-DM on MacOS cannot handle the brackets in a log file, this removes them."""
    if platform != 'win32':
      log.info('laptop is mac, need to rename the files.')
      for file in Path(log_path).parent.iterdir():
        log.info('checking file: {}'.format(str(file)))
        if 'sdm' in file.suffix:
          num_digits = 4 - (str(file).find(')') - str(file).find('('))
          modify_string = '_'
          for _ in range(num_digits):
            modify_string = modify_string + '0'
          log.info(modify_string)
          renamed_file_name = str(file).replace('(', modify_string)
          renamed_file_name = renamed_file_name.replace(')', '')
          os.rename(file, renamed_file_name)
          log.info('file renamed to: {}'.format(renamed_file_name))
    return Path(renamed_file_name)

  def parse_log_signalling_txt_pixellogger(self, log_path):
    """Parse the pixellogger logs."""
    # we need to remove any of the spaces in the log files
    log_path = rename_folder_before_parsing(log_path)
    if Path(log_path / 'pixellogger_parsed.txt').is_file():
      os.remove(Path(log_path / 'pixellogger_parsed.txt'))
    output_file = Path(log_path / 'pixellogger_parsed.txt')
    log_files = []
    for file in Path(log_path).iterdir():
      if 'sdm' in file.suffix:
        if 'sbuff_power' not in file.name:
          log_files.append(file)

    with open(output_file, "w") as output_text_file:
      output_text_file.write('Parsed log file of {}\n\n'.format(str(log_path)))

    for file in sorted(log_files):
      command = str(self.dm_console_location) + ' signalexport ' + str(file)
      print('Parsing the logs. Running this command: {}'.format(command))
      subprocess.run(command.split(), capture_output=True)

      exported_log = Path(str(file)[:-3] + 'txt')
      with open(output_file, 'a') as output_text_file:
        with open(exported_log, 'r') as tmp_output:
          for line in tmp_output.readlines():
            output_text_file.write(line)

      os.remove(str(file)[:-3] + 'txt')
    return output_file

  def parse_log_metrics_txt_maclinux(self, log_path, concatenate_logs=True, output=True, overwrite=True):
    """."""
    for file in Path(log_path).parent.iterdir():
      if 'directory_metrics' in file.name:
        if overwrite:
          with open(file, 'w', encoding='utf-8') as output_file:
            output_file.write('test')
          break
        else:
          return file
    
    self.modify_file_for_mac_os_unidm(log_path)
    log_files = []
    for file in Path(log_path).parent.iterdir():
      if 'sdm' in file.suffix:
        if 'sbuff_power_on_log' not in str(file.name):
          log_files.append(file)
    
    output_file = str(str(Path(file.parent) / 'directory_metrics.txt'))
    with open(output_file, "w") as output_text_file:
      output_text_file.write('Parsed log file of {}\n\n'.format(str(log_path)))

    for file in sorted(log_files):
      command = str(self.dm_console_location) + ' metricexport -f ' + str(FILTER) + ' ' + str(file)
      print('Parsing the logs. Running this command: {}'.format(command))
      subprocess.run(command.split(), capture_output=True)

      exported_log = Path(str(file)[:-3] + 'txt')
      with open(output_file, 'a') as output_text_file:
        try:
          with open(exported_log, 'r') as tmp_output:
            for line in tmp_output.readlines():
              output_text_file.write(line)
        except FileNotFoundError:
          print('File not found')
          continue
      
      os.remove(str(file)[:-3] + 'txt')

      if not concatenate_logs:
        break
    
    return output_file

  def parse_log_signalling_txt_maclinux(self, log_path, concatenate_logs=True, output=True):
    """Parse log file function for mac/linux."""
    for file in Path(log_path).parent.iterdir():
      if 'directory_parsed' in file.name:
        return file
    self.modify_file_for_mac_os_unidm(log_path)
    log_files = []
    for file in Path(log_path).parent.iterdir():
      if 'sdm' in file.suffix:
        if 'sbuff_power_on_log' not in str(file.name):
          log_files.append(file)

    output_file = str(str(Path(file.parent) / 'directory_parsed.txt'))
    # print(output_file)
    with open(output_file, "w") as output_text_file:
      output_text_file.write('Parsed log file of {}\n\n'.format(str(log_path)))

    for file in sorted(log_files):
      command = str(self.dm_console_location) + ' signalexport ' + str(file)
      print('Parsing the logs. Running this command: {}'.format(command))
      subprocess.run(command.split(), capture_output=True)
      
      exported_log = Path(str(file)[:-3] + 'txt')
      with open(output_file, 'a') as output_text_file:
        with open(exported_log, 'r') as tmp_output:
          for line in tmp_output.readlines():
            output_text_file.write(line)

      os.remove(str(file)[:-3] + 'txt')

      if not concatenate_logs:
        break
    
    return output_file

  def parse_log_signalling_txt(self, log_path, concatenate_logs=True, output=None):
    """
    Args:
      log_path (Path): A string of the path to the log file *.sdm (including .sdm)
      concatenate_logs (bool): If True the method will concatenate the logs, if False it will only parse the
        log file from log_path
      filter_flt (Path): A *.flt to filter signaling logs. Default to the SIGNALLING_FILTER
      output (Path): Output path. If it is None the location of the source log
    """
    # we need to remove any of the spaces in the log files
    log_path = rename_folder_before_parsing(log_path)

    if platform != 'win32':
      return self.parse_log_signalling_txt_maclinux(log_path, concatenate_logs, output)

    else:
      if not log_path:
        raise FileNotFoundError('Invalid log path entered. Try again with a valid directory with a .sdm file.')
      command = str(self.dm_console_location) + ' signalexport'

      if not concatenate_logs:
        command = command + ' -c'

      '''
      if filter_flt:
        command = command + ' -f ' + str(filter_flt)
      '''

      if output:
        command = command + ' o ' + str(output)

      command = command + ' ' + str(log_path)
      print('This takes some time! Running the below command\n' + command)

      # send the needed command line to the CLI
      command = subprocess.run(command.split(), capture_output=True)

      if output:
        exported_log_path = Path(str(output) + '/' + str(log_path.name).replace('sdm', 'txt'))
      else:
        exported_log_path = Path(str(str(log_path)[:-3] + 'txt'))

      print('generated log: ' + str(exported_log_path))
      return exported_log_path

  def parse_log_signalling_csv(self, log_folder, concatenate_logs=True, output=None):
    """
    Args:
      log_path (Path): A string of the path to the log file *.sdm (including .sdm)
      concatenate_logs (bool): If True the method will concatenate the logs, if False it will only parse the
        log file from log_path
      filter_flt (Path): A *.flt to filter signaling logs. Default to the SIGNALLING_FILTER
      output (Path): Output path. If it is None the location of the source log

    Returns:
      exported_log_path (Path): the path of the generated parsed log.
    """
    # we need to remove any of the spaces in the log files
    log_folder = rename_folder_before_parsing(log_folder)
    log_folder = self.modify_file_for_mac_os_unidm(log_folder)
    command = str(self.dm_console_location) + ' signalexport -csv'

    if not concatenate_logs:
      command = command + ' -c'

    '''
    if filter_flt:
      command = command + ' -f ' + str(filter_flt)
    '''

    if output:
      command = command + ' o ' + str(output)

    command = command + ' ' + str(Path(log_folder))
    print('\nThis takes some time! Running the below command\n' + command)

    # send the needed command line to the CLI
    command = subprocess.run(command.split(), capture_output=True)

    if output:
      exported_log_path = Path(str(output) + '\\' + str(log_folder.name).replace('sdm', 'csv'))
    else:
      exported_log_path = Path(str(str(log_folder)[:-3] + 'csv'))

    log.info('generated log: ' + str(exported_log_path))
    return exported_log_path

  def get_metrics_export(self, log_path, concatenate_logs=True, output=None):
    """Gets the metrics export of a modem log."""

    # we need to remove any of the spaces in the log files
    log_path = rename_folder_before_parsing(log_path)

    if platform != 'win32':
      return 


  def check_for_rlf_txt(self, parsed_log_txt):
    pass

  def check_for_rlf(self, parsed_log):
    """.
    Args:
       parsed_log (Path): Path of a parsed signaling log in *.csv
    """
    try:
      with open(str(parsed_log), 'r') as csvlogfile:
        csvlog = []
        for line in csvlogfile:
          csvlog.append(line)
    except FileNotFoundError:
      raise FileNotFoundError('Parsed log file not found!')

    current_line = 0
    rlf_found = False
    for line in csvlog:
      if 'rlf-Cause' in line:
        rlf_found = True
        print('Log contains a RLF in line {}: "{}"'.format(current_line, line.strip()))
        if 'other-failure' in line:
          print('The log contains a "other-failure" Re-establishment request at line {}'.format(str(current_line)))
        if 'randomAccessProblem' in line:
          print('The log contains a "randomAccessProblem" Re-establishment request at line {}'.format(str(current_line)))
        if 't310-Expire' in line:
          print('The log contains a "t310-Expiry" Re-establishment request at line {}'.format(str(current_line)))
        if 'rlc-MaxNumRetx' in line:
          print('The log contains a "rlc-MaxNumRetx" Re-establishment request at line {}'.format(str(current_line)))
      # Check for UE sending rlf info available to the NW
      if 'rlf-InfoAvailable-r10: true' in line:
        rlf_found = True
        print('The log contains a RLF info to the network (rlf-InfoAvailable-r10: true) on or around message {}'.format(str(current_line)))
      # Check for UE sending rlf info available to the NW
      if 'rlf-InfoAvailable-r11: true' in line:
        rlf_found = True
        print('The log contains a RLF info to the network (rlf-InfoAvailable-r11: true) on or around message {}'.format(str(current_line)))
      if 'scgFailureInformationNR' in line:
        rlf_found = True
        print('The log contains a RLF info to the network (scgFailureInformationNR) on or around message {}'.format(str(current_line)))
      current_line += 1
      if 'rlf-Report-r9' in line:
        rlf_found = True
        print('The log contains a RLF info to the network (rlf-Report-r9) on or around message {}'.format(str(current_line)))
    return rlf_found

  def check_for_print(self, parsed_log, search_term):
    """.
    Args:
      parsed_log (Path): Path of a parsed signaling log in *.csv
      search_term (str): a string to search the log for
    Returns:

    """
    try:
      with open(str(parsed_log), 'r') as csvlogfile:
        csvlog = []
        for line in csvlogfile:
          csvlog.append(line)
    except FileNotFoundError:
      raise FileNotFoundError('Parsed log file not found!')

    log.info('Scanning log {} for "{}"'.format(str(parsed_log), search_term))

    current_line = 0
    instances_of_log = []
    for row in csvlog:
      if search_term in row:
        print('Found {} in line {}'.format(search_term, current_line))

      current_line += 1


'''
def get_individual_signaling_log_object_csv_lassen(parsed_csv):
  """."""
  header = parsed_csv[0].split()
  time = header[0] + ' ' + header[1] + ' ' + header[2] + ' ' + header[3]
  print(time)
  time = datetime.strptime(time, '%Y %b %d %H:%M:%S.%f')
  tech = header[6]
  layer = header[7]
  log_subtype = header[-1]
  body = parsed_csv[1:]
  direction = None
  channel = None

  return SignalingLog(time, tech, layer, log_subtype, direction, channel, body)
'''


def get_spaces_before_ie_name(line):
  """."""
  spaces_before_ie_start = 0
  for char in line:
    if char != ' ':
      # print('spaces before IE name: {}'.format(spaces_before_ie_start))
      return spaces_before_ie_start

    spaces_before_ie_start += 1
  return spaces_before_ie_start


def get_list_of_enclosed_ie(ota_lines):
  """Takes string list and returns an array of the next sub IEs (such as a list of strings lists for each CA combo)"""
  """
  ie_data = []
  print(get_spaces_before_ie_name(ota_lines[1]))
  indent_of_ie_list = get_spaces_before_ie_name(ota_lines[1])
  start_line = 1
  current_line = 1
  for line in ota_lines[2 : ]:
    current_line += 1
    print(get_spaces_before_ie_name(line))
    current_line_indent = get_spaces_before_ie_name(line)
    print('Current line: {} Current line indent {}'.format(current_line, current_line_indent))

    if current_line_indent == indent_of_ie_list:
      return ota_lines[start_line : current_line]
  """
  def get_num_spaces(line):
    num_spaces = 0
    for char in line:
      if char != ' ':
        return num_spaces
      num_spaces += 1
    return len(line)

  ie_list = []
  log.debug('ota_lines: {}'.format(ota_lines))
  # The indent we are searching for is the indent after the name of the IE, so we find it here
  indent_of_ie_list = get_num_spaces(ota_lines[1])
  start_line = 1
  current_line = 2
  end_line = 2
  for line in ota_lines[2 : ]:
    if get_num_spaces(line) == indent_of_ie_list:
      # print('Indent_of_search: {}, Spaces in line: {}, Line {}'.format(str(get_num_spaces(line)), str(indent_of_ie_list), line))
      end_line = current_line
      ie_list.append(ota_lines[start_line : end_line])
      start_line = end_line
    current_line += 1

  # now we have all but the last entry (or if there is only 1, the first
  ie_list.append(ota_lines[start_line : ])

  return ie_list


def get_line_number_of_next_indent(ie_list, indent):
  """
    Args:
      ie_list (list): List of strings that make up an IE of a OTA log
      indent (int): the number of spaces we are looking for
  """
  current_line = 1
  for line in ie_list[1 : ]:
    current_line_indent = 0
    for char in line:
      if char != ' ':
        break
      current_line_indent += 1

    log.info('current line indent: {}. Line: {}'.format(str(current_line_indent), line))
    if current_line_indent == indent:
      return  current_line - 1
    current_line += 1

  # if we get here then the there was no line with the required indent,
  # so we return the last line of the ie_list
  return len(ie_list)


def get_ie_info_from_name_lassen(ota_log, ie_name):
  """Takes a list of lines from a Lassen modem log and returns the lines that are the information element data.
  If there is more than one entry it returns a list of the string lines. Therefore in both cases we need to return
  a list even if it is a list of 1 entry

  Args:
    ota_log (list): list of strings (lines) from an OTA log
    ie_name (str): The search term

  Returns:
    ie_data (list): A list of the strings contained by the information element
  """
  log.info('ota-log: {}, ie_name: {}'.format(ota_log, ie_name))
  if ie_name in ota_log:
    print('yay the search term is in the log: {}'.format(ie_name))
  current_line = 0
  lines_of_presence_of_ie = []
  ie_data = []
  for line in ota_log:
    if ie_name in line:
      log.info('Line {}: {}'.format(current_line,line))
      lines_of_presence_of_ie.append(current_line)
      log.info('the search term is present in {}, Line: {}'.format(line, str(current_line)))
    current_line += 1

  # For each iteration of the search term get the line number with the next iteration that is
  for start_line in lines_of_presence_of_ie:
    num_spaces_in_ie = get_spaces_before_ie_name(ota_log[start_line])
    # Get the next line where the IE has the same or fewer number of spaces before it is named
    end_line = start_line + 1
    for line in ota_log[start_line + 1: ]:
      if get_spaces_before_ie_name(line) <= num_spaces_in_ie:
        break
      end_line += 1

    ie_data.append(ota_log[start_line : end_line])

  return ie_data

def fix_brackets_for_mac(log_directory):
  """."""


def get_signaling_log_list_from_csv_lassen(log_path):
  """."""
  pass


def get_signalling_log_from_sdm_file(log_file):
  """
  Input a Path object of a unique sdm file. Output a .txt file of the capinfo.

  Args:
      Path: log_file: A Path objexct of the file to parse
  """
  lassen_parser = LassenParser()
  if 'sbuff_' in log_file.name:
    log.info('Log is pixellogger')
    parsed_log = lassen_parser.parse_log_signalling_txt_pixellogger(log_file.parent)
  else:
    parsed_log = lassen_parser.parse_log_signalling_txt(log_file)

  log_lines = []
  with open(parsed_log, 'r', encoding='utf-8') as parsed_log_file:
    for line in parsed_log_file:
      log_lines.append(line)

  return log_lines


def get_metrics_log_from_sdm_file(log_file, overwrite):
  """."""
  lassen_parser = LassenParser()
  if 'sbuff_' in log_file.name:
    log.info('Log is pixellogger')
  else:
    log.info('Logs exist, and overwriting logs is: {}'.format(str(overwrite)))
    parsed_log = lassen_parser.parse_log_metrics_txt_maclinux(log_file, overwrite=overwrite)
  
  log_lines = []
  with open(parsed_log, 'r', encoding='utf-8') as parsed_log_file:
    for line in parsed_log_file:
      log_lines.append(line)

  return log_lines


def get_unique_log_files_capinfo_from_log_folder(log_folder):
  """Gets the capinfo from a directory."""
  def verify_valid_folder(log_folder):
    log_folder = Path(log_folder)
    if not log_folder.is_dir:
      return False
    folder_contains_sdm_file = False
    for file in log_folder.iterdir():
      if 'sdm' in file.suffix:
        folder_contains_sdm_file = True
        break
    return folder_contains_sdm_file

  # we need to remove any of the spaces in the log files
  log_folder = rename_folder_before_parsing(log_folder)
  log_folder = Path(log_folder)
  unique_log_names = []
  is_pixellogger_log = False
  if not verify_valid_folder(log_folder):
    raise LookupError('The directory is not valid: {}'.format(str(log_folder)))
  # Check if the folder is a pixellogger log folder
  for file in sorted(log_folder.iterdir()):
    if 'sbuff_' in file.name:
      # if it is a pixellogger log we can sequentially parse every
      # log in the folder
      is_pixellogger_log = True
      unique_log_names.append(file)
      break

  if not is_pixellogger_log:
    for log_file in sorted(log_folder.iterdir()):
      log.info('Checking file: {} for unique SDM log file'.format(log_file))
      if '.zip' in str(log_file):
        continue
      if 'power_on_log' in str(log_file):
        continue
      if '.sdm' in log_file.name:
        if log_file.name[:-7] not in str(unique_log_names):
          log.info('log is unique, adding to the list {}'.format(log_file))
          unique_log_names.append(log_file)
          log.info(unique_log_names)

  return unique_log_names


def rename_folder_before_parsing(directory):
  """Renames the folder to a valid one for parsing
  
  Args:
    directory (str or Path): a directory of a log file

  Returns:
    validated_directory (Path): the renamed valid directory
  """
  if ' ' in str(directory):
    renamed_folder = str(directory).replace(' ', '_')
    os.makedirs(renamed_folder, exist_ok=True)
    os.rename(directory, renamed_folder)
    directory = Path(renamed_folder)
  return directory


def get_instances_of_log_by_print_from_lines(parsed_log, search_term):
  """Get a list of all OTA logs that contain the print search_term.

  Args:
    parsed_log (list): List of strings representing the log files

  Returns:
    instances_of_log (list): list of logs containing the print
  """
  current_line = 0
  start_of_individual_log = 0
  instances_of_log = []
  for line in parsed_log:
    if line == '\n':
      start_of_individual_log = current_line
    if search_term in line:
      # Get the last line of the OTA log
      tmp = current_line
      for line in parsed_log[current_line: ]:
        if line == '\n':
          last_line_of_individual_log = tmp
          break
        tmp += 1
      log.info(parsed_log[start_of_individual_log + 1 : last_line_of_individual_log])
      instances_of_log.append(parsed_log[start_of_individual_log + 1 : last_line_of_individual_log])

    current_line += 1
  return instances_of_log