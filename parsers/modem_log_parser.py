"""Decides what process to use to parse modem logs.

Allows for calling a parse_log() function without calculating each time what type of log it is.
"""
from pathlib import Path
from parsers.parse_qc_log import get_parsed_text_qc, get_log_sequence_from_txt_file_qc
# from parsers.lassen_parser import LassenParser, get_signaling_log_list_lassen
import zipfile
import subprocess


def parse_lassen_signaling_log(log_path):
  pass


def parse_qc_signaling_log(log_path):
  """."""
  return get_parsed_text_qc(log_path)


def parse_modem_log_zip(path):
  """."""
  try:
    path = Path(path)
  except FileNotFoundError:
    print('Not a valid path')
    exit()
  # first check if it is a zip file, check for modem log and unzip it
  lassen_log = False
  qualcomm_log = False
  log_files_to_parse = []
  if zipfile.is_zipfile(path):
    with zipfile.ZipFile(path, 'r') as zip:
      for name in zip.namelist():
        # If it is a QC log one of these file types will be present, set the flag to True
        if '.isf' in name:
          qualcomm_log = True
        elif '.hdf' in name:
          qualcomm_log = True
        elif '.qmdl' in name:
          qualcomm_log = True
        # If it is a Lassen based log then set that flag
        elif '.sdm' in name:
          lassen_log = True

      print('Lassen log: {}, Qualcomm log: {}'.format(str(lassen_log), str(qualcomm_log)))
      if qualcomm_log or lassen_log:
        zip.extractall(str(Path.cwd()) + '/extracted_zip/')
        path = Path(str(Path.cwd()) + '/extracted_zip/')
        for file in path.iterdir():
          if qualcomm_log:
            if '.xml' in file.suffix:
              continue
            elif 'isf' in file.suffix:
              log_files_to_parse.append(file)
            elif 'hdf' in file.suffix:
              log_files_to_parse.append(file)
            elif 'qmdl' in file.suffix:
              log_files_to_parse.append(file)
          if lassen_log:
            if '.sdm' in file.suffix:
              print('lassen log found')
              log_files_to_parse.append(file)

  parsed_log_paths = []
  for log_file in log_files_to_parse:
    if qualcomm_log:
      parsed_log_paths.append(get_parsed_text_qc(log_file))
    elif lassen_log:
      parsed_log_paths.append(parse_lassen_signaling_log(log_file))

  # erase the files in /extracted_zip/, /qc_log_parsed/ and /lassen_log_parsed/
  pass

  log_sequence = []
  if qualcomm_log:
    for log in parsed_log_paths:
      log_sequence.append(get_log_sequence_from_txt_file_qc(log))


def main():

  parse_modem_log_zip('C:\\Users\\scottrobson\\PycharmProjects\\FieldTestAutomator\\modem_logs\\logs\\2021-03-29_18-48-11.zip')
  # parse_modem_log_zip('C:\\Users\\scottrobson\\PycharmProjects\\FieldTestAutomator\\modem_logs\\logs\\2021-03-29_18-48-25.zip')


if __name__ == '__main__':
  main()