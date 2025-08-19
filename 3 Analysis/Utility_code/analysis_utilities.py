"""
Analysis utilities module for EPL predictor project.

This module contains utility functions and classes for data analysis tasks,
specifically focused on processing football match data and creating
interactive visualizations using Bokeh.
"""

import os
import webbrowser
from typing import List
import bokeh
import pandas as pd  


def save_plots(
    *,
    divs: List[str],
    scripts: List[str],
    titles: List[str],
    file_name: str
) -> None:
    """
    Save the plots to the HTML folder.

    This function creates an HTML file containing Bokeh plots with interactive
    functionality. It also saves individual script and div files for debugging
    and reference purposes.

    Args:
        divs: List of HTML div strings containing plot elements.
        scripts: List of JavaScript script strings for plot interactivity.
        titles: List of plot titles corresponding to divs and scripts.
        file_name: Name of the output HTML file.

    Returns:
        None

    Raises:
        FileNotFoundError: If the Plots directory doesn't exist.
        OSError: If there are issues writing to files.
    """
    # Define the output directory for all plot-related files
    folder_name = "Plots"

    # Create the Plots directory if it doesn't exist
    # This ensures the directory structure is available before writing files
    os.makedirs(folder_name, exist_ok=True)

    # Get Bokeh version for proper script imports
    # This ensures compatibility with the specific Bokeh version being used
    version = bokeh.__version__

    # Construct the CDN script imports for Bokeh libraries
    # These scripts provide the necessary JavaScript functionality for plots
    imported_scripts = (
        f"""<script src="https://cdn.bokeh.org/bokeh/release/"""
        f"""bokeh-{version}.min.js"></script>\n"""
        f"""<script src="https://cdn.bokeh.org/bokeh/release/"""
        f"""bokeh-widgets-{version}.min.js"></script>\n"""
        f"""<script src="https://cdn.bokeh.org/bokeh/release/"""
        f"""bokeh-tables-{version}.min.js"></script>\n"""
        f"""<script src="https://cdn.bokeh.org/bokeh/release/"""
        f"""bokeh-mathjax-{version}.min.js"></script>\n"""
    )

    # Sample text content for the HTML page
    # This provides placeholder content between plots for better presentation
    lorem = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do "
        "eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim "
        "ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut "
        "aliquip ex ea commodo consequat. Duis aute irure dolor in "
        "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
        "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in "
        "culpa qui officia deserunt mollit anim id est laborum."
    )

    # Create HTML file with the generated plot
    # This is the main output file that will be opened in the browser
    try:
        with open(os.path.join(folder_name, file_name), "w") as f:
            # Header equivalent - include Bokeh script imports
            # These scripts must be loaded before any plot content
            f.write("<!-- Script imports -->\n")
            f.write(imported_scripts)

            # Body equivalent - add HTML content
            # Start the main content section of the HTML document
            f.write("<!-- HTML body -->\n")

            # Add introductory text content
            f.write(f"""<p>{lorem}</p>\n""")

            # Iterate through each plot div and add it to the HTML
            # Each plot is wrapped in a centered div for proper alignment
            for index, div in enumerate(divs):
                # Plot container with center alignment
                # This ensures plots are visually centered on the page
                f.write(f"<!-- Plot {titles[index]} -->\n")
                f.write("<div align='center'>\n")
                f.write(div)
                f.write("\n")
                f.write("</div>\n")

                # Add separator text between plots for better readability
                f.write(f"""<p>{lorem}</p>\n""")

            # Chart scripts for interactive functionality
            # These scripts enable plot interactivity and must be placed after divs
            f.write("<!-- Chart scripts -->\n")
            for index, script in enumerate(scripts):
                f.write(f"<!-- Plot {titles[index]} -->\n")
                f.write(script)
                f.write("\n")
    except FileNotFoundError as e:
        # Handle case where directory creation failed or path is invalid
        print(f"Error on line {e.__traceback__.tb_lineno}: Plots directory not "
              f"found. Line content: 'with open(os.path.join(\"{folder_name}\", "
              f"\"file_name\"), \"w\") as f:'")
        raise
    except OSError as e:
        # Handle general file system errors (permissions, disk full, etc.)
        print(f"Error on line {e.__traceback__.tb_lineno}: Failed to write "
              f"HTML file. Line content: 'with open(os.path.join(\"Plots\", "
              f"\"file_name\"), \"w\") as f:'")
        raise

    # Write each of the scripts to a separate file
    # This allows for individual debugging and inspection of plot scripts
    try:
        for index, script in enumerate(scripts):
            # Create individual script files with descriptive names
            script_filename = f"script_{index+1}.txt"
            with open(os.path.join("Plots", script_filename), "w") as f:
                f.write(f"<!--Chart script {titles[index]}-->\n")
                f.write(script)
    except OSError as e:
        # Handle errors when writing individual script files
        print(f"Error on line {e.__traceback__.tb_lineno}: Failed to write "
              f"script files. Line content: 'with open(os.path.join(\"Plots\", "
              f"f\"script_{index+1}.txt\"), \"w\") as f:'")
        raise

    # Write all scripts to a combo file
    # This creates a single file containing all scripts for easy reference
    try:
        with open(os.path.join(folder_name, "scripts.txt"), "w") as f:
            f.write(f"<!-- {file_name} scripts -->\n")
            f.write("<!------------------------>\n")

            # Add each script with its corresponding title
            for index, script in enumerate(scripts):
                f.write(f"<!--Chart script {titles[index]}-->\n")
                f.write(script)
                f.write("\n")
    except OSError as e:
        # Handle errors when writing the combined scripts file
        print(f"Error on line {e.__traceback__.tb_lineno}: Failed to write "
              f"scripts combo file. Line content: 'with open(os.path.join("
              f"\"{folder_name}\", \"scripts.txt\"), \"w\") as f:'")
        raise

    # Write each of the divs to a separate file
    # This allows for individual inspection and debugging of plot HTML
    try:
        for index, div in enumerate(divs):
            # Create individual div files with descriptive names
            div_filename = f"div_{index+1}.txt"
            with open(os.path.join(folder_name, div_filename), "w") as f:
                f.write(f"<!-- Plot {titles[index]} -->\n")
                f.write("<div align='center'>\n")
                f.write("    " + div)  # Indent the div content for readability
                f.write("\n")
                f.write("</div>\n")
    except OSError as e:
        # Handle errors when writing individual div files
        print(f"Error on line {e.__traceback__.tb_lineno}: Failed to write "
              f"div files. Line content: 'with open(os.path.join(\"{folder_name}\", "
              f"f\"div_{index+1}.txt\"), \"w\") as f:'")
        raise

    # Open the generated plot in the default web browser
    # This provides immediate visual feedback of the generated plots
    try:
        # Construct the full file path and convert to file:// URL format
        file_path = os.path.abspath(os.path.join(folder_name, file_name))
        file_url = 'file:///' + file_path
        webbrowser.open(file_url)
    except Exception as e:
        # Handle any errors that might occur when opening the browser
        # This includes browser not found, file not accessible, etc.
        print(f"Error on line {e.__traceback__.tb_lineno}: Failed to open "
              f"browser. Line content: 'webbrowser.open('file:///' + "
              f"os.path.abspath(os.path.join(\"{folder_name}\", "
              f"\"{file_name}\")))'")
        raise


