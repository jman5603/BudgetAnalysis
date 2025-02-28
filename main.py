import os
import matplotlib.pyplot as plt
import numpy as np
import requests
from dotenv import load_dotenv
from googleapiclient.discovery import build
from openai import OpenAI
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def authenticate_sheets(api_key):
    return build('sheets', 'v4', developerKey=api_key).spreadsheets()

def build_pdf(date, values):
    # Set up PDF canvas
    c = canvas.Canvas("reports/" + date.replace(" ", "") + "Summary.pdf", pagesize=letter)
    width, height = letter

    # Add content
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 700, "Budget Report for " + date)
    c.setFont("Helvetica", 12)
    c.drawImage("plots/pie_chart.png", width - 516, 450, width=344, height=235, mask='auto')

    # Gather table data
    over = []
    under = []
    for row in values:
        budget = float(row[1].replace('$', '').replace(',', ''))
        spend = float(row[2].replace('$', '').replace(',', ''))
        over_under = budget - spend
        percent = over_under / budget
        if over_under < 0:
            over.append([row[0], row[1], f"${over_under:.2f}", f"{percent:.2%}"])
        elif over_under > 0:
            under.append([row[0], row[1], f"${over_under:.2f}", f"{percent:.2%}"])

    over.sort(key=lambda x: float(x[2].replace('$','').replace(',', '')), reverse=False)
    under.sort(key=lambda x: float(x[2].replace('$','').replace(',', '')), reverse=True)

    # Add table headers
    over.insert(0, ["Category", "Budget", "Over/Under", "Percent"])
    under.insert(0, ["Category", "Budget", "Over/Under", "Percent"])

    # Create and style the "over" table
    over_table = Table(over)
    over_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TEXTCOLOR', (2, 1), (2, -1), colors.red),
        ('TEXTCOLOR', (3, 1), (3, -1), colors.red),
    ]))

    # Create and style the "under" table
    under_table = Table(under)
    under_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TEXTCOLOR', (2, 1), (2, -1), colors.green),
        ('TEXTCOLOR', (3, 1), (3, -1), colors.green),
    ]))

    # Calculate the height of each table
    over_width, over_height = over_table.wrap(0, 0)
    under_width, under_height = under_table.wrap(0, 0)

    # Add the "over" table title and table to the PDF
    c.drawString(60, 400, "Over Budget")
    over_table.wrapOn(c, width, height)
    over_table.drawOn(c, 60, height - 400 - over_height)
    
    # Add the "under" table title and table to the PDF
    c.drawString(290, 400, "Under Budget")
    under_table.wrapOn(c, width, height)
    under_table.drawOn(c, 290, height - 400 - under_height)

    # Differential title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(60, 425, "Key Differentials")
    c.setFont("Helvetica", 12)

    # Add summary of the month
    summary = chatgpt(values)

    # Create a Paragraph object for the summary
    styles = getSampleStyleSheet()
    summary_paragraph = Paragraph(summary, styles['Normal'])
    
    # Add the Paragraph to the PDF
    summary_paragraph.wrapOn(c, width - 120, height)
    summary_paragraph.drawOn(c, 60, 100)

    c.save()

def chatgpt(data):
    API_KEY = os.getenv("OPENAI_KEY")

    client = OpenAI(api_key=API_KEY)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a budgeting assistant."},
            {
                "role": "user",
                "content": "I need help with my budget for February 2025. \
                    This is a list of my expenses for the month, with the \
                        first element being the category, the second the \
                            budget, and the third the actual amount spent. \
                                Please provide a paragraph summarizing my month. \
                                Here is the data: \
                                        " + str(data)
            }
        ]
    )
    return response.choices[0].message.content

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
    except:
        raise Exception("ERROR: get data failed. Data does not exist or was spelled incorrectly.")

    # Build charts
    # Filter out categories with zero spend
    filtered_values = [row for row in values if float(row[2].replace('$', '').replace(',', '')) > 0]

    # Build pie chart
    labels = [f"{row[0]} ({row[2]})" for row in filtered_values]
    spend = np.array([float(row[2].replace('$', '').replace(',', '')) for row in filtered_values])

    plt.pie(spend, labels=labels, autopct='%1.1f%%')
    plt.tight_layout()
    plt.savefig("plots/pie_chart.png", bbox_inches='tight')
    plt.clf()

    build_pdf(date, values)
    
    return 0

if __name__ == "__main__":
    main()