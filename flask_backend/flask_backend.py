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

client = OpenAI(api_key=os.environ.get('openai_api'))

#load_dotenv()  # Load environment variables

app = Flask(__name__)
CORS(app)

# Replace with your Google Sheets API credentials file
service_account_file = os.environ.get('GOOGLE_SHEETS_CREDENTIALS_FILE')

# Google Sheet ID and range
SPREADSHEET_ID = os.environ.get('SPREADSHEET_ID')
RANGE_NAME = 'シート1!A:G'

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
    

# @app.route('/get_words', methods=['GET'])
# def get_words():
#     user_id = request.args.get('user_id')
#     print("Received user_id in Flask:", user_id) 
#     sheet = service.spreadsheets()
#     result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
#     values = result.get('values', [])

#     matching_words = []
#     for row in values:
#         # Assuming ID is in column 'B' and words in column 'C'
#         if row[1] == user_id:
#             matching_words.append(row[2])

#     return {'words': matching_words}
    
@app.route('/get_words', methods=['GET'])
def get_words():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    print("Received user_id in Flask:", user_id) 
    sheet = service.spreadsheets()
    # Adjusted the range to include pronunciation, definition, synonyms, and examples
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])

    # List to hold the words and their details
    word_details = []
    for row in values:
        if row[1] == user_id:  # Filter rows by user_id
            if len(row) < 7:  # Not all details are present
                word_data = table_content(row[2])  # Fetch missing details for the word
                # Update the sheet with the new details
                modify_sheet('update', user_id, row[2], word_data)
                word_info = {
                    "word": row[2],
                    "pronunciation": word_data["pronunciation"],
                    "definition": word_data["definition"],
                    "synonyms": word_data["synonyms"],
                    "examples": word_data["examples"]
                }
            else:
                # Directly unpack row elements into the word details dictionary
                word_info = {
                    "word": row[2],
                    "pronunciation": row[3],
                    "definition": row[4],
                    "synonyms": row[5],
                    "examples": row[6]
                }
            word_details.append(word_info)

    return word_details

def find_row_index(values, user_id, word):
    for index, row in enumerate(values):
        if row[1] == user_id and row[2] == word:
            return index
    return None

def add_word_to_sheet(sheet, user_id, word):
    # Fetch data from GPT-3
    word_data = table_content(word)

    values = [
        ['', 
        user_id, 
        word,
        word_data["pronunciation"],
        word_data["definition"],
        word_data["synonyms"],
        word_data["examples"]
        ]
    ]
    body = {'values': values}
    range_to_update = 'シート1!A:G'
    result = sheet.values().append(
        spreadsheetId=SPREADSHEET_ID, 
        range=range_to_update, 
        valueInputOption='RAW', 
        body=body
    ).execute()
    return result.get('updates', {}).get('updatedCells', 0)

def delete_word_from_sheet(user_id, word, values):
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

def update_word_in_sheet(user_id, word, word_data, values):
    for index, row in enumerate(values):
        if row[1] == user_id and row[2] == word:
            range_to_update = f'シート1!B{index + 1}:G{index + 1}'
            update_values = [[user_id, word] + list(word_data.values())]
            body = {'values': update_values}
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID, 
                range=range_to_update, 
                valueInputOption='USER_ENTERED', 
                body=body
            ).execute()
            return True
    return False

def modify_sheet(operation, user_id, word, word_data=None):
    global service  # Use the global service variable
    sheet = service.spreadsheets()

    if operation == 'add':
        return add_word_to_sheet(sheet, user_id, word)

    else:
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])

        if operation == 'delete':
            return delete_word_from_sheet(user_id, word, values)
            
        elif operation == 'update':
            return update_word_in_sheet(user_id, word, word_data, values)
        
    return False
    

def format_list_with_newlines(items):
    return '\n'.join(f'{index+1}. {item}' for index, item in enumerate(items))

def table_content(word):
    example_json = {
        "pronunciation": "",
        "definition": "",
        "synonyms": ["", "", ""],
        "examples": ["", "", ""]
    }
    prompt = f"Provide the phonetic symbol, shorter than 20 words definition, 3 synonyms, and 3 example sentences for the word '{word}' in JSON format."
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": "You are a helpful assistant designed to output JSON like the following data schema" + json.dumps(example_json)},
            {"role": "user", "content": prompt}
        ]
    )
    content = response.choices[0].message.content
    word_data = json.loads(content)
    
    return {
        "word": word,
        "pronunciation": word_data.get("pronunciation", ""),
        "definition": word_data.get("definition", ""),
        "synonyms": format_list_with_newlines(word_data.get("synonyms", [])),
        "examples": format_list_with_newlines(word_data.get("examples", []))
    }

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

# if __name__ == '__main__':
#     app.run(debug=True)