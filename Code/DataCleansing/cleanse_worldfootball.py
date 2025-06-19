"""Script to analyze attendance data for data quality issues.

This script reads the attendance data file and reports on:
1. Empty rows in specified columns
2. Non-numeric characters in numeric columns
3. Cleanses data by removing specific rows and normalizing values
4. Transforms club names using a reference mapping

The script processes football match attendance data, focusing on data quality
and consistency. It handles special cases like COVID-19 affected matches and
normalizes club names for consistency across the dataset.
"""

import pandas as pd
from pathlib import Path
import logging
from typing import List, Dict, Any
from utilities import transform_club_names, check_clubs_1, check_clubs_2

# Configure logging with timestamp, level, and message format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_empty_rows(df: pd.DataFrame, columns: List[str]) -> Dict[str, int]:
    """Check for empty rows in specified columns.
    
    Args:
        df: DataFrame to analyze
        columns: List of column names to check
        
    Returns:
        Dictionary with column names as keys and count of empty rows as values
    """
    # Initialize dictionary to store empty row counts for each column
    empty_counts = {}
    
    # Iterate through each specified column and count empty (NA) values
    for col in columns:
        empty_count = df[col].isna().sum()
        empty_counts[col] = empty_count
        # Log warning if any empty values are found
        if empty_count > 0:
            logger.warning(f"Column '{col}' has {empty_count} empty rows")
    return empty_counts


def check_non_numeric(df: pd.DataFrame, columns: List[str]) -> Dict[str, List[Any]]:
    """Check for non-numeric characters in specified columns.
    
    Args:
        df: DataFrame to analyze
        columns: List of column names to check
        
    Returns:
        Dictionary with column names as keys and lists of non-numeric values
    """
    # Initialize dictionary to store non-numeric values found in each column
    non_numeric = {}
    
    # Process each specified column
    for col in columns:
        # Convert column to string and use regex to identify non-numeric values
        # This catches any values that aren't purely numbers or decimal points
        non_numeric_mask = df[col].astype(str).str.match(r'[^0-9.]')
        non_numeric_rows = df[non_numeric_mask]
        
        if not non_numeric_rows.empty:
            # Extract unique non-numeric values for reporting
            non_numeric_values = non_numeric_rows[col].unique()
            non_numeric[col] = non_numeric_values.tolist()
            logger.warning(
                f"Column '{col}' contains non-numeric values: {non_numeric_values}"
            )
            
            # Log detailed information about each row containing non-numeric values
            logger.warning(f"\nRows with non-numeric values in column '{col}':")
            for _, row in non_numeric_rows.iterrows():
                logger.warning(f"Row {row.name}: {row.to_dict()}")
                
    return non_numeric


def cleanse_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the attendance data by replacing specific text values with numeric values.
    
    Args:
        df: DataFrame containing the attendance data
        
    Returns:
        DataFrame with cleaned data
    """
    # Create a copy to avoid modifying the original DataFrame
    df = df.copy()
    
    # Remove rows where Dover Athletic played in 2020-2021 season
    # This is a special case due to COVID-19 related issues
    original_rows = len(df)
    df = df[~(
        ((df['home_club'] == 'Dover Athletic') | 
         (df['away_club'] == 'Dover Athletic')) & 
        (df['season'] == '2020-2021')
    )]
    removed_rows = original_rows - len(df)
    logger.info(
        f"Removed {removed_rows} rows where Dover Athletic played in the "
        "2020-2021 season"
    )

    # Remove rows where away_goals is "- dnp" (did not play)
    df = df[df['away_goals'] != '- dnp']    

    # Replace "without spectators" with 0 in attendance column
    # This handles COVID-19 affected matches
    df['attendance'] = df['attendance'].replace('without spectators', '0')
    
    # Convert attendance column to numeric, coercing errors to NaN
    # This ensures all attendance values are numeric
    df['attendance'] = pd.to_numeric(df['attendance'], errors='coerce')

    # Rename match_day to match_day_of_week
    df = df.rename(columns={'match_day': 'match_day_of_week'})
    
    return df

if __name__ == "__main__":
    # Define input file path for the attendance data
    file_path = Path("../../RawData/Matches/WorldFootball_Attendance/worldfootball_attendance.csv")
    
    try:
        # Read the CSV data with low_memory=False to avoid dtype warnings
        # This is important for large datasets
        logger.info(f"Reading data from {file_path}")
        attendance4 = pd.read_csv(file_path, low_memory=False)
        
        # Clean the data by removing specific rows and normalizing values
        # This includes handling special cases and data type conversions
        logger.info("Cleaning data...")
        attendance4 = cleanse_data(attendance4)
        
        # Transform club names using reference mapping
        # This ensures consistent club naming across the dataset
        logger.info("Transforming club names...")
        attendance4 = transform_club_names(
            df=attendance4,
            source_name="home_club",
            target_name="home_club"
        )   
        attendance4 = transform_club_names(
            df=attendance4,
            source_name="away_club",
            target_name="away_club"
        )
        
        # Define columns to check for data quality issues
        # These are the critical columns that should not contain empty values
        empty_check_columns = [
            'season', 'league_tier', 'match_date', 'home_club',
            'away_club', 'home_goals', 'away_goals', 'attendance'
        ]
        
        # Define columns to check for non-numeric values
        # These columns should only contain numeric values
        numeric_check_columns = ['home_goals']
        
        # Check for and report empty rows
        # This helps identify data quality issues
        logger.info("Checking for empty rows...")
        empty_counts = check_empty_rows(attendance4, empty_check_columns)

        if empty_counts:
            logger.info("\nEmpty rows by column:")
            for col, count in empty_counts.items():
                logger.info(f"{col}: {count} empty rows")
        
        # Check for and report non-numeric values
        # This helps identify data quality issues
        logger.info("Checking for non-numeric values...")
        non_numeric_values = check_non_numeric(attendance4, numeric_check_columns)

        if non_numeric_values:  
            logger.info("\nNon-numeric values by column:")
            for col, values in non_numeric_values.items():
                logger.info(f"{col}: {values}")

        # Check club consistency
        # This ensures all club names are valid and consistent
        check_clubs_1(matches=attendance4, error_stop=True)
        check_clubs_2(matches=attendance4, error_stop=False)
            
        # Save the cleansed data to CSV
        # This creates the final output file
        logger.info("Saving values to CSV...")
        output_path = Path("../../CleansedData/Interim/worldfootball_attendance.csv")
        attendance4.to_csv(output_path, index=False)
        logger.info(f"Saved attendance4 values to {output_path}")
            
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}") 