"""
English Football League Tables Matches Module.

This module provides functionality for retrieving match data from the
English Football League Tables website. It reads day URLs from a CSV file
and retrieves all league matches played on each specified day.
"""

# Standard library imports
import logging  # For logging operations and debugging
import os  # For file and directory operations
import sys  # For system-specific parameters and functions
from typing import Dict, List, Any  # For type hints
import time  # For adding delays between requests
import random  # For random delays to avoid overwhelming the server
from datetime import datetime  # For date parsing and formatting

# Third-party imports
import pandas as pd  # For data manipulation and CSV operations
import requests  # For making HTTP requests to web pages
from bs4 import BeautifulSoup  # For parsing HTML content


def read_day_urls(*, file_path: str) -> pd.DataFrame:
    """
    Read day URLs from a CSV file into a pandas DataFrame.
    
    This function reads the specified CSV file containing day URLs
    and returns the data as a pandas DataFrame for further processing.
    
    Args:
        file_path: Path to the CSV file containing day URLs.
        
    Returns:
        pandas DataFrame containing the day URL data.
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist.
        pd.errors.EmptyDataError: If the CSV file is empty.
        pd.errors.ParserError: If the CSV file is malformed.
    """
    try:
        # Read the CSV file into a pandas DataFrame
        day_urls_df = pd.read_csv(file_path)
        # Log successful file read with basic information
        logging.info(
            f"Successfully read {len(day_urls_df)} rows from {file_path}"
        )
        return day_urls_df
    except FileNotFoundError:
        # Handle case where the specified file doesn't exist
        logging.error(f"File not found: {file_path}")
        raise
    except pd.errors.EmptyDataError:
        # Handle case where CSV file exists but is empty
        logging.error(f"CSV file is empty: {file_path}")
        raise
    except pd.errors.ParserError as err:
        # Handle case where CSV file is malformed or has parsing errors
        logging.error(f"Error parsing CSV file {file_path}: {err}")
        raise
    except Exception as err:
        # Catch any other unexpected errors during file reading
        logging.error(f"Unexpected error reading file {file_path}: {err}")
        raise


def get_day_url_html(*, day_url: str, date: str) -> str:
    """
    Retrieve HTML content for a specific day URL.
    
    This function checks if the HTML page for a given date has already been
    downloaded. If it exists, it reads the file. If not, it downloads the
    page from the URL and saves it to a file.
    
    Args:
        day_url: URL of the day's matches page.
        date: Date string used for file naming.
        data_path: Base path for storing HTML files.
        
    Returns:
        HTML content as a string.
        
    Raises:
        requests.RequestException: If the HTTP request fails.
        OSError: If there are file I/O errors.
    """
    # Define headers to prevent caching and mimic a real browser
    # These headers help avoid being blocked by the website's anti-bot measures
    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/91.0.4472.124 Safari/537.36'),
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        'Accept': ('text/html,application/xhtml+xml,application/xml;q=0.9,'
                  'image/webp,*/*;q=0.8'),
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    # File name to save data to - uses date as filename for easy identification
    file_name = os.path.join('HTML', f'{date}.html')
    
    # Sleep for a random interval of 5 to 12 seconds to avoid overwhelming
    # the server. This is a courtesy to the website and helps prevent IP
    # blocking
    time.sleep(random.randint(5, 12))
    # Load the day page using HTTP GET request with headers
    day_page = requests.get(day_url, headers=headers, timeout=20)
    # Raise exception for HTTP errors (4xx, 5xx status codes)
    day_page.raise_for_status()
    html = day_page.text  # Extract the HTML content from the response
    # Save the HTML to a html file for future use and to avoid re-downloading
    with open(file_name, 'w') as f:
        f.write(html)
    
    return html


