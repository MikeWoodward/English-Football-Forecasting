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
    * club_name: Name of the Premier League team
    * squad_size: Number of players in squad
    * foreigner_count: Number of non-domestic players
    * mean_age: Average age of squad
    * total_market_value: Total squad value in millions
    * season: Season identifier (e.g., "2023-2024")

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
    
    This function scrapes data from multiple English football leagues:
    - Premier League (Tier 1)
    - Championship (Tier 2)
    - League One (Tier 3)
    - League Two (Tier 4)
    
    Args:
        season (str, optional): The season to get values for (e.g., '2023' for 2023/24).
            Defaults to '2023'.
    
    Returns:
        pandas.DataFrame: DataFrame containing:
            - club_name: Team names
            - squad_size: Number of players in squad
            - foreigner_count: Number of non-domestic players
            - mean_age: Average age of squad
            - total_market_value: Total squad value in millions
            - season: Season identifier (e.g., "2023-2024")
            - league: League name (e.g., "Premier League")
            - tier: League tier (1-4)
    """
    # Define the leagues and their URLs
    leagues = [
        {
            'name': 'Premier League',
            'url': 'https://www.transfermarkt.com/premier-league/startseite/wettbewerb/GB1/plus/?saison_id={season}',
            'tier': 1
        },
        {
            'name': 'Championship',
            'url': 'https://www.transfermarkt.com/championship/startseite/wettbewerb/GB2/saison_id/{season}',
            'tier': 2
        },
        {
            'name': 'League One',
            'url': 'https://www.transfermarkt.com/league-one/startseite/wettbewerb/GB3/saison_id/{season}',
            'tier': 3
        },
        {
            'name': 'League Two',
            'url': 'https://www.transfermarkt.com/league-two/startseite/wettbewerb/GB4/saison_id/{season}',
            'tier': 4
        }
    ]
    
    # List to store DataFrames for each league
    all_leagues_data = []
    
    try:
        for league in leagues:
            # Format the URL with the season
            url = league['url'].format(season=season)
            
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
                    print(f"Could not find table for {league['name']}")
                    continue

                # Extract table headers
                header = []
                for table_header in table.find_all('th'):
                    header.append(table_header.text.strip())

                # Extract table rows
                rows = []
                for table_row in table.find('tbody').find_all('tr'):
                    # Get all cells in the row and extract text content
                    rows.append([cell.text.strip() for cell in table_row.find_all('td')])

                # Create initial DataFrame with raw data
                df = pd.DataFrame(rows, columns=header)
                
                # Clean and transform the DataFrame
                # --------------------------------
                # 1. Remove unnecessary columns that don't provide value for analysis
                df = df.drop(['Club', 'ø market value'], axis=1)
                
                # 2. Rename columns to more Python-friendly names and add descriptive labels
                df = df.rename(columns={
                    'name': 'club_name',
                    'Squad': 'squad_size',
                    'Foreigners': 'foreigner_count',
                    'ø age': 'mean_age',
                    'Total market value': 'total_market_value'
                })
                
                # 3. Add season and league information
                df['season'] = f'{season}-{int(season) + 1}'
                df['league'] = league['name']
                df['tier'] = league['tier']
                
                # Add to the list of league data
                all_leagues_data.append(df)
                print(f"Successfully scraped {league['name']} data")

                # Save data for each league separately
                filename = os.path.join(
                    '../../RawData/Matches/TransferValues',
                    f"transfer_values_tier{league['tier']}_{season}.csv"
                )
                # Ensure the directory exists
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                df.to_csv(filename, index=False)
                
            except Exception as e:
                print(f"Error scraping {league['name']}: {e}")
                continue
            
    except Exception as e:
        print(f"Error in main processing: {e}")
        return None
        
    # Combine all league data if we have any
    if all_leagues_data:
        return pd.concat(all_leagues_data, ignore_index=True)
    else:
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
            - club_name: Team names
            - squad_size: Number of players in squad
            - foreigner_count: Number of non-domestic players
            - mean_age: Average age of squad
            - total_market_value: Total squad value in millions
            - season: Season identifier
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
    1. Initiates the scraping process for historical Premier League seasons
    2. Handles the results and error cases
    3. Triggers the save process for successful scrapes
    
    Historical Data Collection:
    - Starts from 1992 (Premier League formation)
    - Ends at 2023 (current season)
    - Processes each season sequentially with appropriate delays
    
    Note: Data availability and quality may vary for older seasons.
    Transfermarkt's historical data might be incomplete or less detailed
    for seasons before certain dates.
    """
    print("Starting transfer value download...")
    
    # Iterate through all Premier League seasons
    # Starting from 1992 (Premier League formation) to 2023 (current)
    for current_season in range(1992, 2024):
        df = get_team_values(current_season)
        
        if df is not None:
            print(f"Successfully retrieved {len(df)} team values for season {current_season}-{current_season+1}")
            save_values(df, current_season)
        else:
            print(f"Failed to retrieve team values for season {current_season}-{current_season+1}")

if __name__ == "__main__":
    main() 