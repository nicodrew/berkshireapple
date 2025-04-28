import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL of the Berkshire Hathaway 13F filings page
url = "https://13f.info/manager/0001067983-berkshire-hathaway-inc"

# Send a GET request to the page
response = requests.get(url)
response.raise_for_status()  # Ensure the request was successful

# Parse the HTML content
soup = BeautifulSoup(response.text, 'html.parser')

# Find all the links in the table and filter out unwanted ones
quarter_links = []
quarter_names = []  # To store quarter names
table = soup.find('table')
if table:
    rows = table.find_all('tr')[1:]  # Skip header row
    for row in rows:
        # Get quarter name from first column
        quarter_cell = row.find('td')
        if quarter_cell:
            quarter_name = quarter_cell.get_text(strip=True)
            link = quarter_cell.find('a')
            if link and 'href' in link.attrs:
                href = link['href']
                if "new-holdings" not in href.lower() and "restatement" not in href.lower():
                    quarter_links.append(href)
                    quarter_names.append(quarter_name)

def get_apple_percentage(quarter_string):
    base_url = "https://13f.info"
    page_url = f"{base_url}{quarter_string}"

    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(page_url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch page: {page_url}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find('table', {'id': 'filingAggregated'})
    if not table:
        print(f"No table found in {page_url}")
        return None

    data_url = table.get('data-url')
    if not data_url:
        print(f"No data-url found in table at {page_url}")
        return None

    # Now fetch the JSON data
    json_url = base_url + data_url
    json_response = requests.get(json_url, headers=headers)

    if json_response.status_code != 200:
        print(f"Failed to fetch JSON data: {json_url}")
        return None

    data_json = json_response.json()

    # Build DataFrame with correct column names
    columns = ['symbol', 'issuer_name', 'class', 'cusip', 'value', 'percentage', 'shares', 'principal', 'option_type']
    df = pd.DataFrame(data_json['data'], columns=columns)

    df['symbol'] = df['symbol'].str.strip()

    # Filter for Apple (AAPL)
    apple_row = df[df['symbol'] == 'AAPL']

    if apple_row.empty:
        print(f"Apple (AAPL) not found in {quarter_string}")
        return None

    # Get the 'percentage' field
    apple_percentage = apple_row.iloc[0]['percentage']

    return apple_percentage

# Create a list to store results
results = []

# Process each quarter
for q, name in zip(quarter_links, quarter_names):
    percentage = get_apple_percentage(q)
    if percentage:
        results.append({'Quarter': name, 'Apple Percentage': percentage})

# Create DataFrame from results
apple_percentages_df = pd.DataFrame(results)

# Display the DataFrame
print(apple_percentages_df)

# Optional: Save to CSV
apple_percentages_df.to_csv('berkshire_apple_percentages.csv', index=False)
#this may not save to the correct directory, just search for the file on your PC and move to the correct location in this case