def process_day_urls(*, day_urls_df: pd.DataFrame,
                     flag: str) -> List[Dict[str, Any]]:
    """
    Process each day URL to retrieve match data.
    
    This function iterates through each row in the DataFrame containing
    day URLs and calls get_matches for each URL to retrieve the
    corresponding match data.
    
    Args:
        day_urls_df: pandas DataFrame containing day URL data.
        data_path: Path to save intermediate CSV files.
        flag: String identifier for the current processing run.
        
    Returns:
        List of dictionaries containing all retrieved match data.
        
    Raises:
        ValueError: If the DataFrame is empty or missing required columns.
    """
    # Check if DataFrame is empty to avoid processing errors
    if day_urls_df.empty:
        logging.warning("DataFrame is empty - no day URLs to process")
        return []
    # Initialize list to store all match data from all processed days
    all_matches = []
    # Process each day URL in the DataFrame
    for index, row in day_urls_df.iterrows():
        try:
            # Extract data from the current row
            date = row['date']  # Date of the matches
            season = row['season']  # Football season (e.g., 1888-89)
            day_url = row['match_url']  # URL to the day's matches page
            
            # Check if HTML file already exists to avoid re-downloading
            file_name = os.path.join('HTML', f'{date}.html')
            if os.path.exists(file_name):
                # If it has been downloaded, read it in from the saved file
                with open(file_name, 'r') as f:
                    html = f.read()
            # Otherwise, get the page and save it for future use
            else:
                # Get HTML content for the day URL by downloading from the web
                html = get_day_url_html(
                    day_url=day_url,
                    date=date,
                )
            
            # Parse the HTML content using BeautifulSoup for easy navigation
            day_soup = BeautifulSoup(html, 'html.parser')
            # Check the date in the html agrees with the date in the url and
            # the date. Extract date from URL (last 15 characters, then last
            # 10 for YYYY-MM-DD format)
            url_date = day_url[-15:-5]
            # Get the HTML date and convert it from "Saturday 1888-09-15" to
            # "YYYY-MM-DD". Note there are all kinds of weird errors we're
            # trying to handle here. The website has various formatting
            # inconsistencies that need to be cleaned up
            html_date = (day_soup
                         .find('h1')  # Find the main heading which contains the date
                         .text
                         .replace('Easter', '')  # Remove Easter references
                         .replace('Good', '')  # Remove Good Friday references
                         .replace('Wenesday', 'Wednesday')  # Fix common typos
                         .replace('Wednessday', 'Wednesday')
                         .replace('Wedneday', 'Wednesday')
                         .replace('Wednsday', 'Wednesday')
                         .replace('Monsday', 'Monday')
                         .replace('Sunday S', 'Sunday ')  # Fix spacing issues
                         .replace('Monday1996', 'Monday 1996')  # Fix missing space
                         .strip())  # Remove leading/trailing whitespace
            # Split the date string to separate day name from date
            date_split = html_date.split(' ')
            if len(date_split) == 1:
                # If only one part, it's just the date
                date_only = date_split[0]
            else:
                # If multiple parts, the second part is the date
                date_only = date_split[1]
            # Handle different date formats found in the HTML
            # First case, date only in YYYY-MM-DD format
            if len(html_date) == 10:
                html_date = datetime.strptime(
                    html_date, '%Y-%m-%d'
                ).strftime('%Y-%m-%d')
            # Second case, date in YY-MM-DD format (2-digit year)
            elif len(date_only) == 8:
                html_date = datetime.strptime(
                    date_only, '%y-%m-%d'
                ).strftime('%Y-%m-%d')
            # Third case, date in "Day YYYY-MM-DD" format
            else:
                html_date = datetime.strptime(
                    html_date, '%A %Y-%m-%d'
                ).strftime('%Y-%m-%d')
            # Raise a warning for inconsistent dates between URL, HTML, and CSV
            # This helps identify data quality issues
            if not (url_date == html_date == date):
                logging.warning(
                    f"Date mismatch: url_date: {url_date}, "
                    f"html_date: {html_date}, date: {date}"
                )
                continue  # Skip this day if dates don't match

            # Find all tables on the page that might contain match data
            tables = day_soup.find_all('table')
            # Iterate through each table to find match data
            for table_index, table in enumerate(tables):
                # Find rows with specific CSS classes that indicate match data
                # These classes are used by the website to style different
                # types of matches
                matches = table.find_all(
                    "tr", {"class": ["pink", "blue", "turq", "lblue"]}
                )
                if len(matches) == 0:
                    continue  # Skip tables without match data
                # Extract league name from table header
                # Note: Web page structure can be inconsistent, requiring
                # fallback logic
                if not table.find("th"):
                    # Handle case where table header is missing - try to get
                    # league name from previous table
                    if table_index == 0:
                        raise ValueError("No league name found.")
                    # Look for league name in header cells of previous table
                    # These classes indicate header cells for different league
                    # divisions
                    columns = tables[table_index - 1].find_all(
                        "td", {"class": ["h1day", "h2day", "h3day", "h4day"]}
                    )
                    if len(columns) != 1:
                        raise ValueError("Could not get unique league name.")
                    league = columns[0].text.strip()
                else:
                    # Extract league name from table header, handling
                    # extraneous whitespace. Split by newlines and take first
                    # part to get clean league name
                    league = table.find("th").text.strip().split('\n')[0]
                # Skip tables that are just notes rather than match data
                if league == "Notes":
                    continue
                # Process each match row in the current table
                for match in matches:
                    # Extract all table cells from the match row
                    columns = match.find_all('td')
                    # Skip rows that don't have enough columns for complete
                    # match data. Need at least 6 columns: home team, home
                    # score, away score, away team, venue, attendance
                    if len(columns) < 6:
                        continue
                    # Extract home and away team scores
                    # Handle cases where games were postponed or cancelled
                    # (non-numeric scores)
                    home_score = columns[1].text.strip()
                    away_score = columns[2].text.strip()
                    # Only process matches with valid numeric scores
                    if not (home_score.isdigit() and away_score.isdigit()):
                        continue  # Skip matches without valid numeric scores
                    # Create match data dictionary with all extracted
                    # information
                    all_matches.append({
                        'season': season,  # Football season (e.g., 1888-89)
                        'date': date,  # Match date in YYYY-MM-DD format
                        'league_name': league,  # League/division name
                        'home_team': ' '.join(
                            columns[0].text.strip().split()
                        ),  # Home team name (clean up whitespace)
                        'away_team': ' '.join(
                            columns[3].text.strip().split()
                        ),  # Away team name (clean up whitespace)
                        'home_score': home_score,  # Home team's score
                        'away_score': away_score,  # Away team's score
                        'venue': columns[4].text.strip(),  # Stadium/venue name
                        'attendance': columns[5].text.strip().replace(
                            ',', ''
                        ),  # Attendance (remove commas)
                    })
                    # Save the matches found so far to a CSV file every 10000
                    # matches. This provides a backup in case the process is
                    # interrupted
                    if len(all_matches) % 10000 == 0:
                        file_name = os.path.join(
                            'Progress',
                            f'matches_{flag}_{len(all_matches)}.csv'
                        )
                        pd.DataFrame(all_matches).to_csv(
                            file_name,
                            index=False
                        )
        except Exception as err:
            # Log error but continue processing other URLs to avoid complete
            # failure. This ensures that one bad day doesn't stop the entire
            # process
            logging.error(
                f"Error processing day URL at row {index}, url: {day_url}: "
                f"{err}\nDate: {date}, Season: {season}\n"
                f"Code line {sys.exc_info()[2].tb_lineno}"  # Include line number for debugging
            )
            continue  # Continue with next day URL
    # Log final count of matches retrieved for monitoring progress
    logging.info(f"Total matches retrieved: {len(all_matches)}")
    return all_matches


