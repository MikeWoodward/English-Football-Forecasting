"""
English Football League Tables Module.

This module provides functionality for retrieving and processing English
football league table data from the englishfootballleaguetables.co.uk website.
It scrapes match data for different seasons and provides utilities for
data processing and storage.
"""

# Standard library imports
import logging  # For logging operations and debugging
import time  # For adding delays between requests to avoid overwhelming the server
from typing import Dict, List, Any  # Type hints for better code documentation
from datetime import datetime  # For date parsing and formatting operations
import os  # For file path operations

# Third-party imports
import pandas as pd  # For data manipulation and CSV export
import requests  # For making HTTP requests to the website
from bs4 import BeautifulSoup  # For parsing HTML content from web pages


def get_day_url(*, link: Any, url_stub: str, year: str, month: str) -> Dict[str, str]:
    """
    Extract day URL information from a link element.

    This function processes a link element from the HTML table and extracts
    the date and match URL. It handles the corner case where the date in
    the link text doesn't match the date in the URL.

    Args:
        link: BeautifulSoup link element containing match information.
        url_stub: Base URL for the football league tables website.
        year: The year for the match.
        month: The month for the match.

    Returns:
        Dictionary containing 'date' and 'match_url' keys.
    """
    # Handle edge case where link element exists but has no href attribute
    # This can happen with malformed HTML or non-functional links
    if 'href' not in link.attrs:
        return {}  # Return empty dict if no href attribute found

    # Extract date from href (positions 19-29 contain the date)
    # Extract match URL and prepend the base URL
    # There's an odd corner case where the date and the link don't match.
    # The date is always correct, so check and change URL if necessary.
    expected_date = f"{year}-{month}-{link.get_text(strip=True)}"  # Construct expected date
    # Convert expected date in format '1888-September-8' to YYY-MM-DD format
    expected_date = datetime.strptime(
        expected_date, '%Y-%B-%d'
    ).strftime('%Y-%m-%d')
    date_from_url = link['href'][3:][16:26]  # Extract date portion from URL

    # Check if the date in URL matches expected date, if not, construct correct URL
    if date_from_url != expected_date:
        # Build URL with corrected date by combining base URL, path prefix, and correct date
        match_url = url_stub + link['href'][3:19] + expected_date + '.html'
    else:
        # Use original URL if dates match
        match_url = url_stub + link['href'][3:]

    # Return dictionary with extracted date and constructed match URL
    return {
        'date': expected_date,
        'match_url': match_url
    }


def get_season_days(*, url_stub: str, season: str) -> List[Dict[str, Any]]:
    """
    Retrieve all day urls for a given season.

    This function scrapes the English Football League Tables website to
    extract all match URLs for a specific season. It parses HTML tables
    that contain monthly match schedules and extracts the relevant URLs.

    Args:
        url_stub: Base URL for the football league tables website.
        season: The season year (e.g., "2023-24").

    Returns:
        List of dictionaries containing match data with 'date' and 'match_url' keys.

    Raises:
        requests.RequestException: If the request fails.
        ValueError: If the season format is invalid.
    """
    # Construct the URL for the season's calendar page
    # Format: https://www.englishfootballleaguetables.co.uk/calendar/c2023-24.html
    url_fetch = f"{url_stub}calendar/c{season}.html"

    # Initialize list to store day URLs extracted from the calendar
    day_urls = []

    # Define valid months for validation to ensure we only process relevant tables
    # This prevents processing tables that don't contain match data
    valid_months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    try:
        # Make HTTP request to the season calendar page with 20 second timeout
        # This timeout prevents hanging if the server is slow to respond
        # Add no-cache header to ensure fresh data
        headers = {'Cache-Control': 'no-cache'}  # Prevent caching to get latest data
        response = requests.get(url_fetch, timeout=20, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP error codes

        # Parse the HTML content using BeautifulSoup for easy navigation
        # Use 'ignore' error handling to skip problematic characters
        soup = BeautifulSoup(
            response.content.decode('utf-8', 'ignore'), 'html.parser'
        )

        # Find all HTML tables on the page - each table represents a month's matches
        tables = soup.find_all('table')

        # Iterate through each table to find those containing match data
        for table in tables:
            # Look for table headers - match tables have exactly 8 columns
            headers = table.find_all('th')
            if len(headers) != 8:
                continue  # Skip tables that don't have the expected structure

            # Extract month and year from the first header cell
            # Format is typically "Month Year" (e.g., "August 2023")
            # Normalize text by removing multiple spaces that may exist in HTML
            month, year = " ".join(headers[0].text.strip().split()).split(" ")

            # Validate that the month is one of the 12 valid months
            if month not in valid_months:
                continue

            # Validate that the year matches the season we're looking for
            # Seasons span two years (e.g., 2023-24), so check both years
            if year not in [season[0:4], str(int(season[0:4]) + 1)]:
                continue

            # At this point, we've confirmed this table contains match data for our season
            # Extract all links (match URLs) from the table
            links = table.find_all('a')
            for link in links:
                # Extract day URL information using the helper function
                day_info = get_day_url(
                    link=link,
                    url_stub=url_stub,
                    year=year,
                    month=month
                )

                # Skip if no valid day info was extracted
                if not day_info:
                    continue

                # Add season information and append to results
                day_urls.append({
                    'season': season,
                    **day_info  # Unpack the day_info dictionary
                })

    except requests.RequestException as e:
        # Log error and return empty list if HTTP request fails
        logging.error(f"Error retrieving matches for season {season}: {e}")
        return []

    # Log successful retrieval with count of days found
    logging.info(f"Retrieved {len(day_urls)} days for season {season}")
    return day_urls


if __name__ == "__main__":
    # Configure logging to show timestamps and log levels
    # This helps with debugging and monitoring the scraping process
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Base URL for the English Football League Tables website
    url_stub = "https://www.englishfootballleaguetables.co.uk/"

    # Full range of seasons from 1888 to 2024
    seasons = [f'{y}-{str(y+1)[2:]}' for y in range(1888, 2024 + 1)]  # Generate season strings

    # Initialize list to store all day URLs across all seasons
    day_urls = []

    # Main execution loop to process all seasons
    try:
        for season in seasons:
            # Retrieve all day URLs for the current season
            day_urls += get_season_days(url_stub=url_stub, season=season)
            # Sleep for 10 seconds to avoid overwhelming the server
            # This is important for web scraping etiquette and to prevent being blocked
            time.sleep(10)

        # Save the day URLs to a CSV file using pandas
        # Create output directory path and save as CSV
        output_path = os.path.join('Day URLs', 'day_urls.csv')
        pd.DataFrame(day_urls).to_csv(output_path, index=False)

    except Exception as e:
        # Log any unexpected errors and re-raise to stop execution
        # This ensures we don't silently fail and can debug issues
        logging.error(f"Error in main execution: {e}")
        raise  # Re-raise the exception to stop processing 