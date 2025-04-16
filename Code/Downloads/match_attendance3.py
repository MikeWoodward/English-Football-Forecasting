"""
match_attendance3.py
------------------

This script scrapes football match URLs from worldfootball.net for English football leagues.
It collects match report URLs for historical match data from 1892 to present day.

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

Author: Mike Woodward
Date: March 2024
"""

# Import required libraries
import requests  # For making HTTP requests to web pages
import time     # For adding delays between requests
from bs4 import BeautifulSoup  # For parsing HTML content of web pages

# Only execute the following code if this script is run directly (not imported)
if __name__ == "__main__":
    # Create a list of football seasons from 1888 to 2024
    # Format: ['1888-1889', '1889-1890', ..., '2023-2024']
    # 1888 is when the Football League was founded
    season_list = [f'{season}-{season + 1}' for season in range(1888, 2024)]
    
    # Define list of English football leagues to scrape
    # These are the current names of the top 5 tiers of English football
    league_list = [
        "premier-league",      # Tier 1: Premier League (1992-present)
        "championship",        # Tier 2: EFL Championship
        "league-one",         # Tier 3: EFL League One
        "league-two",         # Tier 4: EFL League Two
        "national-league"     # Tier 5: National League
    ]  
    
    # Initialize empty list to store all match URLs we find
    match_urls = []

    # Set up request headers with a user agent
    # This makes our requests look like they're coming from a web browser
    # Helps prevent being blocked by the website's security measures
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    } 

    # Define the base URL for the website we're scraping
    baseline_url = "https://www.worldfootball.net"

    # Process each combination of season and league
    for season in season_list:
        for league in league_list:
            # Construct the full URL for this league and season
            # Format: https://www.worldfootball.net/all_matches/eng-{league}-{season}/
            url = baseline_url + f"/all_matches/eng-{league}-{season}/"
            
            try:
                # Make HTTP GET request to the URL
                print(f"Requesting data for {league} {season}...")
                response = requests.get(url, headers=headers)
                
                # Check if the request was successful (status code 200)
                if response.status_code == 200:
                    # Parse the HTML content of the page
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find all tables with class "standard_tabelle"
                    # This is the class used for the match results table
                    standard_tables = soup.find_all('table', class_="standard_tabelle")
                    
                    # If no tables found, log message and continue to next combination
                    if not standard_tables:
                        print(f"No match data found for {league} {season}")
                        continue
                    
                    # Process the first table (main matches table)
                    # Look through each row for match report links
                    for row in standard_tables[0].find_all('tr'):
                        for column in row.find_all('td'):
                            # Find any links in the column
                            a = column.find('a')
                            if a and '/report/' in a.get('href', ''):
                                # Construct full match URL and add to list
                                match_url = baseline_url + a['href']
                                match_urls.append(match_url)
                                print(f"Found match URL: {match_url}")
                else:
                    print(f"Failed to load {url} - Status code: {response.status_code}")
                
                # Add a delay between requests to be polite to the server
                # This helps prevent overwhelming the server with too many rapid requests
                time.sleep(2)
                
            except requests.RequestException as e:
                print(f"Error requesting {url}: {str(e)}")
                continue

    # Save all collected match URLs to a text file
    # URLs are saved one per line in the specified directory
    output_path = '../../RawData/Matches/MatchURLs/match_urls.txt'
    print(f"\nSaving {len(match_urls)} URLs to {output_path}")
    
    with open(output_path, 'w') as f:
        for match_url in match_urls:
            f.write(match_url + '\n')

    # Print final summary
    print(f"\nScript completed. Found {len(match_urls)} total match URLs")
