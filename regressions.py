import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
import statsmodels.api as sm


df = pd.read_csv(r'C:\\Users\\Nicolas\\OneDrive\\GitHub\\berkshireapple\\berkshire_top10_percentages.csv')
df["filing_date"] = pd.to_datetime(df["filing_date"], format="%m/%d/%Y")
priceDelta = df

# Format Holdings changes as log percentages
df_pct = df.copy()
df_pct.iloc[:, 2:] = df.iloc[:, 2:].pct_change(fill_method=None) * 100
df_log = df_pct.copy()
df_pct.iloc[:, 2:] = np.log10(1 + df_pct.iloc[:, 2:] / 100)
df_pct = df_pct.round(2)

# Find stock price deltas
tickers = df.columns[2:]

#Download all data for stocks
historical_data = {}
for ticker in tickers:
    if ticker.strip() == "":
        continue
    all_data = yf.download(tickers.tolist(), start='2013-01-01', end='2024-12-31')
    historical_data[ticker] = all_data

# Parse stock data for deltas on each filing date
open_prices = all_data['Open']
close_prices = all_data['Close']

# Create new DataFrame to store % price changes on filing days
price_change_df = df[['filing_date', 'quarter']].copy()

# Calculate % change for each ticker on each filing date
for ticker in tickers:
    changes = []
    for date in df['filing_date']:
        try:
            date_next_day = pd.to_datetime(date) + pd.Timedelta(days=1)
            date_prev_day = pd.to_datetime(date) - pd.Timedelta(days=1)
            open_price = open_prices.at[date_prev_day, ticker]
            close_price = close_prices.at[date_next_day, ticker]
            pct_change = ((close_price - open_price) / open_price) * 100
        except KeyError:
            pct_change = None  # or float('nan')
        changes.append(pct_change)
    price_change_df[ticker] = changes

print(price_change_df.head())


# Regressions
merged_df = pd.merge(price_change_df, df_pct, on=['filing_date', 'quarter'], suffixes=('_price', '_holding'))
numeric_cols = merged_df.select_dtypes(include=['float64', 'int64']).columns

# Replace NaN values in numeric columns with the mean of each column
merged_df[numeric_cols] = merged_df[numeric_cols].fillna(merged_df[numeric_cols].mean())
# Perform regression for each stock ticker
results = {}

for ticker in price_change_df.columns[2:]:  # Starting from the 3rd column to skip 'filing_date' and 'quarter'
    X = merged_df[[f'{ticker}_holding']]  # Independent variable (holdings)
    y = merged_df[f'{ticker}_price']  # Dependent variable (stock prices)
    
    # Add constant to the independent variable (for intercept)
    X = sm.add_constant(X)
    
    # Run OLS regression
    model = sm.OLS(y, X).fit()
    
    # Store the results
    results[ticker] = model.summary()

# Print the regression results for each stock ticker
for ticker, result in results.items():
    print(f"Regression results for {ticker}:")
    print(result)
    print("\n")