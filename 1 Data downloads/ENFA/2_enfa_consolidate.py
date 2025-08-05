#!/usr/bin/env python3
"""
Module for consolidating ENFA match data from HTML files.

This module provides functions to read and parse ENFA match HTML files,
extracting relevant information for further processing. It handles:
- Reading HTML files from a specified directory
- Parsing match data including teams, scores, and league information
- Converting the data into a structured format for analysis
"""

import logging
import os
from pathlib import Path
from typing import Dict, List

import pandas as pd
from bs4 import BeautifulSoup

# Configure logging with timestamp, level, and message format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# List of special matches that should be excluded from processing
# These matches have different formats or are not part of regular league play
EXCLUDED_MATCHES = [
    "Anglo-Italian Cup",
    "Anglo-Italian Cup (1st Leg)",
    "Anglo-Italian Cup (2nd Leg)",
    "Anglo-Italian Cup Final",
    "Anglo-Italian Cup Preliminary Round",
    "Anglo-Italian Cup Round 1",
    "Anglo-Italian Cup Semi-Final",
    "Anglo-Italian Cup Semi-Final (1st Leg)",
    "Anglo-Italian Cup Semi-Final (2nd Leg)",
    "Anglo-Italian League Cup Winner's Cup Final (1st Leg)",
    "Anglo-Italian League Cup Winner's Cup Final (2nd Leg)",
    "Anglo-Scottish Cup",
    "Anglo-Scottish Cup Preliminary Round",
    "Anglo-Scottish Cup Quarter-Final",
    "Anglo-Scottish Cup Semi-Final",
    "Anglo-Scottish Cup Semi-Final (1st Leg)",
    "Anglo-Scottish Cup Semi-Final (2nd Leg)",
    "Anglo-Scottish Cup Quarter-Final (2nd Leg)",
    "Anglo-Scottish Cup Quarter-Final (1st Leg)",
    "Anglo-Scottish Cup Preliminary Round (r)",
    "Anglo-Scottish Cup Preliminary Round (r2)",
    "Anglo-Scottish Cup Preliminary Round (r3)",
    "Anglo-Scottish Cup Preliminary Round (r4)",
    "Anglo-Scottish Cup Preliminary Round (r5)",
    "Anglo-Scottish Cup Preliminary Round (r6)",
    "Anglo-Scottish Cup Preliminary Round (r7)",
    "Debenhams Cup Final (1st Leg)",
    "Debenhams Cup Final (2nd Leg)",
    "European Champions' Cup (1st Leg)",
    "European Champions' Cup (2nd Leg)",
    "European Champions' Cup Final",
    "European Champions' Cup Preliminary Round (1st Leg)",
    "European Champions' Cup Preliminary Round (2nd Leg)",
    "European Champions' Cup Quarter-Final (1st Leg)",
    "European Champions' Cup Quarter-Final (2nd Leg)",
    "European Champions' Cup Quarter-Final (r)",
    "European Champions' Cup Round 1 (1st Leg)",
    "European Champions' Cup Round 1 (2nd Leg)",
    "European Champions' Cup Round 1 (r)",
    "European Champions' Cup Round 2 (1st Leg)",
    "European Champions' Cup Round 2 (2nd Leg)",
    "European Champions' Cup Semi-Final (1st Leg)",
    "European Champions' Cup Semi-Final (2nd Leg)",
    "European Cup Winners' Cup Round 1 (r)",
    "European Cup Winners' Cup Final",
    "European Cup Winners' Cup Final (r)",
    "European Cup Winners' Cup Preliminary Round",
    "European Cup Winners' Cup Preliminary Round (1st Leg)",
    "European Cup Winners' Cup Preliminary Round (2nd Leg)",
    "European Cup Winners' Cup Quarter-Final",
    "European Cup Winners' Cup Quarter-Final (1st Leg)",
    "European Cup Winners' Cup Quarter-Final (2nd Leg)",
    "European Cup Winners' Cup Round 1",
    "European Cup Winners' Cup Round 1 (1st Leg)",
    "European Cup Winners' Cup Round 1 (2nd Leg)",
    "European Cup Winners' Cup Round 2",
    "European Cup Winners' Cup Round 2 (1st Leg)",
    "European Cup Winners' Cup Round 2 (2nd Leg)",
    "European Cup Winners' Cup Semi-Final (1st Leg)",
    "European Cup Winners' Cup Semi-Final (2nd Leg)",
    "European Cup Winners' Cup Quarter-Final (r)",
    "European Cup Winners' Cup Semi-Final (r)",
    "European Cup Winners' Cup Semi-Final (r2)",
    "European Super Cup",
    "European Super Cup Final",
    "European Super Cup Final (1st Leg)",
    "European Super Cup Final (2nd Leg)",
    "Expunged League Match",
    "FA Cup",
    "FA Cup (r)",
    "FA Cup (r2)",
    "FA Cup (r3)",
    "FA Cup (r4)",
    "FA Cup Final",
    "FA Cup Final (r)",
    "FA Cup Preliminary Round",
    "FA Cup Preliminary Round (r)",
    "FA Cup Preliminary Round (r2)",
    "FA Cup Round 1",
    "FA Cup Round 1 (1st Leg)",
    "FA Cup Round 1 (2nd Leg)",
    "FA Cup Round 1 (r)",
    "FA Cup Round 1 (r2)",
    "FA Cup Round 1 (r3)",
    "FA Cup Round 2",
    "FA Cup Round 2 (1st Leg)",
    "FA Cup Round 2 (2nd Leg)",
    "FA Cup Round 2 (r)",
    "FA Cup Round 2 (r2)",
    "FA Cup Round 2 (r3)",
    "FA Cup Round 2 (r4)",
    "FA Cup Round 3",
    "FA Cup Round 3 (1st Leg)",
    "FA Cup Round 3 (2nd Leg)",
    "FA Cup Round 3 (r)",
    "FA Cup Round 3 (r2)",
    "FA Cup Round 3 (r3)",
    "FA Cup Round 3 (r4)",
    "FA Cup Round 4",
    "FA Cup Round 4 (1st Leg)",
    "FA Cup Round 4 (2nd Leg)",
    "FA Cup Round 4 (r)",
    "FA Cup Round 4 (r2)",
    "FA Cup Round 4 (r3)",
    "FA Cup Round 4 (r4)",
    "FA Cup Round 5",
    "FA Cup Round 5 (1st Leg)",
    "FA Cup Round 5 (2nd Leg)",
    "FA Cup Round 5 (r)",
    "FA Cup Round 5 (r2)",
    "FA Cup Round 6",
    "FA Cup Round 6 (1st Leg)",
    "FA Cup Round 6 (2nd Leg)",
    "FA Cup Round 6 (r)",
    "FA Cup Round 6 (r2)",
    "FA Cup Round 6 (r3)",
    "FA Cup Semi-Final",
    "FA Cup Semi-Final (r)",
    "FA Cup Semi-Final (r2)",
    "FA Cup Semi-Final (r3)",
    "FA Charity Shield",
    "FA Charity Shield (r)",
    "FA Community Shield",
    "FIFA Club World Cup",
    "FIFA Club World Cup Final",
    "FIFA Club World Cup Quarter-Final",
    "FIFA Club World Cup Semi-Final",
    "Football League Cup (2nd Leg)",
    "Football League Cup Final",
    "Football League Cup Final (r)",
    "Football League Cup Final (r2)",
    "Football League Cup Preliminary Round",
    "Football League Cup (1st Leg)",
    "Football League Cup (2nd Leg)",
    "Football League Cup Round 1",
    "Football League Cup Round 1 (1st Leg)",
    "Football League Cup Round 1 (2nd Leg)",
    "Football League Cup Round 1 (r)",
    "Football League Cup Round 1 (r2)",
    "Football League Cup Round 1 (r3)",
    "Football League Cup Round 2",
    "Football League Cup Round 2 (1st Leg)",
    "Football League Cup Round 2 (2nd Leg)",
    "Football League Cup Round 2 (r)",
    "Football League Cup Round 2 (r2)",
    "Football League Cup Round 2 (r3)",
    "Football League Cup Round 3",
    "Football League Cup Round 3 (r)",
    "Football League Cup Round 3 (r2)",
    "Football League Cup Round 3 (r3)",
    "Football League Cup Round 4",
    "Football League Cup Round 4 (r)",
    "Football League Cup Round 4 (r2)",
    "Football League Cup Round 5",
    "Football League Cup Round 5 (r)",
    "Football League Cup Round 5 (r2)",
    "Football League Cup Semi-Final",
    "Football League Cup Semi-Final (1st Leg)",
    "Football League Cup Semi-Final (2nd Leg)",
    "Football League Cup Semi-Final (r)",
    "Football League Cup Semi-Final (r2)",
    "Football League Group Cup Final",
    "Football League Group Cup Quarter-Final",
    "Football League Group Cup Round 1",
    "Football League Group Cup Semi-Final",
    "Football League Playoffs Final",
    "Football League Playoffs Final (1st Leg)",
    "Football League Playoffs Final (2nd Leg)",
    "Football League Playoffs Final (r)",
    "Football League Playoffs Semi-Final",
    "Football League Playoffs Semi-Final (1st Leg)",
    "Football League Playoffs Semi-Final (2nd Leg)",
    "Football League Playoffs Semi-Final  (2nd Leg)",
    "Football League Trophy",
    "Football League Trophy (1st Leg)",
    "Football League Trophy (2nd Leg)",
    "Football League Trophy (NA)",
    "Football League Trophy (NB)",
    "Football League Trophy (NC)",
    "Football League Trophy (ND)",
    "Football League Trophy (NE)",
    "Football League Trophy (NF)",
    "Football League Trophy (NG)",
    "Football League Trophy (NH)",
    "Football League Trophy (SA)",
    "Football League Trophy (SB)",
    "Football League Trophy (SC)",
    "Football League Trophy (SD)",
    "Football League Trophy (SE)",
    "Football League Trophy (SF)",
    "Football League Trophy (SG)",
    "Football League Trophy (SH)",
    "Football League Trophy Final",
    "Football League Trophy Preliminary Round",
    "Football League Trophy Preliminary Round (r)",
    "Football League Trophy Quarter-Final",
    "Football League Trophy Round 1",
    "Football League Trophy Round 1 (1st Leg)",
    "Football League Trophy Round 1 (2nd Leg)",
    "Football League Trophy Round 1 (r)",
    "Football League Trophy Round 2",
    "Football League Trophy Round 3",
    "Football League Trophy Round 4",
    "Football League Trophy Semi-Final",
    "Full Members' Cup (1st Leg)",
    "Full Members' Cup (2nd Leg)",
    "Full Members' Cup Quarter-Final",
    "Full Members' Cup Round 1",
    "Full Members' Cup Round 2",
    "Full Members' Cup Round 3",
    "Full Members' Cup Semi-Final",
    "Full Members' Cup Final",
    "Inter-Cities Fairs Cup Final (1st Leg)",
    "Inter-Cities Fairs Cup Final (2nd Leg)",
    "Inter-Cities Fairs Cup Quarter-Final (1st Leg)",
    "Inter-Cities Fairs Cup Quarter-Final (2nd Leg)",
    "Inter-Cities Fairs Cup Round 1 (1st Leg)",
    "Inter-Cities Fairs Cup Round 1 (2nd Leg)",
    "Inter-Cities Fairs Cup Round 2 (1st Leg)",
    "Inter-Cities Fairs Cup Round 2 (2nd Leg)",
    "Inter-Cities Fairs Cup Round 3 (1st Leg)",
    "Inter-Cities Fairs Cup Round 3 (2nd Leg)",
    "Inter-Cities Fairs Cup Semi-Final (1st Leg)",
    "Inter-Cities Fairs Cup Semi-Final (2nd Leg)",
    "Inter-Cities Fairs Cup Semi-Final (r)",
    "Inter-Cities Fairs Cup Play-off",
    "Inter-Cities Fairs Cup Play-off (1st Leg)",
    "Inter-Cities Fairs Cup Play-off (2nd Leg)",
    "Inter-Cities Fairs Cup Semi-Final (r3)",
    "Inter-Cities Fairs Cup Semi-Final (r4)",
    "Inter-Cities Fairs Cup Semi-Final (r5)",
    "Inter-Cities Fairs Cup Semi-Final (r6)",
    "Inter-Cities Fairs Cup Round 3 (r)",
    "League Division One (abandoned)",
    "League Division Three (Southern Section)",
    "League Division Three (Northern Section)",
    "League Division Three(Northern Section)(abandoned)",
    "League Division Three(Southern Section)(abandoned)",
    "League Division Three (Northern Section) (abandoned)",
    "League Division Three (Southern Section) (abandoned)",
    "League Division Two (abandoned)",
    "Mercentile Credit Centenary Trophy Quarter-Final",
    "Mercentile Credit Centenary Trophy Final",
    "Mercentile Credit Centenary Trophy Semi-Final",
    "Screen Sport Super Cup Round 1",
    "Screen Sport Super Cup Semi-Final (1st Leg)",
    "Screen Sport Super Cup Semi-Final (2nd Leg)",
    "Screen Sport Super Cup (1st Leg)",
    "Screen Sport Super Cup (2nd Leg)",
    "Sheriff of London Charity Shield",
    "Sheriff of London Charity Shield (r)",
    "Test Matches",
    "Texaco Cup (1st Leg)",
    "Texaco Cup (2nd Leg)",
    "Texaco Cup Round 1",
    "Texaco Cup Round 1 (1st Leg)",
    "Texaco Cup Round 2 (2nd Leg)",
    "Texaco Cup Quarter-Final (2nd Leg)",
    "Texaco Cup Quarter-Final (1st Leg)",
    "Texaco Cup Semi-Final (1st Leg)",
    "Texaco Cup Semi-Final (2nd Leg)",
    "Texaco Cup Final",
    "Texaco Cup Round 2 (r)",
    "Texaco Cup Final (2nd Leg)",
    "Texaco Cup Preliminary Round",
    "Texaco Cup Preliminary Round (1st Leg)",
    "Texaco Cup Preliminary Round (2nd Leg)",
    "Texaco Cup Quarter-Final",
    "Texaco Cup Quarter-Final (1st Leg)",
    "Texaco Cup Round 1 (1st Leg)",
    "Texaco Cup Round 1 (2nd Leg)",
    "Texaco Cup Round 2 (1st Leg)",
    "Texaco Cup Round 2 (2nd Leg)",
    "Texaco Cup Round 3 (1st Leg)",
    "Texaco Cup Round 3 (2nd Leg)",
    "Texaco Cup Round 4 (1st Leg)",
    "Texaco Cup Round 4 (2nd Leg)",
    "Texaco Cup Round 5 (1st Leg)",
    "Third Division Cup",
    "Third Division Cup Final",
    "Third Division Cup Round 1",
    "Third Division Cup Round 1 (r)",
    "Third Division Cup Round 2",
    "Third Division Cup Round 2 (r)",
    "Third Division Cup Round 3",
    "Third Division Cup Round 3 (r)",
    "Third Division Cup Round 3 (r2)",
    "Third Division Cup Semi-Final",
    "Third Division Cup Semi-Final (r)",
    "Third Division Cup Semi-Final (r2)",
    "UEFA Champions League (1st Leg)",
    "UEFA Champions League (2nd Leg)",
    "UEFA Champions League (A)",
    "UEFA Champions League (B)",
    "UEFA Champions League (C)",
    "UEFA Champions League (D)",
    "UEFA Champions League (E)",
    "UEFA Champions League (F)",
    "UEFA Champions League (G)",
    "UEFA Champions League (H)",
    "UEFA Champions League Final",
    "UEFA Champions League Quarter-Final",
    "UEFA Champions League Quarter-Final (1st Leg)",
    "UEFA Champions League Quarter-Final (2nd Leg)",
    "UEFA Champions League Round 1 (1st Leg)",
    "UEFA Champions League Round 1 (2nd Leg)",
    "UEFA Champions League Round 1 (r)",
    "UEFA Champions League Round 2 (1st Leg)",
    "UEFA Champions League Round 2 (2nd Leg)",
    "UEFA Champions League Round of 16 (1st Leg)",
    "UEFA Champions League Round of 16 (2nd Leg)",
    "UEFA Champions League Semi-Final (1st Leg)",
    "UEFA Champions League Semi-Final (2nd Leg)",
    "UEFA Conference League (1st Leg)",
    "UEFA Conference League (2nd Leg)",
    "UEFA Conference League (A)",
    "UEFA Conference League (B)",
    "UEFA Conference League (C)",
    "UEFA Conference League (D)",
    "UEFA Conference League (E)",
    "UEFA Conference League (F)",
    "UEFA Conference League (G)",
    "UEFA Conference League (H)",
    "UEFA Conference League Final",
    "UEFA Conference League Quarter-Final (1st Leg)",
    "UEFA Conference League Quarter-Final (2nd Leg)",
    "UEFA Conference League Round 1 (1st Leg)",
    "UEFA Conference League Round 1 (2nd Leg)",
    "UEFA Conference League Round of 16 (1st Leg)",
    "UEFA Conference League Round of 16 (2nd Leg)",
    "UEFA Conference League Semi-Final (1st Leg)",
    "UEFA Conference League Semi-Final (2nd Leg)",
    "UEFA Conference League Semi-Final  (2nd Leg)",
    "UEFA Cup (1st Leg)",
    "UEFA Cup (2nd Leg)",
    "UEFA Cup (A)",
    "UEFA Cup (B)",
    "UEFA Cup (C)",
    "UEFA Cup (D)",
    "UEFA Cup (E)",
    "UEFA Cup (F)",
    "UEFA Cup (G)",
    "UEFA Cup (H)",
    "UEFA Cup Final",
    "UEFA Cup Final (1st Leg)",
    "UEFA Cup Final (2nd Leg)",
    "UEFA Cup Quarter-Final (1st Leg)",
    "UEFA Cup Quarter-Final (2nd Leg)",
    "UEFA Cup Round 1 (1st Leg)",
    "UEFA Cup Round 1 (2nd Leg)",
    "UEFA Cup Round 2 (1st Leg)",
    "UEFA Cup Round 2 (2nd Leg)",
    "UEFA Cup Round 3 (1st Leg)",
    "UEFA Cup Round 3 (2nd Leg)",
    "UEFA Cup Round 4 (1st Leg)",
    "UEFA Cup Round 4 (2nd Leg)",
    "UEFA Cup Round 5 (1st Leg)",
    "UEFA Cup Round 5 (2nd Leg)",
    "UEFA Cup Round of 16 (1st Leg)",
    "UEFA Cup Round of 16 (2nd Leg)",
    "UEFA Cup Round of 32 (1st Leg)",
    "UEFA Cup Round of 32 (2nd Leg)",
    "UEFA Cup Semi-Final (1st Leg)",
    "UEFA Cup Semi-Final (2nd Leg)",
    "UEFA Europa League",
    "UEFA Europa League (1st Leg)",
    "UEFA Europa League (2nd Leg)",
    "UEFA Europa League (A)",
    "UEFA Europa League (B)",
    "UEFA Europa League (C)",
    "UEFA Europa League (D)",
    "UEFA Europa League (E)",
    "UEFA Europa League (F)",
    "UEFA Europa League (G)",
    "UEFA Europa League (H)",
    "UEFA Europa League (I)",
    "UEFA Europa League (J)",
    "UEFA Europa League (K)",
    "UEFA Europa League (L)",
    "UEFA Europa League Final",
    "UEFA Europa League Quarter-Final",
    "UEFA Europa League Quarter-Final (1st Leg)",
    "UEFA Europa League Quarter-Final (2nd Leg)",
    "UEFA Europa League Round 1 (1st Leg)",
    "UEFA Europa League Round 1 (2nd Leg)",
    "UEFA Europa League Round of 16 (1st Leg)",
    "UEFA Europa League Round of 16 (2nd Leg)",
    "UEFA Europa League Round of 32 (1st Leg)",
    "UEFA Europa League Round of 32 (2nd Leg)",
    "UEFA Europa League Semi-Final",
    "UEFA Europa League Semi-Final (1st Leg)",
    "UEFA Europa League Semi-Final (2nd Leg)",
    "UEFA Intertoto Cup",
    "UEFA Intertoto Cup Round 2 (1st Leg)",
    "UEFA Intertoto Cup Round 2 (2nd Leg)",
    "UEFA Intertoto Cup Round 3 (1st Leg)",
    "UEFA Intertoto Cup Round 3 (2nd Leg)",
    "UEFA Intertoto Cup Round 4 (1st Leg)",
    "UEFA Intertoto Cup Round 4 (2nd Leg)",
    "UEFA Intertoto Cup Round 5 (1st Leg)",
    "UEFA Intertoto Cup Round 5 (2nd Leg)",
    "Watney Cup Final",
    "Watney Cup Round 1",
    "Watney Cup Semi-Final",
    "World Club Championship Final",
    "World Club Championship Final (1st Leg)",
    "World Club Championship Final (2nd Leg)",
]