def wide_to_long_matches(*, matches: pd.DataFrame) -> pd.DataFrame:
    """
    Convert match data from wide format to long format and add derived metrics.

    This function transforms match data where each row represents a match
    (with home and away teams in separate columns) into a long format where
    each row represents a team's performance in a specific match. It also
    calculates aggregated statistics and adds derived columns for analysis.

    Args:
        matches: DataFrame containing match data with columns:
               season, league_tier, match_date, home_club, away_club,
               home_goals, away_goals

    Returns:
        DataFrame with the following structure:
        - season: Original season identifier (e.g., "2020-21")
        - league_tier: League tier/division level
        - club_name: Name of the club (from either home_club or away_club)
        - for_goals: Total goals scored by the club in the season
        - against_goals: Total goals conceded by the club in the season
        - net_goals: Difference between goals scored and conceded
        - season_start: Starting year of the season (extracted from season
          string)

    Example:
        Input: One row per match with home_club, away_club, home_goals, away_goals
        Output: Two rows per match (one for each team) with standardized
                club_name, for_goals, against_goals columns
    """
    # Select only the required columns for analysis
    # This reduces memory usage and focuses on relevant data
    columns = [
        'season', 'league_tier', 'match_date', 'home_club', 'away_club',
        'home_goals', 'away_goals'
    ]
    matches = matches.loc[:, columns]

    # Create separate dataframes for home and away teams
    # This allows us to treat each team's performance separately
    home = matches.loc[:, ['season', 'league_tier', 'home_club', 'home_goals',
                           'away_goals']].copy()
    
    # Rename columns to standardize the data structure
    # This creates a consistent format for both home and away teams
    home = home.rename(columns={
        'home_club': 'club_name',  # Standardize club name column
        'home_goals': 'for_goals',  # Goals scored by the club
        'away_goals': 'against_goals'  # Goals conceded by club
    })

    # Create away team dataframe with same structure
    # Extract away team data and prepare for transformation
    away = matches.loc[:, ['season', 'league_tier', 'away_club', 'home_goals',
                           'away_goals']].copy()
    
    # Rename columns for away teams (note: goals are swapped for away
    # perspective)
    # For away teams, their goals are the away_goals from the original data
    away = away.rename(columns={
        'away_club': 'club_name',  # Standardize club name column
        'away_goals': 'for_goals',  # Goals scored by club (away goals)
        'home_goals': 'against_goals'  # Goals conceded by club (home goals)
    })

    # Combine home and away data into a single dataframe
    # This gives us one row per team per match
    total = pd.concat(objs=[home, away])

    # Aggregate goals by club, season, and league tier
    # This gives us total goals for and against each club per season
    # The groupby operation sums up all goals across all matches in a season
    total = total.groupby(by=['season', 'league_tier', 'club_name']).agg(
        func={
            'for_goals': 'sum',  # Total goals scored by club
            'against_goals': 'sum'  # Total goals conceded by club
        }).reset_index().sort_values(by=['club_name', 'season',
                                         'league_tier'])

    # Calculate net goals (goals scored minus goals conceded)
    # This gives us a measure of overall performance - positive values
    # indicate better performance
    total['net_goals'] = total['for_goals'] - total['against_goals']

    # Extract starting year from season string (e.g., "2020-21" -> 2020)
    # This is needed for chronological analysis and sorting
    # The season format is typically "YYYY-YY" where we want the first year
    total['season_start'] = (total.loc[:, 'season']
                             .str.split(pat='-')  # Split on hyphen
                             .str[0]  # Take first part (year)
                             .astype(dtype=int))  # Convert to integer

    # Sort data chronologically by club and season for proper analysis
    # This ensures that when we analyze trends over time, the data is
    # in the correct chronological order
    total = total.sort_values(by=['club_name', 'season_start'])

    return total

