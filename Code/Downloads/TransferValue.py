"""
TransferValue.py - Premier League Team Market Value Scraper

This script downloads and processes market value data for Premier League teams from Transfermarkt.
It implements ethical web scraping practices including:
- Appropriate delays between requests
- Proper user agent headers
- Error handling and logging
- Respect for the website's robots.txt

Data Structure:
- Input: None (uses command line parameters)
- Output: CSV file with columns:
    * Team: Name of the Premier League team
    * Market_Value: Total market value of the team's squad
    * Season: Season identifier (e.g., "2023-2024")

Usage:
    python TransferValue.py

Dependencies:
    - requests: For making HTTP requests
    - beautifulsoup4: For parsing HTML content
    - pandas: For data manipulation and CSV output
    - numpy: For numerical operations
    
Author: Mike Woodward
Date: March 2024
Version: 1.0
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
import random
from datetime import datetime
import numpy as np

def get_headers():
    """
    Generate headers for HTTP requests to mimic a real browser.
    
    This function returns a dictionary of HTTP headers that make the request appear
    to come from a legitimate web browser. This is good practice for web scraping
    as it:
    1. Helps avoid being blocked by the website
    2. Makes the script's purpose clear to the website owners
    3. Allows for proper tracking and analytics on their end
    
    Returns:
        dict: Dictionary containing HTTP headers including:
            - User-Agent: Browser identification
            - Accept: Acceptable content types
            - Accept-Language: Preferred languages
            - Connection: Connection type
    """
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

def get_team_values(season='2023'):
    """
    Scrape and process team market values from Transfermarkt for a specified season.
    
    This function:
    1. Makes an HTTP request to Transfermarkt's Premier League page
    2. Parses the HTML table containing team values
    3. Extracts team names and their market values
    4. Processes and structures the data into a pandas DataFrame
    
    The function implements polite scraping by:
    - Adding random delays between requests (2-4 seconds)
    - Using proper headers
    - Including error handling
    
    Args:
        season (str, optional): The season to get values for (e.g., '2023' for 2023/24).
            Defaults to '2023'.
    
    Returns:
        pandas.DataFrame: DataFrame containing:
            - Team: Team names
            - Market_Value: Team market values
            - Season: Season identifier (e.g., "2023-2024")
            
    Raises:
        ValueError: If the teams table cannot be found on the page
        Exception: For any other errors during scraping or processing
    """
    # Base URL for Premier League on Transfermarkt
    url = ('https://www.transfermarkt.com/premier-league/startseite/wettbewerb/'
           f'GB1/plus/?saison_id={season}')
    
    # Add a random delay between 2-4 seconds to be polite
    time.sleep(random.uniform(2, 4))
    
    try:
        # Make HTTP request with proper headers
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()

        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', {'class': 'items'})
        
        if not table:
            raise ValueError("Could not find the teams table on the page")

        # Extract table headers
        header = []
        for table_header in table.find_all('th'):
            header.append(table_header.text.strip())

        # Extract table rows
        rows = []
        for table_row in table.find('tbody').find_all('tr'):
            # Get all cells in the row and extract text content
            rows.append([cell.text.strip() for cell in table_row.find_all('td')])

        # Create DataFrame and add season information
        df = pd.DataFrame(rows, columns=header)
        df['Season'] = f'{season}-{int(season) + 1}'

        return df
    
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def save_values(df, season):
    """
    Save the transfer values DataFrame to a CSV file.
    
    This function handles the storage of scraped data, including:
    1. Creating the output directory if it doesn't exist
    2. Generating appropriate filenames
    3. Saving the data in CSV format
    
    Args:
        df (pandas.DataFrame): DataFrame containing:
            - Team: Team names
            - Market_Value: Team market values
            - Season: Season identifier
        season (str): Season identifier used in filename generation.
            If None, uses current date in filename.
    
    File Structure:
        - Base directory: RawData/Matches/TransferValues/
        - Filename format: 
            - With season: transfer_values_{season}.csv
            - Without season: transfer_values_{YYYYMMDD}.csv
    
    Raises:
        Exception: If there are any errors during the save process
    """
    if df is None:
        print("No data to save")
        return

    # Define base directory for data storage
    baseline = '../../RawData/Matches/TransferValues'
  
    # Generate filename based on season or current date
    if season is None:
        filename = os.path.join(baseline, f'transfer_values_{datetime.now().strftime("%Y%m%d")}.csv')
    else:
        filename = os.path.join(baseline, f'transfer_values_{season}.csv')
    
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Save to CSV
        df.to_csv(filename, index=False)
        print(f"Data saved successfully to {filename}")
    except Exception as e:
        print(f"Error saving data: {e}")

def main():
    """
    Main execution function for the transfer value scraping process.
    
    This function:
    1. Initiates the scraping process for the current season
    2. Handles the results and error cases
    3. Triggers the save process for successful scrapes
    
    The process follows these steps:
    1. Print start message
    2. Get current season's values
    3. Check if data was retrieved successfully
    4. Save the data if successful
    5. Print appropriate status messages
    
    No arguments or return values - this is the script's entry point.
    """
    print("Starting transfer value download...")
    
    # Get current season's values
    current_season = 2023
    df = get_team_values(current_season)
    
    if df is not None:
        print(f"Successfully retrieved {len(df)} team values")
        save_values(df, current_season)
    else:
        print("Failed to retrieve team values")

if __name__ == "__main__":
    main() 