def read_enfa_matches(*, folder_path: str) -> List[str]:
    """
    Read all HTML files from the specified folder.

    This function:
    1. Validates the folder exists
    2. Finds all HTML files in the folder
    3. Sorts them by date (most recent first)
    4. Returns the list of file paths

    Args:
        folder_path: Path to the folder containing ENFA HTML files.

    Returns:
        List of full paths to HTML files in the folder.

    Raises:
        FileNotFoundError: If the specified folder does not exist.
    """
    try:
        # Convert string path to Path object for better path handling
        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")

        # Get all HTML files in the directory
        html_files = [str(file) for file in folder.glob("*.html")]

        # Sort files by date (extracted from filename) in descending order
        html_files.sort(
            key=lambda x: x.split("/")[-1].split(".")[0],
            reverse=True
        )

        logger.info(f"Found {len(html_files)} HTML files in {folder_path}")
        return html_files

    except Exception as e:
        logger.error(f"Error reading ENFA matches: {str(e)}")
        raise

def parse_enfa_file(*, file_path: str) -> Dict:
    """
    Parse an ENFA HTML file and extract relevant information.

    This function:
    1. Reads the HTML file
    2. Extracts match day and date information
    3. Parses the HTML tables containing match data
    4. Processes each match, excluding special matches
    5. Returns structured data for each match

    Args:
        file_path: Path to the ENFA HTML file to parse.

    Returns:
        Dictionary containing parsed data from the HTML file with keys:
        - match_day: The match day identifier
        - match_date: The date of the match
        - league_tier: The tier of the league (1 or 2)
        - home_club: Name of the home team
        - away_club: Name of the away team
        - home_goals: Number of goals scored by home team
        - away_goals: Number of goals scored by away team

    Raises:
        FileNotFoundError: If the specified file does not exist.
        Exception: For any other parsing errors.
    """
    try:
        parsed_data = []

        # Read the HTML file with UTF-8 encoding
        with open(file_path, 'r', encoding='utf-8') as file:
            data_html = file.read()

        # Extract match day and date from the HTML header
        index_pos = data_html.find("<br>")
        match_day = data_html[0:index_pos]
        match_date = data_html[index_pos + 4:index_pos + 14]

        # Parse HTML using BeautifulSoup
        soup = BeautifulSoup(data_html, 'html.parser')
        tables = soup.find_all("table")

        # Process each table (excluding the first one which contains date only)
        for table in tables[1:]:
            rows = table.find("tbody").find_all("tr")

            columns = rows[1].find_all("td")
            if len(columns) > 1 and columns[1].text == "Table":
                continue

            table_title = rows[1].text.strip()
            # Remove multiple spaces
            table_title = " ".join(table_title.split())

            # Skip special matches that are not part of regular league play
            if table_title in EXCLUDED_MATCHES:
                continue

            # Process each match in the table
            # Start from index 4 to skip header rows
            for row in rows[4:]:
                columns = row.find_all("td")
                # If there's are images in the first column, skip the row
                if len(columns[0].find_all("img")) > 0:
                    continue
                # Extract the home and away clubs and their scores
                home_club = ' '.join(columns[0].stripped_strings)
                away_club = ' '.join(columns[2].stripped_strings)
                score = columns[1].text.strip().split("-")
                home_goals = int(score[0])
                away_goals = int(score[1])

                # Create a dictionary for each match
                parsed_data.append({
                    "table_title": table_title,
                    "match_day": match_day,
                    "match_date": match_date,
                    "home_club": home_club,
                    "away_club": away_club,
                    "home_goals": home_goals,
                    "away_goals": away_goals
                })

        logger.info(f"Successfully parsed file: {file_path}")
        return parsed_data

    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error parsing file {file_path}: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        # Path to the folder containing ENFA match HTML files
        folder_path = "HTML"  # Use the local HTML folder

        # Read all match files
        matches = read_enfa_matches(folder_path=folder_path)

        # Parse each file and collect the data, note we don't add nulls
        parsed_data = []
        for match_file in matches:
            parsed_matches = parse_enfa_file(file_path=match_file)
            if len(parsed_matches) > 0:
                parsed_data += parsed_matches

        # Convert the parsed data to a DataFrame and save as CSV
        file_name = os.path.join("Data", "enfa_baseline.csv")
        pd.DataFrame(parsed_data).drop_duplicates().sort_values(
            by=['match_date'],
            ascending=False
        ).to_csv(
            file_name,
            index=False
        )

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise 