import requests
from bs4 import BeautifulSoup
import pandas as pd 
from datetime import datetime
import os
import time

url = "https://13f.info/manager/0001037389-renaissance-technologies-llc"

start_time = time.time()

# Send a GET request to the page
response = requests.get(url)
response.raise_for_status()  # Ensure the request was successful

# Parse the HTML content
soup = BeautifulSoup(response.text, 'html.parser')

# Find all the links in the table and filter out unwanted ones
quarter_links = []
quarter_names = []  
filing_dates = [] 
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
                if "new-holdings" not in href.lower():
                    quarter_links.append(href)
                    quarter_names.append(quarter_name)
                    # Extract filing date.  Assumes it's in the next 'td'
                    date_cell = row.find_all('td')[5]
                    if date_cell:
                        filing_date_str = date_cell.get_text(strip=True)
                        try:
                            filing_date = datetime.strptime(filing_date_str, '%m/%d/%Y').date()  # Convert to date
                            filing_dates.append(filing_date)
                        except ValueError:
                            print(f"Error: Could not parse date string '{filing_date_str}'.  Setting to None.")
                            filing_dates.append(None)  # Set to None if parsing fails
                    else:
                        filing_dates.append(None)  # Add None if no date found
                
def get_top10_percentages(quarter_string):
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
# placeholder for the top holdings, top 50 from the current quarter (1/25)
    symbols = ['PLTR', 'VRSN', 'CORT', 'HOOD', 'SFM', 'UTHR', 'GILD', 'VRTX', 'EXEL', 'NVO', 'FNV.TO','ABNB', 'SPOT', 'K.TO', 'AVGO', 'CBOE', 'DASH', 'RBLX', 'GOOGL', 'META', 'FTNT', 'AMD', 'NTNX', 'TEAM', 'DOCU', 'ALSN', 'MNDY', 'DBX', 'NBIX', 'CL', 'TW', 'ZM', 'CVLT', 'WMT', 'ABBV', 'NVS', 'CCL', 'ETSY', 'APP', 'INCY', 'NOW', 'CME', 'ECL', 'HIMS', 'CRVL', 'RDDT', 'LI', 'NGG', 'WSM', 'CVX']

    # Filter the DataFrame for these symbols
    filtered_df = df[df['symbol'].isin(symbols)][['symbol', 'percentage']]

    if filtered_df.empty:
        print(f"None of the target symbols found in {quarter_string}")
        return None

    # Pivot to get symbols as columns, one row of percentages
    percentage_row = filtered_df.set_index('symbol').T
    percentage_row = percentage_row.reindex(columns=sorted(symbols))  # ensure consistent column order

    return percentage_row.reset_index(drop=True)

# calculate time taken to pull data
end_time = time.time()
elapsed_time = end_time - start_time



results = []

# Process each quarter
for q, name, date in zip(quarter_links, quarter_names, filing_dates):
    percentage_df = get_top10_percentages(q)
    if percentage_df is not None:
        row = percentage_df.iloc[0].to_dict()
        row['filing_date'] = date
        row['quarter'] = name
        results.append(row)

# Create a DataFrame from the list of row dictionaries
holdings_df = pd.DataFrame(results)
holdings_df = holdings_df.sort_values(by='filing_date').reset_index(drop=True)

# Optional: move the metadata columns to the front
cols = ['filing_date', 'quarter'] + [col for col in holdings_df.columns if col not in ['filing_date', 'quarter']]
holdings_df = holdings_df[cols]

script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, 'RenTech_top50_percentages.csv')
holdings_df.to_csv(csv_path, index=False)


print(f"Data pull completed in {elapsed_time:.2f} seconds.")
print(f"Data saved to {csv_path}")