if __name__ == "__main__":
    # Flag indicating run conditions (e.g., "forward" for forward processing)
    # This can be used to identify different processing runs
    start_point = 0  # Starting row index in the CSV file
    flag = str(start_point)  # Convert to string for use in filenames
    # Configure logging with both file and console output
    # This provides both persistent logs and immediate feedback
    log_file_name = os.path.join(
        'Logs', f'englishfootballleaguetables_matches_{flag}.log'
    )
    logging.basicConfig(
        level=logging.INFO,  # Log all messages at INFO level and above
        format='%(asctime)s - %(levelname)s - %(message)s',  # Include timestamp and log level
        handlers=[
            logging.FileHandler(log_file_name),  # Save logs to file
            logging.StreamHandler()  # Also display logs in console
        ]
    )

    # Define the path to the CSV file containing day URLs
    csv_file_path = os.path.join('Day URLs', 'day_urls.csv')
    try:
        # Check if the input CSV file exists before attempting to read it
        if not os.path.exists(csv_file_path):
            logging.error(f"CSV file not found: {csv_file_path}")
            logging.info("Please ensure the file exists and the path is correct")
            sys.exit(1)  # Exit with error code 1
        # Read the day URLs from the CSV file into a DataFrame
        # Use iloc to start from the specified start_point (allows resuming
        # from where we left off)
        day_urls_df = read_day_urls(file_path=csv_file_path).iloc[start_point:]
        # Process each day URL to retrieve match data
        all_matches = process_day_urls(
            day_urls_df=day_urls_df,
            flag=flag
        )
        # Save final results to CSV file, removing any duplicate matches
        # Duplicates can occur if the same match appears in multiple tables
        matches_file_name = os.path.join(
            'Data', f'englishfootballleaguetables_matches_{flag}.csv'
        )
        pd.DataFrame(all_matches).drop_duplicates().to_csv(
            matches_file_name,
            index=False  # Don't include DataFrame index in output
        )
        logging.info(
            f"Successfully processed {len(all_matches)} total matches"
        )
    except Exception as err:
        # Log any unexpected errors and re-raise to stop execution
        # This ensures we don't silently fail and helps with debugging
        logging.error(f"Error in main execution: {err}")
        raise  # Re-raise the exception to stop execution 