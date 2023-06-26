"""A class containing the interfaces to Drive and Sheets and helper functions.

Creates instances of Google Drive API v3 and Google Sheets API v4 and helper
functions to create/edit/share the sheet.
Requires the service_account.json file acquired from pantheon.corp.google.com.

  How to use:
  sheet_helper = Sheet_Helper(service_account_link, scopes)
  sheet_helper.new_spreadsheet(sheet_helper.sheet_interface, title)
"""

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from pathlib import Path
from sys import platform
import logging


# set up the sheet_helper logger
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='./logs/tool_log.log',
                    filemode='w')
log = logging.getLogger('sheet_helper')


SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']


SERV_ACC_FILE = 'emeia-field-test-1ea4815f77ba.json'
if platform == 'win32':
  CLIENT_SECRET = Path(str(Path.cwd()) + str(Path('\\google_apis\\client_secret_pixel_carrier_enginnering_external.json')))
else:
  CLIENT_SECRET = Path(str(Path.cwd()) + str(Path('/google_apis/client_secret_pixel_carrier_enginnering_external.json')))

EMAIL = 'scottrobson@google.com'


class SheetHelper:
  """Container class for GSheets and Drive APIs and helper functions.

  Attributes:
    service_acount_link: A link to the service_account.json file obtained from
      pantheon.corp.google.com. If one is not provided my FieldTestScripts is
      used
    scopes: The google API scopes that are associated with the service account.
      If one is not provided then it defaults to
      https://www.googleapis.com/auth/spreadsheets
      https://www.googleapis.com/auth/drive.file.
    creds: The parsed credentils provided by oauth2 API
    sheet_interface: The object containing the callable Sheets API
    drive_interface: The object containing the callable Drive API
  """

  def __init__(self, client_secret=CLIENT_SECRET, scopes=SCOPES):

    self.creds = self.get_credentials(client_secret, scopes)
    self.sheet_interface = self.get_sheets_interface(self.creds)
    self.drive_interface = self.get_drive_interface(self.creds)

  def get_credentials(self, client_secret, scopes):
    """Generates the credentials for activating the google APIs using oauth."""
    print(client_secret)
    print()
    creds = None
    if platform == 'win32':
      if Path(str(Path.cwd()) + '\\google_apis\\token.json').exists():
        creds = Credentials.from_authorized_user_file(str(Path.cwd()) + '\\google_apis\\token.json', scopes)
    else:
      if Path(str(Path.cwd()) + '/google_apis/token.json').exists():
        creds = Credentials.from_authorized_user_file(str(Path.cwd()) + '/google_apis/token.json', scopes)

    if not creds or not creds.valid:
      if creds and creds.expired and creds.refresh:
        creds.refresh(Request())
      else:
        flow = InstalledAppFlow.from_client_secrets_file(client_secret, scopes)
        creds = flow.run_local_server(port=0)
      if platform == 'win32':
        with open(str(Path.cwd()) + '\\google_apis\\token.json', 'w') as token:
          token.write(creds.to_json())
      else:
        with open(str(Path.cwd()) + '/google_apis/token.json', 'w') as token:
          token.write(creds.to_json())
    return creds

  def get_credentials_serv_acc(self, serv_acc_file, scopes):
    """Generates the credentials for activating the google APIs using service account."""
    creds = service_account.Credentials.from_service_account_file(serv_acc_file, scopes=scopes)

    log.info('got creds')
    return creds

  def get_sheets_interface(self, creds):
    """Calls the Google Sheets API and generates the interface."""
    sheets_service = build('sheets', 'v4', credentials=creds)
    sheets_interface = sheets_service.spreadsheets()
    log.info('got sheet interface')

    return sheets_interface

  def get_drive_interface(self, creds):
    """Calls the Google Sheets API and generates the interface."""
    drive_interface = build('drive', 'v3', credentials=creds)
    log.info('got drive interface')

    return drive_interface

  def new_spreadsheet(self, title, email=EMAIL, role='writer'):
    """Creates a new spreadhseet with specified title."""
    sheet_properties = {
        'properties':
        {
            'title': title
        }
    }
    new_sheet = self.sheet_interface.create(body=sheet_properties,
                                            fields='spreadsheetId').execute()
    self.share_sheet(new_sheet.get('spreadsheetId'))
    return new_sheet

  def share_sheet(self, file_id, email=EMAIL, role='writer'):
    """Shares a specified google sheet with the email specified."""
    transfer_ownership = False
    if role == 'owner' or role == 'organizer':
      transfer_ownership = True

    print('sharing with ' + email + ' ' + role + ' ' + file_id)
    user_permissions = {
        'type': 'user',
        'role': role,
        'emailAddress': email
    }

    res = self.drive_interface.permissions().create(
        fileId=file_id,
        body=user_permissions,
        fields='id',
        transferOwnership=transfer_ownership
    ).execute()

    return res

  def batch_update(self, body, output_sheet_id):
    """Receives a ilst of updates to sheets and applies them."""
    res = self.sheet_interface.batchUpdate(
        spreadsheetId=output_sheet_id,
        body=body
        ).execute()

    return res

  def read_range(self, value_range, output_sheet_id):
    """Reads a range of values from the given sheet."""
    result = self.sheet_interface.values().batchGet(
        spreadsheetId=output_sheet_id,
        ranges=value_range
    ).execute()

    return result

  def read_single_values(self, value_range, output_sheet_id):
    """Reads a single set of values from a Google Sheet.

    Args:
      value_range: the range in valuerange format e.g. SheetName!A1:C10.
      output_sheet_id: the working sheet ID read from
    Returns:
      values: the requested values from the sheet
    """
    result = self.sheet_interface.values().get(
        spreadsheetId=output_sheet_id,
        range=value_range
    ).execute()

    values = result.get('values', [])

    return values

  def update_sheet(self, body, value_range, output_sheet_id,
                   value_input_option='RAW'):
    """Use to update a sheet."""
    self.sheet_interface.values().update(
        spreadsheetId=output_sheet_id,
        range=value_range,
        valueInputOption=value_input_option,
        body=body
    ).execute()

  def new_worksheet(self, sheet_name, output_sheet_id):
    """Helper function to create a new spreadsheet with given name."""
    data = {
        'requests': [{
            'addSheet': {
                'properties': {
                    'title': sheet_name
                }
            }
        }]
    }

    result = self.batch_update(data, output_sheet_id)

    return result

  def rename_sheet(self, old_name, new_name, output_sheet_id):
    """Helper function to easily rename a sheet."""

    sheet_metadata = self.sheet_interface.get(spreadsheetId=output_sheet_id
                                             ).execute()
    # Search the given spreadsheet for the old_name string and pull the ID
    sheets = sheet_metadata.get('sheets')
    for i in sheets:
      if i.get('properties').get('title') == old_name:
        sheet_id = (i.get('properties').get('sheetId'))

    if sheet_id is None:
      raise Exception('old title not found')

    sheet_properties = {
        'requests': [{
            'updateSheetProperties': {
                'properties': {
                    'sheetId': sheet_id,
                    'title': new_name,
                },
                'fields': 'title',
            }
        }]
    }

    result = self.batch_update(sheet_properties, output_sheet_id)

    return result

  def new_worksheet_with_data(self, sheet_name, value_range, spreadsheet_id,
                              data):
    """Calls the new_worksheet and batch_update commands to add filled sheet."""
    # TODO(scottrobson) check and parse the value_range to ensure it is valid
    sheet = self.new_worksheet(sheet_name, spreadsheet_id)
    value_range = sheet_name + value_range
    self.update_sheet(data, value_range, spreadsheet_id)
    return sheet

  def delete_worksheet(self, sheet_name, spreadsheet_id):
    """Deletes a worksheet of a specific name."""
    sheet_metadata = self.sheet_interface.get(spreadsheetId=spreadsheet_id
                                             ).execute()
    sheets = sheet_metadata.get('sheets')
    for i in sheets:
      if i.get('properties').get('title') == sheet_name:
        sheet_id = (i.get('properties').get('sheetId'))

    request = {
        'requests': [
            {
                'deleteSheet': {
                    'sheetId': sheet_id
                }
            }
        ]
    }
    result = self.batch_update(request, spreadsheet_id)
    return result

  def get_next_available_row(self, spreadsheet_id, sheet_name):
    """."""
    row_a = self.read_single_values(sheet_name + '!A:A', spreadsheet_id)

    return len(row_a) + 1