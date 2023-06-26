"""Compare metrics from 2 SDM logs."""

import re
import os
import csv
import sys
import logging
import matplotlib.pyplot as plt
import matplotlib.dates as md
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from matplotlib.backends.backend_pdf import PdfPages
from parsers.lassen_parser import (get_unique_log_files_capinfo_from_log_folder,
                                   get_metrics_log_from_sdm_file)

# set up the get_log_metrics logger
Path(os.getcwd() + '/logs/').mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='./logs/tool_log.log',
                    filemode='w')
log = logging.getLogger('compare_sdm_metrics')


PDF_NAME = 'Log_File_Analysis_' + datetime.now().strftime('%H-%M-%S') + '.pdf'

def get_nr_state(parsed_log):
  """."""
  output_csv = [['Time', 'DL TP', 'UL TP']]

  for line in parsed_log:
    if 'n.L2_NR_MacThroughput' in line:
      tmp_line = line.replace('\t', ' ')
      tmp_line = line.split()
      time = datetime.strptime(tmp_line[2], '%H:%M:%S.%f')
      ultp = float(tmp_line[3].split(':')[-1]) / 1000
      dltp = float(tmp_line[5].split(':')[-1]) / 1000
      output_csv.append([time, dltp, ultp])

  return output_csv


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
      tmp_line = tmp_line.split()
      tmp_time = datetime.strptime(tmp_line[2], '%H:%M:%S.%f')
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
          lte_bands = lte_bands + 'B{}_'.format(tmp.split(':')[-1])
      lte_bands = lte_bands[:-1]
      log.info(lte_bands)
      if lte_bands not in lte_ca_combos:
        lte_ca_combos.append(lte_bands)

      #if 'Deact' not in line:
      output_csv.append([tmp_time, dltp, ultp, total_dl_bw, total_ul_bw, lte_bands.split()[-1]])

  log.info(output_csv[-6:-1])
  log.info(lte_ca_combos)
  return output_csv


def get_time_of_metrics(parsed_log, category):
  """."""
  time_list = []
  for line in parsed_log:
    if category in line:
      line = line.replace('\t', ' ')
      tmp_line = line.split()
      # time_list.append(datetime.strptime(tmp_line[1], '%H:%M:%S.%f'))
      time_list.append(tmp_line[1])

  return time_list


def get_list_of_metrics(parsed_log, category, metric, addative=False):
  """Take in the psrsed log and extract a list of the metrics"""
  metric_list = []
  time_list = []

  for line in parsed_log:
    if category in line:
      tmp_metric = ''
      # Get the line as separated by spaces
      line = line.replace('\t', ' ')
      tmp_line = line.split()
      tmp_time = tmp_line[2]
      tmp_time = datetime.strptime(tmp_time, '%H:%M:%S.%f')
      if addative:
        tmp_value = 0.0
        for tmp in tmp_line[3:]:
          if metric in tmp:
            log.info('{} line: {}'.format(str(tmp_value), tmp))
            tmp_value = tmp_value + float(tmp.split(':')[-1])
        tmp_metric = tmp_value

      else:
        for tmp in tmp_line[3:]:
          if metric in tmp:
            tmp_metric = tmp.split(':')[-1]
            tmp_metric_is_number = True
            if tmp_metric_is_number:
              try:
                tmp_metric = float(tmp_metric)
              except ValueError:
                tmp_metric_is_number = False
                log.info('value is not a float {}'.format(tmp_metric))
            break

      if not tmp_metric:
        log.info('{} is not present in line {}'.format(metric, line))
      else:
        metric_list.append(tmp_metric)
        time_list.append(tmp_time)

  return (time_list, metric_list)


# def get_comparisson_graph(dut_parsed_log, ref_parsed_log, )


def get_graph_of_full_data_rate(dut_parsed_log, ref_parsed_log, output_pdf):
  """gets a graph of the DUT v REF total data, bler"""
  def get_metric(line):
    """."""
    metric = line.split(':')[-1]
    try:
      metric = metric.replace(',', '')
      return float(metric)
    except ValueError:
      return metric

  dut_dltp = []
  dut_ultp = []
  dut_dlbler = []
  dut_ulbler = []
  dut_time = []
  output_csv = [['Time', 'DLTP', 'ULTP', 'DLBLER', 'ULBLER']]

  for line in dut_parsed_log:
    if 'c.data' in line:
      tmp_line = line.split()
      # dut_time.append(tmp_line[1])
      time = datetime.strptime(tmp_line[1], '%H:%M:%S.%f')
      dut_time.append(md.date2num(time))
      # time = tmp_line[1]

      for tmp in tmp_line:
        if 'dltp' in tmp:
          dltp = get_metric(tmp)
          dut_dltp.append(get_metric(tmp))
        if 'ultp' in tmp:
          ultp = get_metric(tmp)
          dut_ultp.append(get_metric(tmp))
        if 'dlbler' in tmp:
          dlbler = get_metric(tmp)
          dut_dlbler.append(get_metric(tmp))
        if 'ulbler' in tmp:
          ulbler = get_metric(tmp)
          dut_ulbler.append(get_metric(tmp))
      output_csv.append([time, dltp, ultp, dlbler, ulbler])

  with open(Path(str(Path.cwd() / 'last_output_tp_dut.csv')), mode='w') as output_file:
    writer = csv.writer(output_file)
    for line in output_csv:
      writer.writerow(line)
  
  ref_dltp = []
  ref_ultp = []
  ref_dlbler = []
  ref_ulbler = []
  ref_time = []
  output_csv = [['Time', 'DLTP', 'ULTP', 'DLBLER', 'ULBLER']]

  for line in ref_parsed_log:
    if 'c.data' in line:
      tmp_line = line.split()
      time = datetime.strptime(tmp_line[1], '%H:%M:%S.%f')
      ref_time.append(md.date2num(time))

      for tmp in tmp_line:
        if 'dltp' in tmp:
          dltp = get_metric(tmp)
          ref_dltp.append(get_metric(tmp))
        if 'ultp' in tmp:
          ultp = get_metric(tmp)
          ref_ultp.append(get_metric(tmp))
        if 'dlbler' in tmp:
          dlbler = get_metric(tmp)
          ref_dlbler.append(get_metric(tmp))
        if 'ulbler' in tmp:
          ulbler = get_metric(tmp)
          ref_ulbler.append(get_metric(tmp))
      output_csv.append([time, dltp, ultp, dlbler, ulbler])

  #TODO: Merge the lists so the time is a persistent value

  with open (Path(str(Path.cwd() / 'last_output_tp_ref.csv')), mode='w') as output_file:
    writer = csv.writer(output_file)
    for line in output_csv:
      writer.writerow(line)

  fig = plt.figure()
  fig, ax1 = plt.subplots()
  ax1.plot(dut_time, dut_dltp, 'b-', label='DUT DL TP')
  # ax1.plot(dut_time, dut_ultp, label='DUT UL TP')
  ax1.xaxis.set_major_formatter(md.DateFormatter('%H:%M:%S'))
  ax2 = ax1.twiny()
  ax2.plot(ref_time, ref_dltp, 'r-', label='REF DL TP')
  ax2.xaxis.set_major_formatter(md.DateFormatter('%H:%M:%S'))
  #ax2.plot(ref_time, ref_ultp, label='REF DL TP')
  #ax2.plot(ref_time, ref_ultp, label='REF UL TP')
  ax1.set_xlabel('Time')
  ax1.set_ylabel('TP (Gbps)')
  ax1.set_title('DUT v REF Total DL TP')
  plt.legend(loc='best')
  fig.savefig('DUT-v-REF_Full_DL_Data_Rate.png')
  output_pdf.savefig(fig)

  fig = plt.figure()
  fig, ax1 = plt.subplots()
  ax1.plot(dut_time, dut_dltp, 'b-', label='DUT UL TP')
  # ax1.plot(dut_time, dut_ultp, label='DUT UL TP')
  ax1.xaxis.set_major_formatter(md.DateFormatter('%H:%M:%S'))
  ax2 = ax1.twiny()
  ax2.plot(ref_time, ref_dltp, 'r-', label='REF UL TP')
  ax2.xaxis.set_major_formatter(md.DateFormatter('%H:%M:%S'))
  #ax2.plot(ref_time, ref_ultp, label='REF DL TP')
  #ax2.plot(ref_time, ref_ultp, label='REF UL TP')
  ax1.set_xlabel('Time')
  ax1.set_ylabel('TP (Gbps)')
  ax1.set_title('DUT v REF Total UL TP')
  plt.legend(loc='best')
  fig.savefig('DUT-v-REF_Full_UL_Data_Rate.png')
  output_pdf.savefig(fig)
  return output_pdf


def get_time_spent_in_lte_ca_bands(lte_dataframe):
  """."""
  # get the duration of LTE CA state
  time_in_bands = []
  # get the initial line for comparisson
  for index, line in lte_dataframe.iterrows():
    log.info(line['LTE Bands'])
    first_ca_band = line['LTE Bands']
    last_time = line['Time']
    log.info(type(last_time))
    time_in_bands.append([first_ca_band, last_time - last_time + timedelta(milliseconds=50)])
    break
  log.info(time_in_bands)
  for index, line in lte_dataframe.iterrows():
    band_present = False
    for row in time_in_bands:
      if line['LTE Bands'] in row:
        band_present = True
        break

    if not band_present:
      time_in_bands.append([line['LTE Bands'], timedelta(milliseconds=50)])
    else:
      for num, combo in enumerate(time_in_bands):
        log.info(time_in_bands)
        log.info(time_in_bands[num][1])
        if line['LTE Bands'] in combo:
          log.info(line['Time'])
          log.info(last_time)
          dif = line['Time'].to_pydatetime() - last_time
          log.info(dif)
          time_in_bands[num][1] = time_in_bands[num][1] + line['Time'].to_pydatetime() - last_time
          break
    last_time = line['Time'].to_pydatetime()

  log.info(time_in_bands)

  return time_in_bands


