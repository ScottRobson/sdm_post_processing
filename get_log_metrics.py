"""Get metrics."""

import re
import os
import csv
import logging
import matplotlib.pyplot as plt
from pathlib import Path
from parsers.lassen_parser import (get_unique_log_files_capinfo_from_log_folder,
                                   get_metrics_log_from_sdm_file)


# set up the get_log_metrics logger
Path(os.getcwd() + '/logs/').mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='./logs/tool_log.log',
                    filemode='w')
log = logging.getLogger('get_log_metrics')


def get_mcs(parsed_log):
  """Get a csv file of the mcs and pdsch layer."""
  output_csv = [['Time', 'MCS', 'Layers']]
  for line in parsed_log:
    time = ""
    mcs = ""
    layer = ""
    if "pdschResult.mcs:" in line:
      line = line.replace('\t', ' ')
      tmp_line = line.split()
      time = tmp_line[2]
      # mcs = re.findall(r'%s(\d+)' % )
      mcs = tmp_line[3].split(':')[-1]
      layer = tmp_line[4].split(':')[-1]
      output_csv.append([time, mcs, layer])
  
  with open (Path(str(Path.cwd() / 'last_output.csv')), mode='w') as output_file:
    writer = csv.writer(output_file)
    for line in output_csv:
      writer.writerow(line)
  
  fig = plt.figure()
  fig, ax = plt.subplots()
  time = []
  mcs = []
  layers = []
  for tmp in output_csv:
    if 'Time' in tmp:
      continue
    time.append(tmp[0])
  #log.info(time)
  for tmp in output_csv:
    if 'MCS' in tmp:
      continue
    mcs.append(tmp[1])
  #log.info(mcs)
  for tmp in output_csv:
    if 'Layers' in tmp:
      continue
    layers.append(tmp[2])
  #log.info(layers)

  ax.plot(time, mcs, label='MCS')
  ax.plot(time, layers, label='layers')
  ax.set_xlabel('Time')
  ax.set_title("MCS and Layers")
  ax.legend()
  fig.show()
  fig.savefig('tmp2.png')


def get_lte_ca_state(parsed_log):
  """Gets plottable graph data of throughput from metrics log."""
  output_csv = [['Time', 'DL TP', 'UL TP', 'DL BW', 'UL BW', 'LTE Bands']]

  tmp_time = '0'
  dltp = '0'
  ultp = '0'
  total_dl_bw = 0
  total_ul_bw = 0
  lte_bands = ''
  lte_ca_combos = []

  for line in parsed_log:
    if 'e.l1_ca' in line:
      tmp_line = line.replace('\t', ' ')
      print(line)
      tmp_line = tmp_line.split()
      print(tmp_line)
      tmp_time = tmp_line[2]
      dltp = float(tmp_line[4].split(':')[-1]) / 1000
      ultp = float(tmp_line[5].split(':')[-1]) / 1000
      total_dl_bw = 0
      total_ul_bw = 0
      for tmp in tmp_line:
        if '.bw' in tmp:
          total_dl_bw = total_dl_bw + float(tmp.split(':')[-1])
      for tmp in tmp_line:
        if '.ulbw' in tmp:
          total_ul_bw = total_ul_bw + float(tmp.split(':')[-1])
      lte_bands = 'LTE Bands: '
      for tmp in tmp_line:
        if '.band' in tmp:
          lte_bands = lte_bands + '{}_'.format(tmp.split(':')[-1])
      lte_bands = lte_bands[:-1]
      print(lte_bands)
      if lte_bands not in lte_ca_combos:
        lte_ca_combos.append(lte_bands)

      #if 'Deact' not in line:
      output_csv.append([tmp_time, dltp, ultp, total_dl_bw, total_ul_bw, lte_bands])

  print(lte_ca_combos)
  with open (Path(str(Path.cwd() / 'last_output_tp.csv')), mode='w') as output_file:
    writer = csv.writer(output_file)
    for line in output_csv:
      writer.writerow(line)

  time = []
  dltp = []
  ultp = []
  dlbw = []
  ulbw = []
  lte_bands = []
  for tmp in output_csv:
    if 'Time' in tmp:
      continue
    time.append(tmp[0])
  #log.info(time)
  for tmp in output_csv:
    if 'DL TP' in tmp:
      continue
    dltp.append(tmp[1])
  #log.info(mcs)
  for tmp in output_csv:
    if 'UL TP' in tmp:
      continue
    ultp.append(tmp[2])
  for tmp in output_csv:
    if 'DL BW' in tmp:
      continue
    dlbw.append(tmp[3])
  for tmp in output_csv:
    if 'UL BW' in tmp:
      continue
    ulbw.append(tmp[4])
  for tmp in output_csv:
    if 'LTE Bands' in tmp:
      continue
    lte_bands.append(tmp[4])

  fig = plt.figure()
  fig, ax1 = plt.subplots()

  ax1.plot(time, dltp, label='Downlink TP')
  ax1.plot(time, ultp, label='Uplink TP')
  ax2 = ax1.twinx()
  ax2.plot(time, dlbw, 'b--', label='Downlink BW')
  ax2.plot(time, ulbw, 'g--', label='Uplink BW')
  ax1.set_xlabel('Time')
  ax1.set_ylabel('TP (Mbps)')
  ax2.set_ylabel('Bandwidth')
  ax1.set_title("DL/UL TP")
  ax1.legend()
  fig.show()
  fig.savefig('tmp1.png')



def main():
  """Main function to get the metrics."""
  log_folder = input('What is the directory of the folder?\n')
  log_files = get_unique_log_files_capinfo_from_log_folder(log_folder)
  print('log folders: {}'.format(log_files))

  for file in log_files:
    parsed_log = get_metrics_log_from_sdm_file(file)

    #get_mcs(parsed_log)
    get_lte_ca_state(parsed_log)


if __name__ == "__main__":
  main()
