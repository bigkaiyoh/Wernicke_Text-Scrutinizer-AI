from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import service_account
from googleapiclient.discovery import build
from openai import OpenAI
import os
import base64
import json
import random
import string
from dotenv import load_dotenv



#load_dotenv()  # Load environment variables

app = Flask(__name__)
CORS(app)

# Replace with your Google Sheets API credentials file
service_account_file = os.environ.get('GOOGLE_SHEETS_CREDENTIALS_FILE')

# Google Sheet ID and range
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')
RANGE_NAME = 'シート1!A:C'

USER_SHEET_ID = os.environ.get('USERSHEET_ID')
USER_RANGE_NAME = 'シート1!A:C'


def get_google_sheets_service():
    creds_json = base64.b64decode(service_account_file)
    creds = service_account.Credentials.from_service_account_info(json.loads(creds_json))
    service = build('sheets', 'v4', credentials=creds)
    return service

# Initialize Google Sheets Service at the start
service = get_google_sheets_service()

def get_or_create_user_id(email):
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=USER_SHEET_ID, range=USER_RANGE_NAME).execute()
    values = result.get('values', [])

    # Search for email in the first column and get ID from the third column
    for row in values:
        if len(row) > 0 and row[0] == email:
            return row[2]  # Assuming the user ID is in the third column

    # If not found, create a new user ID, append it, and return it
    new_user_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    new_row = [email, '', new_user_id]
    sheet.values().append(
        spreadsheetId=USER_SHEET_ID, 
        range=USER_RANGE_NAME, 
        valueInputOption='RAW', 
        body={'values': [new_row]}
    ).execute()
    return new_user_id

@app.route('/get_or_create_user', methods=['POST'])
def get_or_create_user():
    data = request.json
    email = data.get('email')
    if email:
        user_id = get_or_create_user_id(email)
        return jsonify({'user_id': user_id})
    else:
        return jsonify({'error': 'Email is required'}), 400
    

@app.route('/get_words', methods=['GET'])
def get_words():
    user_id = request.args.get('user_id')
    print("Received user_id in Flask:", user_id) 
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])

    matching_words = []
    for row in values:
        # Assuming ID is in column 'B' and words in column 'C'
        if row[1] == user_id:
            matching_words.append(row[2])

    return {'words': matching_words}

def modify_sheet(operation, user_id, word=None):
    global service  # Use the global service variable
    sheet = service.spreadsheets()

    if operation == 'add':
        values = [['', user_id, word]]
        body = {'values': values}
        result = sheet.values().append(
            spreadsheetId=SPREADSHEET_ID, 
            range=RANGE_NAME, 
            valueInputOption='RAW', 
            body=body
        ).execute()
        return result.get('updates').get('updatedCells')

    elif operation == 'delete':
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])

        for index, row in enumerate(values):
            if len(row) > 2 and row[1] == user_id and row[2] == word:
                body = {
                    "requests": [{
                        "deleteDimension": {
                            "range": {
                                "sheetId": 0,
                                "dimension": "ROWS",
                                "startIndex": index,
                                "endIndex": index + 1
                            }
                        }
                    }]
                }
                service.spreadsheets().batchUpdate(
                    spreadsheetId=SPREADSHEET_ID, body=body).execute()
                return True
        return False



@app.route('/add_word', methods=['POST'])
def add_word():
    data = request.json
    result = modify_sheet('add', data['user_id'], data['word'])
    if result:
        return {'result': 'success', 'updatedCells': result}
    else:
        return {'result': 'error'}, 500

@app.route('/delete_word', methods=['POST'])
def delete_word():
    data = request.json
    success = modify_sheet('delete', data['user_id'], data['word'])
    if success:
        return {'result': 'success'}
    else:
        return {'result': 'word not found'}, 404