def main():
  """Main function to compare SDM metrics."""
  #TODO: allow the main function to receive either one or two CLI inputs with the directories of log files

  # If there are 2 command line entries we can use those as log paths
  args = sys.argv[1:]
  if len(args) > 1:
    dut_log_folder = args[0]
    dut_log_file = get_unique_log_files_capinfo_from_log_folder(dut_log_folder)[0]
    ref_log_folder = args[1]
    ref_log_file = get_unique_log_files_capinfo_from_log_folder(ref_log_folder)[0]
  else:
    #Lets get the DUT log file
    dut_log_folder = input('What is the directory of the folder with the DUT logs?\n')
    directory_log_files = get_unique_log_files_capinfo_from_log_folder(dut_log_folder)
    dut_log_file = None
    for log_file in directory_log_files:
      response = input('is this your DUT log file? y/n: {}\n'.format(str(log_file)))
      if response == 'y':
        dut_log_file = log_file
        break
    if not dut_log_file:
      exit('None of the log files are DUT. Please try again with a different directory')

    # Now lets get the reference log folder.
    ref_log_folder = input('What is the directory of the folder with the REF logs?\n')
    directory_log_files = get_unique_log_files_capinfo_from_log_folder(ref_log_folder)
    ref_log_file = None
    for log_file in directory_log_files:
      response = input('is this your REF log file? y/n: {}\n'.format(str(log_file)))
      if response == 'y':
        ref_log_file = log_file
        break
    if not ref_log_file:
      exit('None of the log files are REF. Please try agian with a different directory.\n'
          'Or if you only want to view graphs of one log use the "get_log_metrics.py" file.')

  # If we get here then we have two valid DUT and REF logs
  print('DUT log file: {}'.format(str(dut_log_file)))
  print('REF log file: {}'.format(str(ref_log_file)))

  dut_log_metrics = get_metrics_log_from_sdm_file(dut_log_file, overwrite=False)
  ref_log_metrics = get_metrics_log_from_sdm_file(ref_log_file, overwrite=False)

  dut_time, dut_log_metrics_lte_dltp = get_list_of_metrics(dut_log_metrics, 'e.l1_ca', 'dltp')
  ref_time, ref_log_metrics_lte_dltp = get_list_of_metrics(ref_log_metrics, 'e.l1_ca', 'dltp')

  dut_time2, dut_log_metrics_lte_dlbw = get_list_of_metrics(dut_log_metrics, 'e.l1_ca', '.bw', addative=True)
  ref_time2, ref_log_metrics_lte_dlbw = get_list_of_metrics(ref_log_metrics, 'e.l1_ca', '.bw', addative=True)

  log.info(len(dut_log_metrics_lte_dltp))
  log.info(len(ref_log_metrics_lte_dltp))

  output_pdf = PdfPages(PDF_NAME)

  fig = plt.figure()
  fig, ax1 = plt.subplots()

  ax1.plot(dut_time, dut_log_metrics_lte_dltp, label='Downlink TP DUT')
  ax2 = ax1.twiny()
  ax3 = ax1.twinx()
  #ax4 = ax1.twinx()
  ax2.plot(ref_time, ref_log_metrics_lte_dltp, 'g', label='Downlink TP REF')
  ax3.plot(dut_time2, dut_log_metrics_lte_dlbw, 'o--', label='DL BW')
  ax3.plot(ref_time2, ref_log_metrics_lte_dlbw, 'g--', label='Ref BW')
  ax1.set_xlabel('Time')
  ax1.set_ylabel('TP (kbps)')
  ax3.set_ylabel('Bandwidth (MHz)')
  ax1.set_title('LTE DL TP DUTvREF')
  fig.show()
  fig.savefig('dut-ref-BW.png')
  output_pdf.savefig(fig)

  get_graph_of_full_data_rate(dut_log_metrics, ref_log_metrics, output_pdf)

  dut_lte_state = pd.DataFrame(get_lte_ca_state(dut_log_metrics)[1:], columns=['Time', 'DL TP', 'UL TP', 'DL BW', 'UL BW', 'LTE Bands'])
  ref_lte_state = pd.DataFrame(get_lte_ca_state(ref_log_metrics)[1:], columns=['Time', 'DL TP', 'UL TP', 'DL BW', 'UL BW', 'LTE Bands'])

  log.info(str(dut_lte_state[0:5]))
  log.info(str(ref_lte_state[0:5]))

  fig = plt.figure()
  fig, ax1 = plt.subplots()

  ax1.plot(dut_lte_state["Time"], dut_lte_state["DL TP"], label='DUT Downlink TP')
  ax4 = ax1.twinx()
  ax4.plot(dut_lte_state["Time"], dut_lte_state["DL BW"], 'r--', label='DUT DL Bandwidth')
  ax2 = ax1.twiny()
  ax2.plot(ref_lte_state["Time"], ref_lte_state["DL TP"], 'g-', label='REF Downlink TP')
  ax5 = ax2.twinx()
  ax5.plot(ref_lte_state["Time"], ref_lte_state["DL BW"], 'y--', label='REF DL Bandwidth')
  ax1.set_ylabel('LTE DL TP (Mbps)')
  ax2.set_ylabel('Bandwidth (MHz)')
  ax1.set_title('DUT v REF LTE TP and BW')
  plt.legend(loc='best')
  fig.show()
  fig.savefig('dut-v-ref-lte-dltp-bw.png')
  output_pdf.savefig(fig)

  fig = plt.figure()
  fig, ax1 = plt.subplots()

  ax1.plot(dut_lte_state["Time"], dut_lte_state["UL TP"], label='Downlink TP')
  ax1.plot(dut_lte_state["Time"], dut_lte_state["UL BW"], 'b--', label='DL Bandwidth')
  ax2 = ax1.twiny()
  ax2.plot(ref_lte_state["Time"], ref_lte_state["UL TP"], 'g-', label='Downlink TP')
  ax2.plot(ref_lte_state["Time"], ref_lte_state["UL BW"], 'g--', label='DL Bandwidth')
  ax1.set_ylabel('LTE DL TP (Mbps)')
  ax2.set_ylabel('Bandwidth (MHz)')
  ax1.set_title('DUT v REF LTE UL TP and BW')
  plt.legend(loc='best')
  fig.show()
  fig.savefig('dut-v-ref-lte-ultp-bw.png')
  output_pdf.savefig(fig)

  fig = plt.figure()
  fig, ax1 = plt.subplots()

  ax1.plot(dut_lte_state["Time"], dut_lte_state["DL TP"], label='Downlink TP')
  ax1.plot(dut_lte_state["Time"], dut_lte_state["LTE Bands"], 'b--', label='DL Bandwidth')
  ax2 = ax1.twiny()
  ax2.plot(ref_lte_state["Time"], ref_lte_state["DL TP"], 'g-', label='Downlink TP')
  ax2.plot(ref_lte_state["Time"], ref_lte_state["LTE Bands"], 'g--', label='DL Bandwidth')
  ax1.set_ylabel('LTE DL TP (Mbps)')
  ax2.set_ylabel('Bandwidth (MHz)')
  ax1.set_title('DUT v REF LTE UL TP and BW')
  plt.legend(loc='best')
  fig.show()
  fig.savefig('dut-v-ref-lte-dltp-bands.png')
  output_pdf.savefig(fig)

  analysis = []
  # analysis.append('DUT has average DLTP {}'.format(str(dut_lte_state[dut_lte_state["DL TP"] > 5].mean(1))))
  tmp_df = dut_lte_state[dut_lte_state["DL TP"] > 10.0]
  dut_time_in_bands = get_time_spent_in_lte_ca_bands(tmp_df)
  log.info(dut_time_in_bands)
  tmp_str = 'While in data download mode, the DUT is in the following LTE CA state:\n'
  for line in dut_time_in_bands:
    tmp_str = tmp_str + line[0] + ': ' + str(line[1])
  analysis.append(tmp_str)
  tmp_df = dut_lte_state[dut_lte_state["DL TP"] > 10.0]["DL TP"]
  log.info(tmp_df.mean())

  analysis.append('DUT has average LTE DLTP: {}'.format(str(int(tmp_df.mean()))))

  tmp_df = ref_lte_state[ref_lte_state["DL TP"] > 10.0]
  ref_time_in_bands = get_time_spent_in_lte_ca_bands(tmp_df)
  log.info(ref_time_in_bands)
  tmp_str = 'While in data download mode, the REF is in the following LTE CA state:\n'
  for line in ref_time_in_bands:
    tmp_str = tmp_str + line[0] + ': ' + str(line[1]) + '\n'
  analysis.append(tmp_str)
  tmp_df = ref_lte_state[ref_lte_state["DL TP"] > 10.0]["DL TP"]
  analysis.append('Reference has average LTE DLTP: {}'.format(str(int(tmp_df.mean()))))

  dut_nr_state = pd.DataFrame(get_nr_state(dut_log_metrics)[1:], columns=['Time', 'DL TP', 'UL TP'])
  ref_nr_state = pd.DataFrame(get_nr_state(ref_log_metrics)[1:], columns=['Time', 'DL TP', 'UL TP'])

  fig = plt.figure()
  fig, ax1 = plt.subplots()

  ax1.plot(dut_nr_state['Time'], dut_nr_state['DL TP'], label='DUT NR DL TP')
  ax1.set_title('NR DL TP DUT v REF')
  ax2 = ax1.twiny()
  ax2.plot(ref_nr_state['Time'], ref_nr_state['DL TP'], 'g', label='REF NR DL TP')

  plt.legend(loc='best')
  fig.savefig('dut-v-ref-nr-dl-stats.png')
  output_pdf.savefig(fig)

  fig = plt.figure()
  fig, ax1 = plt.subplots()

  ax1.plot(dut_nr_state['Time'], dut_nr_state['UL TP'], label='DUT NR UL TP')
  ax1.set_title('NR UL TP DUT v REF')
  ax2 = ax1.twiny()
  ax2.plot(ref_nr_state['Time'], ref_nr_state['UL TP'], 'r', label='REF NR UL TP')
  plt.legend(loc='best')
  fig.savefig('dut-v-ref-nr-ul-stats.png')
  output_pdf.savefig(fig)

  output_pdf.close()

  for line in analysis:
    print(line)


if __name__ == "__main__":
  main()