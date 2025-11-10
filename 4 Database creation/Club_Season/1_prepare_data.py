"""
1_prepare_data.py - Club Season Data Processing Script

This script processes TransferMarkt data files and prepares club season data
for analysis. It performs the following operations:
- Combines all CSV files from different seasons and tiers
- Cleans and standardizes the data
- Converts market values to numeric format
- Normalizes club names using club_name_normalization.csv
- Validates against club history data
- Creates a consolidated club season dataset

Data Structure:
- Input: Multiple CSV files from TransferMarkt data directory
- Output: Single processed CSV file (club_season.csv) with cleaned data

Usage:
    python 1_prepare_data.py

Dependencies:
    - pandas: For data manipulation
    - os: For file operations
    - logging: For logging operations

Author: Mike Woodward
Date: March 2024
Version: 1.0
"""

# Standard library imports for data manipulation and file operations
import os
import sys
import logging
from datetime import datetime

# Third-party imports
import pandas as pd

# Add parent directory to path to import cleanup utilities
# This allows access to the cleanuputilities module from a different directory
sys.path.append(
    os.path.join(os.path.dirname(__file__), '..', 'DataSourceCleanUp')
)


def setup_logging(
    *,
    log_level=logging.INFO
) -> None:
    """
    Set up logging configuration for the data processing application.

    This function configures logging to write to both console and file.
    Logs are saved to a 'Log' folder with timestamped filenames.

    Args:
        log_level: The logging level to use. Defaults to logging.INFO.

    Returns:
        None
    """
    # Create Log directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), '..', 'Logs')
    os.makedirs(log_dir, exist_ok=True)

    # Create timestamped log filename to avoid overwriting previous logs
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = os.path.join(
        log_dir,
        f'club_season_process_{timestamp}.log'
    )

    # Configure logging with both file and console handlers
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),  # Write to file
            logging.StreamHandler()  # Write to console
        ]
    )

    logging.info(f"Logging initialized. Log file: {log_filename}")


def get_data(
    *,
    data_folder: str = os.path.join(
        os.path.dirname(__file__), '..', '..', '1 Data Downloads',
        'TransferMarkt-values', 'Data-Download-age-foreign'
    )
) -> pd.DataFrame:
    """
    Read all CSV files from the specified data folder and merge them into a
    single pandas DataFrame.

    This function searches for all CSV files in the data folder, reads each
    one, and concatenates them into a single DataFrame. It handles potential
    encoding issues and provides detailed logging of the process.

    Args:
        data_folder: Path to the folder containing CSV files.
                    Defaults to TransferMarkt data directory.

    Returns:
        pd.DataFrame: Combined DataFrame containing all CSV data.

    Raises:
        FileNotFoundError: If the data folder doesn't exist.
        ValueError: If no CSV files are found in the folder.
    """
    # Check if data folder exists before attempting to read files
    if not os.path.exists(data_folder):
        raise FileNotFoundError(
            f"Data folder '{data_folder}' not found at line "
            f"{get_data.__code__.co_firstlineno + 15}"
        )

    # Get all CSV files in the folder, excluding hidden files
    # This filters for files ending with .csv and not starting with a dot
    csv_files = [
        f for f in os.listdir(data_folder)
        if f.endswith('.csv') and not f.startswith('.')
    ]

    # Check if any CSV files were found
    if not csv_files:
        raise ValueError(
            f"No CSV files found in '{data_folder}' at line "
            f"{get_data.__code__.co_firstlineno + 22}"
        )

    logging.info(f"Found {len(csv_files)} CSV files in {data_folder}")

    # List to store all dataframes for later concatenation
    dataframes = []

    # Read each CSV file individually
    for csv_file in csv_files:
        try:
            # Construct the full file path
            file_path = os.path.join(data_folder, csv_file)
            logging.info(f"Reading file: {csv_file}")

            # Read CSV with error handling for encoding issues
            # Specify data types for known columns to improve performance
            # squad_size and foreigner_count are integers
            # mean_age is a float that needs conversion to int
            # total_market_value is a string that needs conversion to float
            df = pd.read_csv(
                file_path,
                encoding='utf-8',
                on_bad_lines='warn',  # Warn about problematic lines
                dtype={
                    'squad_size': int,
                    'foreigner_count': int,
                    'mean_age': float
                },
                na_values=['-', '']  # Treat these values as missing data
            )

            # Add the dataframe to our collection
            dataframes.append(df)
            logging.info(
                f"Successfully read {csv_file} with {len(df)} rows"
            )

        except Exception as e:
            # Log any errors that occur during file reading
            logging.error(
                f"Failed to read {csv_file} at line "
                f"{e.__traceback__.tb_lineno}: {e}"
            )
            raise

    # Concatenate all dataframes into a single dataset
    if dataframes:
        # Combine all dataframes, ignoring the original index
        combined_df = pd.concat(
            dataframes,
            ignore_index=True,
            sort=False  # Don't sort columns to maintain original order
        )
        
        # Sort the dataframe by season, league_tier, and club_name
        # This makes the data easier to analyze and compare
        combined_df = combined_df.sort_values(
            by=['season', 'league_tier', 'club_name'],
            ascending=[True, True, True]
        ).reset_index(drop=True)

        logging.info(
            f"Successfully combined {len(dataframes)} files into "
            f"DataFrame with {len(combined_df)} total rows"
        )
        logging.info(
            "DataFrame sorted by season, league_tier, and club_name"
        )
        return combined_df
    else:
        # Handle case where no valid CSV files could be read
        raise ValueError(
            f"No valid CSV files could be read from '{data_folder}' at line "
            f"{get_data.__code__.co_firstlineno + 85}"
        )


