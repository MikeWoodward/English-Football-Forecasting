#!/usr/bin/env python3
"""
League Season Data Processing Script

This script reads the league_season.csv file, loads it into a pandas DataFrame,
and performs data cleaning operations including dropping duplicates.
"""

import logging
import pandas as pd
from pathlib import Path


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def load_league_season_data(*, csv_file_path: str) -> pd.DataFrame:
    """
    Load league season data from CSV file.
    
    Args:
        csv_file_path: Path to the CSV file containing league season data
        
    Returns:
        pandas.DataFrame: Loaded league season data
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        pd.errors.EmptyDataError: If the CSV file is empty
        Exception: For other file reading errors
    """
    try:
        league_season = pd.read_csv(csv_file_path)
        logging.info(f"Successfully loaded {len(league_season)} rows from {csv_file_path}")
        return league_season
    except FileNotFoundError as e:
        logging.error(f"File not found at line {e.__traceback__.tb_lineno}: {csv_file_path}")
        raise
    except pd.errors.EmptyDataError as e:
        logging.error(f"Empty CSV file at line {e.__traceback__.tb_lineno}: {csv_file_path}")
        raise
    except Exception as e:
        logging.error(f"Error reading CSV file at line {e.__traceback__.tb_lineno}: {str(e)}")
        raise


def drop_duplicates_from_dataframe(*, dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate rows from the DataFrame.
    
    Args:
        dataframe: The pandas DataFrame to process
        
    Returns:
        pandas.DataFrame: DataFrame with duplicates removed
    """
    original_count = len(dataframe)
    dataframe_cleaned = dataframe.drop_duplicates()
    removed_count = original_count - len(dataframe_cleaned)
    
    logging.info(f"Removed {removed_count} duplicate rows")
    logging.info(f"DataFrame now contains {len(dataframe_cleaned)} rows")
    
    return dataframe_cleaned


def main() -> None:
    """Main function to process league season data."""
    setup_logging()
    
    # Define the CSV file path
    csv_file_path = "league_season.csv"
    
    try:
        # Load the data
        league_season = load_league_season_data(csv_file_path=csv_file_path)
        
        # Display initial information
        logging.info(f"Initial DataFrame shape: {league_season.shape}")
        logging.info(f"Columns: {list(league_season.columns)}")
        
        # Drop duplicates
        league_season = drop_duplicates_from_dataframe(dataframe=league_season)

        # Remove league_names "Third Division South" and "Third Division North"
        league_season = league_season[~league_season['league_name'].isin(['Third Division South', 'Third Division North'])]
        
        # Group by league_name and season, get minimum and maximum dates and label them start_data and end_data
        league_season = league_season.groupby(['league_name', 'season']).agg({'date': ['min', 'max']}).reset_index()
        league_season.columns = ['league_name', 'season', 'start_date', 'end_date']

        # Get th season start year from the season column, cast it to an int
        league_season['start_year'] = league_season['season'].str.split('-').str[0].astype(int)
        # The season stop year is the start year + 1
        league_season['end_year'] = league_season['start_year'] + 1
        # Now, re-build the season column
        league_season['season'] = (
            league_season['start_year'].astype(str) + '-' +
            league_season['end_year'].astype(str)
        )

        # Rename the league_names
        division_mapping = {
            'Division 1': 'First Division',
            'Division 2': 'Second Division',
            'Division 3': 'Third Division',
            'Division 4': 'Fourth Division'
        }
        league_season['league_name'] = league_season['league_name'].replace(
            division_mapping
        )

        # Set the tier conditionally based on the league_name
        def assign_tier(league_name, start_year):
            """Assign tier based on league name and year."""
            # Modern league names (post-1992)
            if league_name in ['Football League', 'Premier League']:
                return 1
            elif league_name == 'Championship':
                return 2
            elif league_name == 'League One':
                return 3
            elif league_name == 'League Two':
                return 4
            
            # Historical league names (pre-1992)
            elif league_name == 'First Division' and start_year < 1992:
                return 1
            elif league_name == 'Second Division' and start_year < 1992:
                return 2
            elif league_name == 'Third Division' and start_year < 1992:
                return 3
            elif league_name == 'Fourth Division' and start_year < 1992:
                return 4
            
            # Post-1992 historical names
            elif league_name == 'First Division' and start_year >= 1992:
                return 2
            elif league_name == 'Second Division' and start_year >= 1992:
                return 3
            elif league_name == 'Third Division' and start_year >= 1992:
                return 4
            
            else:
                return 0
        
        league_season['tier'] = league_season.apply(
            lambda row: assign_tier(row['league_name'], row['start_year']), 
            axis=1
        )

        # Sort the dataframe by tier and season
        league_season = league_season.sort_values(by=['season', 'tier'])

        # Add a notes column
        league_season['notes'] = ''

        # Rename the columns: league_name to name, start_date to season_start, end_date to season_end
        league_season=league_season.rename(columns={'league_name': 'name', 'start_date': 'season_start', 'end_date': 'season_end'})

        # Re-order the columns: tier
        league_season = league_season[['tier', 'season_start', 'season_end', 'name', 'notes', 'season']]

        # Display final information
        logging.info(f"Final DataFrame shape: {league_season.shape}")
        logging.info("Data processing completed successfully")

        # Write the dataframe to a csv file
        league_season.to_csv('league_season_cleaned.csv', index=False)
        
    except Exception as e:
        logging.error(f"Error in main processing at line {e.__traceback__.tb_lineno}: {str(e)}")
        raise


if __name__ == "__main__":
    main()
