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

def sheet_operation(operation, spreadsheet_id, range_name, data=None, user_id=None, word=None):
    sheet = service.spreadsheets()
    if operation == "get":
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        return result.get('values', [])
    elif operation == "append":
        body = {'values': [data]}
        sheet.values().append(
            spreadsheetId=spreadsheet_id, 
            range=range_name, 
            valueInputOption='RAW', 
            body=body
        ).execute()
    elif operation == "update":
        body = {'values': [data]}
        sheet.values().update(
            spreadsheetId=spreadsheet_id, 
            range=range_name, 
            valueInputOption='USER_ENTERED', 
            body=body
        ).execute()
    
    elif operation == "delete":
        values = sheet_operation("get", spreadsheet_id, range_name)
        for index, row in enumerate(values):
            if len(row) > 2 and row[1] == user_id and row[2] == word:
                body = {
                    "requests": [{
                        "deleteDimension": {
                            "range": {
                                "sheetId": 0,  # Adjust if using a specific sheet within the spreadsheet
                                "dimension": "ROWS",
                                "startIndex": index,
                                "endIndex": index + 1
                            }
                        }
                    }]
                }
                response = sheet.batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
                return response  # Or a custom response indicating success
        return None


def get_or_create_user_id(email):
    values = sheet_operation("get", USER_SHEET_ID, USER_RANGE_NAME)
    
    # Search for email in the first column and get ID from the third column
    for row in values:
        if len(row) > 0 and row[0] == email:
            return row[2]  # Assuming the user ID is in the third column

    # If not found, create a new user ID, append it, and return it
    new_user_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    new_row = [email, '', new_user_id]
    sheet_operation("append", USER_SHEET_ID, USER_RANGE_NAME, data=new_row)
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
    values = sheet_operation("get", SPREADSHEET_ID, RANGE_NAME)

    # List to hold the words and their details
    word_details = []
    for row in values:
        if len(row) > 1 and row[1] == user_id:  # Ensure row has at least 2 elements and matches user_id
            # Fill missing elements with empty strings
            filled_row = row + [''] * (7 - len(row))  # Ensure row has at least 7 elements
            word_info = {
                "word": filled_row[2],
                "pronunciation": filled_row[3],
                "definition": filled_row[4],
                "synonyms": filled_row[5],
                "examples": filled_row[6]
            }
            word_details.append(word_info)

    return word_details

# def add_word_to_sheet(sheet, user_id, word):
#     # Fetch data from GPT-3
#     word_data = table_content(word)

#     values = [
#         ['', 
#         user_id, 
#         word,
#         word_data["pronunciation"],
#         word_data["definition"],
#         word_data["synonyms"],
#         word_data["examples"]
#         ]
#     ]
#     body = {'values': values}
#     result = sheet.values().append(
#         spreadsheetId=SPREADSHEET_ID, 
#         range=RANGE_NAME, 
#         valueInputOption='RAW', 
#         body=body
#     ).execute()
#     return result.get('updates', {}).get('updatedCells', 0)

# def delete_word_from_sheet(user_id, word, values):
#     for index, row in enumerate(values):
#         if len(row) > 2 and row[1] == user_id and row[2] == word:
#             body = {
#                 "requests": [{
#                     "deleteDimension": {
#                         "range": {
#                             "sheetId": 0,
#                             "dimension": "ROWS",
#                             "startIndex": index,
#                             "endIndex": index + 1
#                         }
#                     }
#                 }]
#             }
#             service.spreadsheets().batchUpdate(
#                 spreadsheetId=SPREADSHEET_ID, body=body).execute()
#             return True
#     return False

# def modify_sheet(operation, user_id, word):
#     global service  # Use the global service variable
#     sheet = service.spreadsheets()

#     if operation == 'add':
#         return add_word_to_sheet(sheet, user_id, word)

#     elif operation == 'delete':
#         result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
#         values = result.get('values', [])
#         return delete_word_from_sheet(user_id, word, values)
        
#     return False
    

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
    user_id, word = data['user_id'], data['word']
    word_data = table_content(word)  # Continue using your function to get word details

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

    sheet_operation("append", SPREADSHEET_ID, RANGE_NAME, data=values)
    return jsonify({'result': 'success'})


@app.route('/delete_word', methods=['POST'])
def delete_word():
    data = request.json
    user_id, word = data['user_id'], data['word']
    response = sheet_operation("delete", SPREADSHEET_ID, RANGE_NAME, user_id=user_id, word=word)
    if response:
        return jsonify({'result': 'success'})
    else:
        return jsonify({'result': 'word not found'}), 404


def fill_missing_content(user_id):
    # Fetch rows from the Google Sheet for the specified user_id
    values = sheet_operation("get", SPREADSHEET_ID, RANGE_NAME)
    updated_count = 0
    
    for i, row in enumerate(values):
        # Assuming the user_id is in a specific column, e.g., the third column
        if row[1] == user_id and (len(row) < 4 or not all(row[3:6])):
            word = row[2]  # Assuming the word is in the first column
            word_data = table_content(word)
            update_values = [
                word_data["pronunciation"],
                word_data["definition"],
                word_data["synonyms"],
                word_data["examples"]
            ]

            # Update the row individually
            update_range = f'シート1!D{i+1}:G{i+1}'
            sheet_operation("update", SPREADSHEET_ID, update_range, data=update_values)
            updated_count += 1

    # Return the result indicating how many words were updated
    if updated_count > 0:
        return {'result': 'success', 'updated': updated_count}
    else:
        return {'result': 'no updates needed'}


# Endpoint to trigger filling missing content for a user
@app.route('/fill_missing_content', methods=['POST'])
def fill_missing_content_endpoint():
    data = request.json
    user_id = data['user_id']
    response = fill_missing_content(user_id)
    return response

@app.route('/check_nickname', methods=['POST'])
def check_nickname():
    data = request.json
    user_id = data['user_id']
    values = sheet_operation("get", USER_SHEET_ID, 'シート1!A:D')

    for row in values:
        if len(row) > 2 and row[2] == user_id:
            nickname = row[3] if len(row) > 3 else None
            return {'nickname': nickname}

    return {'error': 'User not found'}, 404

@app.route('/update_nickname', methods=['POST'])
def update_nickname():
    data = request.json
    user_id = data['user_id']
    nickname = data['nickname']
    
    values = sheet_operation("get", USER_SHEET_ID, 'シート1!A:D')


    for i, row in enumerate(values):
        if len(row) > 2 and row[2] == user_id:  # Assuming user_id is in the third column
            range_to_update = f'シート1!D{i+1}'  # Constructing the range for the fourth column
            sheet_operation("update", USER_SHEET_ID, range_to_update, data=[[nickname]])
            return {'success': True}

    return {'error': 'User not found'}, 404

@app.route('/get_nicknames_and_ids', methods=['POST'])
def get_nicknames_and_ids():
    emails = request.json['emails']

    values = sheet_operation("get", USER_SHEET_ID, 'シート1!A:D')

    nicknames_with_ids = {}
    for row in values:
        if len(row) >= 4 and row[0] in emails:  # Column A contains emails
            nicknames_with_ids[row[3]] = row[2]  # Column D contains nicknames, Column C contains user_id

    return nicknames_with_ids

# @app.route('/add_word_for_users', methods=['POST'])
# def add_word_for_users():
#     data = request.json
#     word = data['word']
#     user_ids = data['user_ids']

#     for user_id in user_ids:
#         result = modify_sheet('add', user_id, word)
#     return result




# if __name__ == '__main__':
#     app.run(debug=True)