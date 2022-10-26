# -*- coding: utf-8 -*-
#
# Copyright ©2018-2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at apache.org/licenses/LICENSE-2.0.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# pylint: disable=(consider-using-f-string)

"""
docs-mail-merge.py (Python 2.x or 3.x)

Google Docs (REST) API mail-merge sample app
"""
# [START mail_merge_python]
from __future__ import print_function

import time

import google.auth
import sys
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import base64
from email.message import EmailMessage

# Fill-in IDs of your Docs template & any Sheets data source
DOCS_FILE_ID = # Enter google docs file ID as string
SHEETS_FILE_ID = # Enter sheets file ID as string

# authorization constants

SCOPES = (  # iterable or space-delimited string
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/gmail.send',
)

# application constants
SOURCES = ('text', 'sheets')
SOURCE = 'sheets'  # Choose one of the data SOURCES
COLUMNS = ['EMAIL', 'NAME']

creds = None
# The file token.json stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

# pylint: disable=maybe-no-member

# service endpoints to Google APIs

DRIVE = build('drive', 'v2', credentials=creds)
DOCS = build('docs', 'v1', credentials=creds)
SHEETS = build('sheets', 'v4', credentials=creds)
GMAIL = build('gmail', 'v1', credentials=creds)

# Below is the function for writing and sending email
# -------------------------------------------------

def gmail_send_message(TO, FROM, SUBJECT, BODY):

    try:
        message = EmailMessage()

        message.set_content(BODY)

        message['To'] = TO
        message['From'] = FROM
        message['Subject'] = SUBJECT

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()) \
            .decode()

        create_message = {
            'raw': encoded_message
        }
        # pylint: disable=E1101
        send_message = (GMAIL.users().messages().send
                        (userId="me", body=create_message).execute())
        print(F'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(F'An error occurred: {error}')
        send_message = None
    return send_message

# Below are functions for merging
#--------------------------------------------------
def read_paragraph_element(element):
    """Returns the text in the given ParagraphElement.

        Args:
            element: a ParagraphElement from a Google Doc.
    """
    text_run = element.get('textRun')
    if not text_run:
        return ''
    return text_run.get('content')


def read_structural_elements(elements):
    """Recurses through a list of Structural Elements to read a document's text where text may be
        in nested elements.

        Args:
            elements: a list of Structural Elements.
    """
    text = ''
    for value in elements:
        if 'paragraph' in value:
            elements = value.get('paragraph').get('elements')
            for elem in elements:
                text += read_paragraph_element(elem)
        elif 'table' in value:
            # The text in table cells are in nested Structural Elements and tables may be
            # nested.
            table = value.get('table')
            for row in table.get('tableRows'):
                cells = row.get('tableCells')
                for cell in cells:
                    text += read_structural_elements(cell.get('content'))
        elif 'tableOfContents' in value:
            # The text in the TOC is also in a Structural Element.
            toc = value.get('tableOfContents')
            text += read_structural_elements(toc.get('content'))
    return text

def get_data(source):
    """Gets mail merge data from chosen data source.
    """
    try:
        if source not in {'sheets', 'text'}:
            raise ValueError(f"ERROR: unsupported source {source}; "
                             f"choose from {SOURCES}")
        return SAFE_DISPATCH[source]()
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error


def _get_text_data():
    """(private) Returns plain text data; can alter to read from CSV file.
    """
    return TEXT_SOURCE_DATA


def _get_sheets_data(service=SHEETS):
    """(private) Returns data from Google Sheets source. It gets all rows of
        'Sheet1' (the default Sheet in a new spreadsheet), but drops the first
        (header) row. Use any desired data range (in standard A1 notation).
    """
    return service.spreadsheets().values().get(spreadsheetId=SHEETS_FILE_ID,
                                               range='Sheet1').execute().get(
        'values')[1:]
    # skip header row


# data source dispatch table [better alternative vs. eval()]
SAFE_DISPATCH = {k: globals().get('_get_%s_data' % k) for k in SOURCES}


def _copy_template(tmpl_id, source, service):
    """(private) Copies letter template document using Drive API then
        returns file ID of (new) copy.
    """
    try:
        body = {'name': 'Merged form letter (%s)' % source}
        return service.files().copy(body=body, fileId=tmpl_id,
                                    fields='id').execute().get('id')
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error


def merge_template(tmpl_id, source, service):
    """Copies template document and merges data into newly-minted copy then
        returns its file ID.
    """
    try:
        # copy template and set context data struct for merging template values
        copy_id = _copy_template(tmpl_id, source, service)
        context = merge.iteritems() if hasattr({},
                                               'iteritems') else merge.items()
        # "search & replace" API requests for mail merge substitutions
        reqs = [{'replaceAllText': {
            'containsText': {
                'text': '{{%s}}' % key.upper(),  # {{VARS}} are uppercase
                'matchCase': True,
            },
            'replaceText': value,
        }} for key, value in context]

        # send requests to Docs API to do actual merge
        DOCS.documents().batchUpdate(body={'requests': reqs},
                                     documentId=copy_id, fields='').execute()
        return copy_id
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error


if __name__ == '__main__':
    # fill-in your data to merge into document template variables
    merge = {
        # recipient data (supplied by 'text' or 'sheets' data source)
        'EMAIL': None,
        'NAME': None
        # - - - - - - - - - - - - - - - - - - - - - - - - - -
    }

    # get row data, then loop through & process each form letter
    data = get_data(SOURCE)  # get data from data source
    for i, row in enumerate(data):
        try:
            merge.update(dict(zip(COLUMNS, row)))
            doc = DOCS.documents().get(documentId=merge_template(DOCS_FILE_ID, SOURCE, DRIVE)).execute()
            doc_content = doc.get('body').get('content')

            EMAILROW = SHEETS.spreadsheets().values().get(spreadsheetId=SHEETS_FILE_ID,
                                               range='Sheet1').execute().get(
            'values')[i+1:i+2]
            EMAILROW = EMAILROW[0]

            EMAIL_TO =  EMAILROW[0]
            EMAIL_FROM =  #Enter your email address here as a string
            EMAIL_SUBJECT = #Enter your email subject here as a string
            EMAIL_BODY = read_structural_elements(doc_content)

            gmail_send_message(EMAIL_TO, EMAIL_FROM, EMAIL_SUBJECT, EMAIL_BODY)
            print('Message sent!')
        except:
            sys.exit()
# [END mail_merge_python]
