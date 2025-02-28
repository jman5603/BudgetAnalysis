import os
import matplotlib.pyplot as plt
import numpy as np
import requests
from dotenv import load_dotenv
from googleapiclient.discovery import build
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def authenticate_sheets(api_key):
    return build('sheets', 'v4', developerKey=api_key).spreadsheets()

def build_pdf(date):
    # Set up PDF canvas
    c = canvas.Canvas("reports/" + date.replace(" ", "") + "Summary.pdf", pagesize=letter)
    width, height = letter

    # Add content
    c.drawString(200, 700, "Summary Report for " + date)
    c.drawImage("plots/pie_chart.png", 100, 450, width=344, height=235, mask='auto')

    c.save()

def main():
    # Load .env and retrieve variables
    load_dotenv()
    API_KEY = os.getenv("API_KEY")
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    # date = input("Enter a month to retrieve data (format '<Month> <year>', 'February 2025' for example):\n")
    date = "February 2025"
    if date == "February 2025":
        RANGE = "February 2025!A2:C13"
    else:
        RANGE = date + os.getenv("RANGE")

    # Get spreadsheet data
    sheets = authenticate_sheets(API_KEY)
    try:
        result = sheets.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE).execute()
        values = result.get("values", [])
        print(values)
    except:
        raise Exception("ERROR: get data failed. Data does not exist or was spelled incorrectly.")

    # Build charts
    # Filter out categories with zero spend
    filtered_values = [row for row in values if float(row[2].replace('$', '').replace(',', '')) > 0]

    # Build pie chart
    labels = [f"{row[0]} ({row[2]})" for row in filtered_values]
    spend = np.array([float(row[2].replace('$', '').replace(',', '')) for row in filtered_values])
    spend1 = [float(row[2].replace('$', '').replace(',', '')) for row in filtered_values]
    
    print("Labels:", labels)
    print("Spend:", spend1)

    plt.pie(spend, labels=labels, autopct='%1.1f%%')
    plt.tight_layout()
    plt.savefig("plots/pie_chart.png", bbox_inches='tight')
    plt.clf()

    build_pdf(date)
    
    return 0

if __name__ == "__main__":
    main()