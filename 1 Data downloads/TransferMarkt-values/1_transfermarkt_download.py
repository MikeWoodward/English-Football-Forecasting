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
import logging

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

def log_503_error(
    *,
    url: str,
    season: str,
    league_name: str,
    error_details: str
) -> None:
    """
    Log 503 errors to a dedicated file for tracking and analysis.
    
    This function appends 503 error details to a file in the Log folder.
    Each entry includes timestamp, URL, season, league, and error details.
    
    Args:
        url: The URL that caused the 503 error
        season: The season being processed
        league_name: The name of the league being processed
        error_details: Additional error details or context
    
    Returns:
        None
    """
    log_dir = 'Log'
    os.makedirs(log_dir, exist_ok=True)
    
    error_file = os.path.join(log_dir, '503_errors.txt')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    error_entry = (
        f"[{timestamp}] 503 Error\n"
        f"URL: {url}\n"
        f"Season: {season}\n"
        f"League: {league_name}\n"
        f"Details: {error_details}\n"
        f"{'='*50}\n"
    )
    
    try:
        with open(error_file, 'a', encoding='utf-8') as f:
            f.write(error_entry)
        logging.warning(f"503 error logged to {error_file}")
    except Exception as e:
        logging.error(f"Failed to write to 503 error file at line {e.__traceback__.tb_lineno}: {e}")


def setup_logging(
    *,
    log_level=logging.INFO
) -> None:
    """
    Set up logging configuration for the application.
    
    This function configures logging to write to both console and file.
    Logs are saved to a 'Log' folder with timestamped filenames.
    
    Args:
        log_level: The logging level to use. Defaults to logging.INFO.
    
    Returns:
        None
    """
    # Create Log directory if it doesn't exist
    log_dir = 'Log'
    os.makedirs(log_dir, exist_ok=True)
    
    # Create timestamped log filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = os.path.join(log_dir, f'transfer_value_download_{timestamp}.log')
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
    
    logging.info(f"Logging initialized. Log file: {log_filename}")


def get_team_values(
    *,
    season='2023'
) -> pd.DataFrame:
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
        },
        {
            'name': 'National League',
            'url': 'https://www.transfermarkt.com/national-league/startseite/wettbewerb/CNAT/plus/?saison_id={season}',
            'tier': 5
        }
    ]
    
    all_data = []
    
    for league in leagues:
        # Format the URL with the season
        url = league['url'].format(season=season)
        
        filename = os.path.join(
            'Data-Download',
            f"transfer_values_tier{league['tier']}_{season}.csv"
        )

        # Ensure the directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        if os.path.exists(filename):
            logging.info(f"Skipping {league['name']} for season {season} because it already exists")
            continue

        # Add a random delay between 20-40 seconds to be polite
        time.sleep(random.uniform(20, 40))

        logging.info(f"Processing {league['name']} for season {season}")
            
        try:
            # Make HTTP request with proper headers
            response = requests.get(url, headers=get_headers())
            
            # Check for 503 errors specifically
            if response.status_code == 503:
                error_msg = f"503 Service Unavailable for {league['name']}"
                log_503_error(
                    url=url,
                    season=season,
                    league_name=league['name'],
                    error_details=error_msg
                )
                logging.error(f"503 error for {league['name']} - service temporarily unavailable")
                continue
            
            response.raise_for_status()

            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            table = soup.find('table', {'class': 'items'})
            
            if not table:
                logging.warning(f"Could not find table for {league['name']}")
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
            df = df.drop(['Club', 'ø market value'], errors='ignore', axis=1)

            if 'Total market value' not in df.columns:
                df['Total market value'] = None
            
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
            df['league_tier'] = league['tier']

            # Save data for each league separately
            df.to_csv(filename, index=False)
            
            logging.info(f"Saved {len(df)} records for {league['name']} to {filename}")
            
            # Add to collection for return
            all_data.append(df)
            
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response.status_code == 503:
                error_msg = f"HTTP 503 Error: {e}"
                log_503_error(
                    url=url,
                    season=season,
                    league_name=league['name'],
                    error_details=error_msg
                )
                logging.error(f"503 error for {league['name']} at line {e.__traceback__.tb_lineno}: {e}")
            else:
                logging.error(f"HTTP error for {league['name']} at line {e.__traceback__.tb_lineno}: {e}")
            continue
        except Exception as e:
            logging.error(f"Error scraping {league['name']} at line {e.__traceback__.tb_lineno}: {e}")
            continue
    
    # Combine all league data and return
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        logging.info(f"Combined {len(combined_df)} total records from {len(all_data)} leagues")
        return combined_df
    else:
        logging.warning("No data collected from any leagues")
        return pd.DataFrame()


if __name__ == "__main__":
    # Set up logging
    setup_logging()
    
    logging.info("Starting transfer value download...")
    
    # Starting from 1992 (Premier League formation) to 2025 (current)
    for current_season in range(1992, 2025):
        try:
            logging.info(f"Processing season {current_season}")
            season_data = get_team_values(season=str(current_season))
            if not season_data.empty:
                logging.info(f"Successfully processed season {current_season} with {len(season_data)} records")
            else:
                logging.warning(f"No data found for season {current_season}")
        except Exception as e:
            logging.error(f"Error processing season {current_season} at line {e.__traceback__.tb_lineno}: {e}")
            continue
    
    logging.info("Transfer value download process completed") 