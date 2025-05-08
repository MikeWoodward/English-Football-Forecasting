"""
match_attendance3.py
------------------

This script scrapes football match URLs from worldfootball.net for English football
leagues. It collects match report URLs for historical match data from 1892 to
present day.

Purpose:
    - Collects match report URLs for English football leagues
    - Covers multiple tiers of English football (Championship to National League)
    - Creates a comprehensive database of historical match data URLs

Process:
    1. Generates combinations of seasons (1892-2024) and leagues
    2. For each combination, scrapes the season's match listing page
    3. Extracts URLs for individual match reports
    4. Saves all discovered URLs to a text file

Output:
    - Creates a text file at '../../RawData/Matches/MatchURLs/match_urls.txt'
    - Each line contains one match report URL
    
Notes:
    - Uses polite scraping practices (delays between requests)
    - Includes error handling for failed requests
    - Provides progress updates during execution
    
Dependencies:
    - requests: For making HTTP requests
    - beautifulsoup4: For parsing HTML content
    - time: For implementing delays between requests
    - logging: For proper logging of script execution

Author: Mike Woodward
Date: March 2024
"""

# Import required libraries
import requests  # For making HTTP requests to web pages
import time     # For adding delays between requests
import logging  # For proper logging
import pandas as pd  # For creating dataframes
from bs4 import BeautifulSoup  # For parsing HTML content of web pages
from pathlib import Path  # For handling file paths
from typing import List, Optional, Dict, Any, Union
from bs4.element import Tag
from datetime import datetime  # For date formatting

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('match_attendance.log')
    ]
)

# Define the base URL for the website we're scraping
BASELINE_URL = "https://www.worldfootball.net"

def get_match_url(standard_tables: List[Tag], match_urls: List[str]) -> Optional[str]:
    """
    Extract match report URL from the first standard table found.
    
    Args:
        standard_tables: List of BeautifulSoup table objects containing match data
        match_urls: List to store found match URLs
        
    Returns:
        Boolean indicating if any match URLs were found
        
    Raises:
        IndexError: If standard_tables is empty
        AttributeError: If table structure is unexpected
    """
    try:
        # Flag to track if any match URLs were found
        found = False
        
        # Look through each row for match report links
        for row in standard_tables[0].find_all('tr'):
            for column in row.find_all('td'):
                # Find any links in the column
                a = column.find('a')
                if a and '/report/' in a.get('href', ''):
                    # Construct full match URL and add to list
                    match_urls.append(BASELINE_URL + a['href'])
                    found = True
        return found
    except (IndexError, AttributeError) as e:
        logging.error(f"Error processing table: {str(e)}")
        return False

def get_match_results(
    standard_tables: List[Tag],
    season: str,
    league_tier: int,
    league_name: str
) -> Optional[pd.DataFrame]:
    """
    Extract match results from the first standard table found.
    
    Args:
        standard_tables: List of BeautifulSoup table objects containing match data
        season: The season in format 'YYYY-YYYY'
        league_tier: The tier of the league (1-5)
        league_name: The name of the league
        
    Returns:
        DataFrame containing match results if found, None otherwise. The DataFrame
        includes columns for season, league_tier, match_date, match_day,
        match_time, home_club, away_club, home_goals, away_goals, attendance,
        and venue.
        
    Raises:
        IndexError: If standard_tables is empty
        AttributeError: If table structure is unexpected
    """
    results: List[Dict[str, Any]] = []
    rows = standard_tables[0].find_all('tr')

    # Initialize date variable to handle cases where date might be missing
    html_date = ""
    
    for row in rows:
        columns = row.find_all('td')
        if len(columns) != 7:
            continue

        # Get date of match - transform from dd/mm/yyyy to yyyy-mm-dd       
        html_date = (columns[0].text.strip() 
                if columns[0].text.strip() != "" else html_date) 
        
        # Correct known date error in the data
        if html_date == "00/00/1939":
            html_date = "25/08/1939"
            
        # Convert date to standard format
        date = datetime.strptime(html_date, "%d/%m/%Y").strftime("%Y-%m-%d")
        
        # Extract day of week from date
        match_day = datetime.strptime(date, "%Y-%m-%d").strftime("%A")
        
        # Extract team names and scores
        home_club = columns[2].text.strip()
        away_club = columns[4].text.strip()
        score = columns[5].text.strip().split(":")
        home_goals = score[0]   
        away_goals = score[1]
        
        # Create match record
        results.append({
            'season': season,
            'league_tier': league_tier,
            'match_date': date,
            'match_day': match_day,
            'match_time': None,
            'home_club': home_club,
            'away_club': away_club,
            'home_goals': home_goals,
            'away_goals': away_goals,
            'attendance': None,
            'venue': None,
        })

    return pd.DataFrame(results) if results else None

