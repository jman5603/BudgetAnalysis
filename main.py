import os
import requests
from dotenv import load_dotenv
from googleapiclient.discovery import build

def authenticate_sheets(api_key):
    return build('sheets', 'v4', developerKey=api_key).spreadsheets()

def main():
    # Load .env and retrieve variables
    load_dotenv()
    API_KEY = os.getenv("API_KEY")
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    date = input("Enter a month to retrieve data (format '<Month> <year>', 'February 2025' for example):\n")
    RANGE = date + os.getenv("RANGE")

    # Get spreadsheet data
    sheets = authenticate_sheets(API_KEY)
    try:
        result = sheets.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE).execute()
        values = result.get("values", [])
    except:
        raise Exception("ERROR: get data failed. Data does not exist or was spelled incorrectly.")

    print(values)
    
    return 0

if __name__ == "__main__":
    main()