def cleanse_data(*, combined_data: pd.DataFrame) -> pd.DataFrame:
    """
    Cleanse the combined TransferMarkt data.

    This function takes the combined dataframe and performs data cleaning
    operations to prepare it for analysis.

    Args:
        combined_data: The combined dataframe from all CSV files.

    Returns:
        A cleansed dataframe ready for analysis.

    Raises:
        Exception: If any error occurs during data cleansing.
    """
    try:
        # Create a copy of market values to avoid modifying original data
        # This prevents unintended side effects on the original dataframe
        market_values = combined_data['total_market_value'].copy()

        # Remove currency symbols ($, €) and commas from market value strings
        # This prepares the data for numeric conversion
        market_values = market_values.replace(
            {'\\$': '', '€': '', ',': ''},
            regex=True
        )

        # Convert billions (bn) to actual numeric values
        # Example: "1.5bn" becomes 1500000000
        # First, identify rows containing 'bn' in any case
        billions_mask = market_values.str.contains(
            'bn', case=False, na=False)
        # Then convert those values by removing 'bn' and multiplying by 1B
        market_values[billions_mask] = (
            market_values[billions_mask]
            .str.replace('bn', '', case=False, regex=False)
            .astype(float) * 1_000_000_000
        )

        # Convert millions (m) to actual numeric values
        # Example: "50m" becomes 50000000
        # First, identify rows containing 'm' in any case
        millions_mask = market_values.str.contains(
            'm', case=False, na=False)
        # Then convert those values by removing 'm' and multiplying by 1M
        market_values[millions_mask] = (
            market_values[millions_mask]
            .str.replace('m', '', case=False, regex=False)
            .astype(float) * 1_000_000
        )

        # Convert thousands (k) to actual numeric values
        # Example: "500k" becomes 500000
        # First, identify rows containing 'k' in any case
        thousands_mask = market_values.str.contains(
            'k', case=False, na=False)
        # Then convert those values by removing 'k' and multiplying by 1K
        market_values[thousands_mask] = (
            market_values[thousands_mask]
            .str.replace('k', '', case=False, regex=False)
            .astype(float) * 1_000
        )

        # Update the dataframe with the converted market values
        # This replaces the original string values with numeric equivalents
        combined_data['total_market_value'] = market_values

        # Calculate the fraction of foreign players in each squad
        # This provides a normalized measure of squad internationalization
        # Useful for comparing teams with different squad sizes
        combined_data['foreigner_fraction'] = (
            combined_data['foreigner_count'] / combined_data['squad_size']
        )

        # Get the club_name_normalization.csv file from the Data folder
        club_name_normalization_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '4 Database creation',
            'Data', 'club_name_normalization.csv'
        )
        club_name_normalization = pd.read_csv(club_name_normalization_path)

        combined_data = combined_data.merge(
            club_name_normalization, on="club_name", how='left')

        # Report on unmatched club names
        print('Unmatched club names:')
        print('---------------------')
        print(combined_data[combined_data['club_name_normalized'].isnull()])

        # Use the normalized name
        combined_data = combined_data.drop(columns=['club_name']).rename(
            columns={'club_name_normalized': 'club_name'}
        )

        # Check all clubs in club_history.csv
        club_history_path = os.path.join(
            os.path.dirname(__file__), '..', 'Club_History',
            'Data', 'club_history.csv'
        )
        club_history = pd.read_csv(club_history_path)
        print('Club_names in combined_data that are not in '
              'club_history.csv')
        print('------------------------------------------------------------')
        print(combined_data[
            ~combined_data['club_name'].isin(club_history['club_name'])
        ])

        # Add a tier_season id
        combined_data['league_id'] = (
            combined_data['league_tier'] * 10000 +
            combined_data['season'].str.split('-').str[0].astype(int)
        )

        # Remove unused columns and reorder
        combined_data = combined_data[[
            'league_id', 'club_name', 'squad_size', 'foreigner_count',
            'foreigner_fraction', 'mean_age', 'total_market_value'
        ]]

        # Now, read in the matches.csv file
        matches_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '2 Data preparation',
            'Data', 'matches.csv'
        )
        matches = pd.read_csv(matches_path)
        # Add a league_id column to the matches dataframe
        matches['league_id'] = (
            matches['league_tier'] * 10000 +
            matches['season'].str.split('-').str[0].astype(int)
        )
        matches = pd.concat([
            matches[['league_id', 'home_club']].rename(
                columns={'home_club': 'club_name'}),
            matches[['league_id', 'away_club']].rename(
                columns={'away_club': 'club_name'})
        ]).drop_duplicates().merge(
            club_name_normalization, on="club_name", how='left')

        print('Club_names in matches that are not in '
              'club_name_normalization.csv')
        print('------------------------------------------------------------')
        print(matches[matches['club_name_normalized'].isnull()])

        matches = matches.drop(columns=['club_name']).rename(
            columns={'club_name_normalized': 'club_name'}
        )

        # Merge the matches dataframe with the combined_data dataframe
        combined_data = matches.merge(
            combined_data, on=['league_id', 'club_name'], how='left'
        ).sort_values(by=['league_id', 'club_name'])

        # Add a combined primary key
        combined_data['club_league_id'] = (combined_data['league_id'].astype(str)
        + '-'
        + (combined_data['club_name']
           .str
           .replace(' ', '')
           .replace("&", "")
           .replace("'", "")
           .replace(".", ""))
        )

        return combined_data

    except KeyError as e:
        # Handle missing column errors
        logging.error(
            f"Missing column error in cleanse_data at line "
            f"{e.__traceback__.tb_lineno}: {e}. "
            f"Available columns: {list(combined_data.columns)}"
        )
        raise

    except ValueError as e:
        # Handle value conversion errors (e.g., non-numeric strings)
        logging.error(
            f"Value conversion error in cleanse_data at line "
            f"{e.__traceback__.tb_lineno}: {e}"
        )
        raise

    except TypeError as e:
        # Handle type errors (e.g., wrong data types for operations)
        logging.error(
            f"Type error in cleanse_data at line "
            f"{e.__traceback__.tb_lineno}: {e}"
        )
        raise

    except AttributeError as e:
        # Handle attribute errors (e.g., missing methods on objects)
        logging.error(
            f"Attribute error in cleanse_data at line "
            f"{e.__traceback__.tb_lineno}: {e}"
        )
        raise

    except Exception as e:
        # Handle any other unexpected errors
        logging.error(
            f"Unexpected error in cleanse_data at line "
            f"{e.__traceback__.tb_lineno}: {e}"
        )
        raise


if __name__ == "__main__":
    # Set up logging for the main execution
    setup_logging()

    logging.info("Starting club season data processing...")

    try:
        # Load and combine all CSV data from TransferMarkt data directory
        logging.info("Loading data from CSV files...")
        combined_data = get_data()

        # Log information about the loaded data for debugging and verification
        logging.info(f"Data loaded successfully. Shape: {combined_data.shape}")
        logging.info(f"Columns: {list(combined_data.columns)}")
        logging.info(f"Sample data:\n{combined_data.head()}")

        # Cleanse the combined data to prepare it for analysis
        cleansed_data = cleanse_data(combined_data=combined_data)

        # Save the cleansed data to a CSV file in the Data folder
        cleansed_data.to_csv(
            os.path.join(os.path.dirname(__file__), 'Data', 'club_season.csv'),
            index=False
        )

        logging.info("Club season data processing completed successfully")

    except Exception as e:
        # Handle any fatal errors that occur during the main processing
        logging.error(
            f"Fatal error in main processing at line "
            f"{e.__traceback__.tb_lineno}: {e}"
        )
        exit(1)
