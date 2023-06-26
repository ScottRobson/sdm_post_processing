"""The adb_interface module defines a class to automate adb interactions.

The class gives the developer or tester an adb interface where they can send
commands to all connected devices and also monitor and control the state of
those devices."""
import logging
import subprocess
from pathlib import Path


# set up the AdbInterface logger
Path('./logs/').mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='./logs/tool_log.log',
                    filemode='w')
log = logging.getLogger('adb_interface_logger')


class AdbDevice:
  pass


class AdbInterface:
  """Class AdbInterface provides a platform for managing connected adb devices.

  This class defines common adb use cases, offering control of adb devices
  to other programs perform complex tasks automatically.

  AdbInterface.run() will run a adb command
  AdbInterface.wait-for-device() will wait for any device or a specific device
  AdbInterface.get_connected_devices() will get the serial numbers of connected
  devices
  AdbInterface.wait_for_authorised_devices() waits for all connected devices
  to be authorised by the end user
  """

  def __init__(self):
    self.log = logging.getLogger('adb_interface_logger')
    self.log.info('adb interface initiated')

  def run(self, command, device_id=None, shell=False):
    """."""
    command = command.split()
    if shell:
      if 'shell' not in command:
        command.insert(0, 'shell')
    if 'adb' not in command:
      command.insert(0, 'adb')

    if device_id is not None:
      command.insert(1, '-s')
      command.insert(2, device_id)

    output = subprocess.run(command, capture_output=True)
    return output

  def wait_for_device(self, device_id=None):
    """Wait for any adb device, or the specific one in the argument device_id."""
    command = 'wait-for-device'
    output = self.run(command, device_id)
    return output

  def get_telephony_parameter(self, register_item, device_id):
    """Take the string and check if it is present in the telephony registry of the chosen device.

    Args:
      register_item: a string to search the registry
      device_id: the serial number of the device to check
    Returns:
      None if the register item is not present, or the value if it is there
    """
    register = ''
    register_item = str(register_item)
    output = self.run('root', device_id)
    self.log.debug(output)
    output = self.run('dumpsys telephony.registry', device_id, True)
    if output.returncode == 0:
      output = str(output.stdout)
      output = output.split()
      for registry in output:
        if register_item in registry:
          sub_registers = registry.split()
          for sub_register in sub_registers:
            if register_item + '=' in sub_register:
              index = sub_register.find('=')
              register = sub_register[index + 1 :]
              self.log.debug('Register item: {}:, index: {}, register value: {}'.format(sub_register,
                                                                                        str(index),
                                                                                        register))
              if len(register) > 0:
                return register

      if not register:
        self.log.debug('No register item with {} is found'.format(register_item))

    else:
      self.log.debug('Error in ADB command. Returning None')
      return None

  def get_current_rat(self, device_id):
    """Gets the current attached RAT and returns the string representation."""
    current_rat = 'unknown'
    rat_id = self.get_telephony_parameter('getRilDataRadioTechnology', device_id)
    if rat_id:
      current_rat = rat_id[ rat_id.find('(') + 1 : rat_id.find(')') ]

    return current_rat

  def get_signal_strength(self, device_id):
    """Gets a string representing the signal strength"""
    signal_strength_registry = ''
    signal_strength_dict = {}
    output = self.run('root', device_id)
    self.log.debug(output)
    output = self.run('dumpsys telephony.registry', device_id, True)
    if output.returncode == 0:
      output = str(output.stdout)
      output = output.readlines()

      for line in output:
        if 'mSignalStrength' in line:
          signal_strength_registry = line
          break

      self.log.debug('Signal Strength_registry: {}'.format(signal_strength_registry))

      # Get the individual signal strength objects from the "mSingalStrength" telephony registry
      signal_strength_objects = signal_strength_registry.split(',')

      for signal_strength_object in signal_strength_objects:
        if 'primary' in signal_strength_objects:
          continue
        if 'CellSignalStrengthNr' in signal_strength_object:
          # Add NR signal strength to the SignalStrength dictionary
          signal_strength_dict['NR'] = {}
          signal_strength_object_items = signal_strength_object.split()
          index = 0
          for item in signal_strength_object_items:
            if '=' in item:
              signal_strength_dict['NR'][signal_strength_object_items[index - 1]] = signal_strength_object_items[index + 1]
        if 'CellSignalStrengthGsm' in signal_strength_object:
          # Add GSM signal strength to SignalStrength dictionary
          signal_strength_dict['GSM'] = {}
          signal_strength_object_items = signal_strength_object.split()
          for item in signal_strength_object_items:
            if 'CellSignalStrength' in item:
              continue

            item_values = item.split('=')
            signal_strength_dict['GSM'][item_values[0]] = item_values[-1]
        if 'CellSignalStrengthWcdma' in signal_strength_object:
          # Add GSM signal strength to SignalStrength dictionary
          signal_strength_dict['WCDMA'] = {}
          signal_strength_object_items = signal_strength_object.split()
          for item in signal_strength_object_items:
            if 'CellSignalStrength' in item:
              continue

            item_values = item.split('=')
            signal_strength_dict['WCDMA'][item_values[0]] = item_values[-1]
        if 'CellSignalStrengthLte' in signal_strength_object:
          # Add GSM signal strength to SignalStrength dictionary
          signal_strength_dict['LTE'] = {}
          signal_strength_object_items = signal_strength_object.split()
          for item in signal_strength_object_items:
            if 'CellSignalStrength' in item:
              continue

            item_values = item.split('=')
            signal_strength_dict['LTE'][item_values[0]] = item_values[-1]
    else:
      print('signal strength object not available')
      self.log.debug('signal strength object not available. source: {}'.format(str(output)))

    return signal_strength_dict


  def fastboot_command(self, command, device_id=None):
    """Performs a fastboot ."""
    command = command.split()

    if device_id is not None:
      command.insert(1, '-s')
      command.insert(2, device_id)

    if 'fastboot' not in command:
      command.insert(0, 'fastboot')

    self.log.debug('command for sending to fastboot: ' + str(command))
    output = subprocess.run(command, capture_output=True)
    return output

  def get_connected_devices(self):
    """Returns a list of connected adb devices.

    format is [[serial number, status, device name, software branch, software],
    [second device]]
    if no devices are connected it returns False
    :return:
    """
    output = self.run('adb devices')
    response = str(output.stdout)
    response = response.split('\\n')

    if len(response) > 3:
      connected_devices_detail = []
      self.log.debug('some devices are connected. getting relevant lines')
      response.pop(0)
      response.pop()
      response.pop()

      for device in response:
        # Getting device serial number
        self.log.debug('adb device return: %s', device)
        current_device_detail = {}
        device = device.split('\\t')
        device_serial_number = device[0]
        current_device_detail['serial_no'] = device_serial_number
        self.log.debug('serial number = %s', current_device_detail['serial_no'])

        # Get the product name of the current device being checked
        name = self.run('getprop ro.product.name', device_serial_number, True)
        name = name.stdout.decode('utf-8')
        name = name.strip()
        self.log.debug('name: %s', name)
        current_device_detail['name'] = name

        # Get the software
        software = self.run('getprop ro.build.id ', device_serial_number, True)
        software = software.stdout.decode('utf-8')
        software = software.strip()
        software = software.replace('.', '-')
        current_device_detail['software'] = software

        # Get the MCC
        mcc = self.get_telephony_parameter('Mcc',
                                           current_device_detail['serial_no'])
        current_device_detail['mcc'] = mcc

        # Get the MNC
        mnc = self.get_telephony_parameter('Mnc',
                                           current_device_detail['serial_no'])
        current_device_detail['mnc'] = mnc

        # Get the current RAT
        current_rat = self.get_current_rat(current_device_detail['serial_no'])
        current_device_detail['rat'] = current_rat

        # Get the NW name
        current_nw_name = self.get_telephony_parameter('mOperatorAlphaShort', current_device_detail['serial_no'])
        if not current_nw_name:
          current_nw_name = 'UNKNOWN'
        current_nw_name = current_nw_name.replace(',', '')
        current_nw_name = current_nw_name.split('.')
        current_nw_name = current_nw_name[0]
        current_device_detail['nw'] = current_nw_name

        if 'unauthorized' in device:
          self.log.debug('the following device is not authorised')
          print(device_serial_number + ' is not authorised')
        if 'disconnected' in device_serial_number:
          print(device_serial_number + ' is not connected')

        connected_devices_detail.append(current_device_detail)

      self.log.debug('Connected device detail: %s',
                     str(connected_devices_detail))
      return connected_devices_detail

    else:
      self.log.debug('No devices connected')
      return None

  def wait_for_authorised_devices(self):
    """Wait for all connected devices to be authorised by the user.

    Returns:
      devices: a tuple containing the device data of all connected and
      authorised adb devices
    """
    devices = None
    all_devices_authorised = False
    self.wait_for_device()
    while not all_devices_authorised:
      devices = self.get_connected_devices()
      # print(devices)
      if devices is not None:
        print(devices)
        if 'unauthorized' in devices or 'disconnected' in devices:
          if 'unauthorized' in devices:
            print('One or more devices are not authorized. Check that the adb '
                  'connection is allowed on the phone UI')
          if 'disconnected' in devices:
            print('One or more devices are not connected. Check that the adb '
                  'connection is allowed on the phone UI or try'
                  ' "adb kill-server" and try again')
        else:
          all_devices_authorised = True

      else:
        input('No devices connected. Insert devices and press "enter" to start '
              'again')

    return devices


if __name__ == '__main__':
  pass
