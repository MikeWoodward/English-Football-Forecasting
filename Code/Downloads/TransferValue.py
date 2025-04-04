"""
This script downloads transfer market values for Premier League teams from Transfermarkt.
It uses web scraping techniques with proper delays and user agent headers to be respectful
of the website's terms of service.

The data is saved in a structured format for further analysis.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
import random
from datetime import datetime
import numpy as np
from io import StringIO

def get_headers():
    """
    Returns headers for HTTP requests to mimic a real browser.
    This is good practice for web scraping.
    """
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

def get_team_values(season='2023'):
    """
    Scrapes team market values from Transfermarkt for the specified season using pandas read_html.
    Handles complex table structure with colspan headers.
    
    Args:
        season (str): The season to get values for (e.g., '2023' for 2023/24)
    
    Returns:
        pandas.DataFrame: DataFrame containing team names and their market values
    """
    # Base URL for Premier League on Transfermarkt
    url = ('https://www.transfermarkt.com/premier-league/startseite/wettbewerb/'
           f'GB1/plus/?saison_id={season}')
    
    # Add a random delay between 2-4 seconds
    time.sleep(random.uniform(2, 4))
    
    try:
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()

        # First use BeautifulSoup to analyze the table structure
        soup = BeautifulSoup(response.text, 'html.parser')
        table_element = soup.find('table', {'class': 'items'})
        
        if not table_element:
            raise ValueError("Could not find the teams table on the page")

        # Extract team names and market values directly
        teams = []
        values = []
        
        # Find all team rows
        for row in table_element.find_all('tr')[1:]:  # Skip header row
            team_cell = row.find('td', {'class': 'hauptlink'})
            value_cell = row.find('td', {'class': 'rechts'})
            
            if team_cell and value_cell:
                team_name = team_cell.text.strip()
                market_value = value_cell.text.strip()
                
                if team_name and market_value:
                    teams.append(team_name)
                    values.append(market_value)
        
        # Create a new DataFrame with clean data
        result_df = pd.DataFrame({
            'Team': teams,
            'Market_Value': values,
            'Season': f'{season}-{int(season) + 1}'
        })
        
        return result_df
    
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def save_values(df, season):
    """
    Saves the transfer values DataFrame to a CSV file.
    
    Args:
        df (pandas.DataFrame): DataFrame containing the transfer values
        filename (str, optional): Name of the file to save to. If None, generates a default name.
    """
    if df is None:
        print("No data to save")
        return

    baseline = '../../RawData/Matches/TransferValues'
  
    if season is None:
        filename = os.path.join(baseline, f'transfer_values_{datetime.now().strftime("%Y%m%d")}.csv')
    else:
        filename = os.path.join(baseline, f'transfer_values_{season}.csv')
    try:
        df.to_csv(filename, index=False)
        print(f"Data saved successfully to {filename}")
    except Exception as e:
        print(f"Error saving data: {e}")

def main():
    """
    Main function to execute the transfer value scraping process.
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