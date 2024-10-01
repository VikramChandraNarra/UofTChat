import requests
from bs4 import BeautifulSoup
import csv
import json
import pandas as pd

# Fetch the webpage
url = "https://artsci.calendar.utoronto.ca/section/Computer-Science"
try:
    response = requests.get(url)
    response.raise_for_status()  # Raises an exception for HTTP errors
except requests.exceptions.RequestException as e:
    print(f"Error fetching the webpage: {e}")
    exit()

# Parse the HTML
soup = BeautifulSoup(response.text, 'html.parser')

# Extract relevant text
data = []
current_heading = None
paragraphs = []

# Loop through the elements and store them as dictionaries
for elem in soup.find_all(['h1', 'h2', 'h3', 'p', 'div', 'li']):  # Expanding tags to look for
    if elem.name in ['h1', 'h2', 'h3']:  # These are section headings
        # Save previous heading's paragraphs if there are any
        if current_heading and paragraphs:
            data.append({
                "heading": current_heading,
                "paragraphs": ' '.join(paragraphs)  # Join all paragraphs under the same heading
            })
            paragraphs = []  # Reset paragraphs for the next heading

        current_heading = elem.get_text(strip=True)

    elif elem.name == 'p' or elem.name == 'li':
        # Collect paragraphs and list items
        paragraph = ' '.join(elem.stripped_strings)  # Collect text, clean multiple spaces
        if paragraph:
            paragraphs.append(paragraph)

# Add the last section after looping
if current_heading and paragraphs:
    data.append({
        "heading": current_heading,
        "paragraphs": ' '.join(paragraphs)
    })

# Log the extracted data (optional)
for section in data:
    print(f"Heading: {section['heading']}")
    print(f"Paragraph: {section['paragraphs']}\n")

# Save as CSV using pandas for simplicity
csv_file = "UofT_Computer_Science_Description.csv"
df = pd.DataFrame(data)
df.to_csv(csv_file, index=False, encoding='utf-8')

# Save as JSON
json_file = "UofT_Computer_Science_Description.json"
with open(json_file, 'w', encoding='utf-8') as file:
    json.dump(data, file, ensure_ascii=False, indent=4)

print("Data has been saved to CSV and JSON formats.")