# Only execute the following code if this script is run directly (not imported)
if __name__ == "__main__":
    try:
        # Define list of English football leagues to scrape
        # These are the current names of the top 5 tiers of English football
        # Each league has a start year when it was founded or reorganized
        leagues: List[Dict[str, Union[str, int]]] = [
            {'name': 'premier-league', 'league_tier': 1, 'start_year': 1888},
            {'name': 'championship', 'league_tier': 2, 'start_year': 1892},
            {'name': 'league-one', 'league_tier': 3, 'start_year': 1999},
            {'name': 'league-two', 'league_tier': 4, 'start_year': 1999},
            {'name': 'national-league', 'league_tier': 5, 'start_year': 2002}
        ]  
        
        # Initialize empty list to store all match URLs we find
        match_urls: List[str] = []

        # Set up request headers with a user agent
        # This makes our requests look like they're coming from a web browser
        # Helps prevent being blocked by the website's security measures
        headers: Dict[str, str] = {
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/122.0.0.0 Safari/537.36'
            )
        } 

        # Process each league and its valid seasons
        for league in leagues:
            # Generate seasons from league's start year to present
            for season in [str(x) + '-' + str(x + 1) 
                          for x in range(league['start_year'], 2024)]:
                # Construct the full URL for this league and season
                url = (f"{BASELINE_URL}/all_matches/"
                      f"eng-{league['name']}-{season}/")
                
                try:
                    # Make HTTP GET request to the URL
                    logging.info(
                        f"Requesting data for {league['name']} {season}..."
                    )
                    response = requests.get(url, headers=headers)
                    
                    # Check if the request was successful (status code 200)
                    if response.status_code == 200:
                        # Parse the HTML content of the page
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Find all tables with class "standard_tabelle"
                        standard_tables = soup.find_all(
                            'table', 
                            class_="standard_tabelle"
                        )
                        
                        # If no tables found, log message and continue
                        if not standard_tables:
                            logging.warning(
                                f"No match data found for {league['name']} "
                                f"{season}"
                            )
                            continue
                        
                        # Process the first table (main matches table)
                        # Try to find match URLs first
                        found_urls = get_match_url(standard_tables, match_urls)  

                        # If no URLs found, try to get match results
                        if not found_urls:
                            results = get_match_results(
                                standard_tables, 
                                season, 
                                league['league_tier'], 
                                league['name']
                            )
                            if results is not None:
                                output_file = (
                                    f"../../RawData/Matches/Attendance4/"
                                    f"attendance4_{league['name']}_{season}.csv"
                                )
                                results.to_csv(output_file, index=False)  
                            logging.warning(
                                f"No match URL found for {league['name']} "
                                f"{season} - saving score only"
                            )
                    else:
                        logging.error(
                            f"Failed to load {url} - "
                            f"Status code: {response.status_code}"
                        )
                    
                    # Add a delay between requests to be polite to the server
                    time.sleep(2)
                    
                except requests.RequestException as e:
                    logging.error(f"Error requesting {url}: {str(e)}")
                    continue

        # Save all collected match URLs to a text file
        output_path = Path('../../RawData/Matches/MatchURLs/match_urls.txt')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logging.info(f"\nSaving {len(match_urls)} URLs to {output_path}")
        
        with open(output_path, 'w') as f:
            for match_url in match_urls:
                f.write(match_url + '\n')

        # Print final summary
        logging.info(
            f"\nScript completed. Found {len(match_urls)} total match URLs"
        )

    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        raise
