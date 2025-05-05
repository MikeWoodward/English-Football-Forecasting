"""Script to analyze attendance data for data quality issues.

This script reads the attendance data file and reports on:
1. Empty rows in specified columns
2. Non-numeric characters in numeric columns
"""

import pandas as pd
from pathlib import Path
import logging
from typing import List, Dict, Any

# Configure logging
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
    empty_counts = {}
    for col in columns:
        empty_count = df[col].isna().sum()
        empty_counts[col] = empty_count
        if empty_count > 0:
            logger.warning(f"Column '{col}' has {empty_count} empty rows")
    return empty_counts

def check_non_numeric(df: pd.DataFrame, columns: List[str]) -> Dict[str, List[Any]]:
    """Check for non-numeric characters in specified columns.
    
    Args:
        df: DataFrame to analyze
        columns: List of column names to check
        
    Returns:
        Dictionary with column names as keys and lists of non-numeric values as values
    """
    non_numeric = {}
    for col in columns:
        # Convert to string and check if it can be converted to numeric
        non_numeric_mask = df[col].astype(str).str.match(r'[^0-9.]')
        non_numeric_rows = df[non_numeric_mask]
        
        if not non_numeric_rows.empty:
            non_numeric_values = non_numeric_rows[col].unique()
            non_numeric[col] = non_numeric_values.tolist()
            logger.warning(f"Column '{col}' contains non-numeric values: {non_numeric_values}")
            
            # Print out the full rows containing non-numeric values
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
    # Remove rows where Dover Athletic played in 2020-2021 season
    df = df.copy()  # Create an explicit copy to avoid SettingWithCopyWarning
    original_rows = len(df)
    df = df[~(
        ((df['home_club'] == 'Dover Athletic') | (df['away_club'] == 'Dover Athletic')) & 
        (df['season'] == '2020-2021')
    )]
    removed_rows = original_rows - len(df)
    logger.info(f"Removed {removed_rows} rows where Dover Athletic played in the 2020-2021 season")

    # Remove "away_goals" column where the value is "- dnp"
    df = df[df['away_goals'] != '- dnp']    

    # Replace "without spectators" with 0 in the attendance column
    df['attendance'] = df['attendance'].replace('without spectators', '0')
    
    # Convert attendance column to numeric
    df['attendance'] = pd.to_numeric(df['attendance'], errors='coerce')
    
    return df

def transform_club_names(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize club names using a reference mapping.
    
    Args:
        df: DataFrame containing attendance data with club names to normalize
        
    Returns:
        DataFrame with normalized club names
    """
    # Load club name normalization mapping
    club_normalization_path = Path("../../CleansedData/Corrections and normalization/club_name_normalization.csv")
    try:    
        club_normalization = pd.read_csv(club_normalization_path)
    except FileNotFoundError:
        logger.error(f"File not found: {club_normalization_path}")
        return df
    
    # Normalize home club names
    df = df.merge(
        club_normalization,
        left_on='home_club',
        right_on='club_name',
        how='left'
    )
    df = df.drop(columns=['home_club', 'club_name'])
    df = df.rename(columns={'club_name_normalized': 'home_club'})
    
    # Normalize away club names
    df = df.merge(
        club_normalization,
        left_on='away_club',
        right_on='club_name',
        how='left'
    )
    df = df.drop(columns=['away_club', 'club_name'])
    df = df.rename(columns={'club_name_normalized': 'away_club'})
    
    return df

def main() -> None:
    """Main function to analyze attendance data."""
    # Define file path
    file_path = Path("../../RawData/Matches/Attendance4/attendance4.csv")
    
    try:
        # Read the data
        logger.info(f"Reading data from {file_path}")
        attendance4 = pd.read_csv(file_path, low_memory=False)
        
        # Clean the data
        logger.info("Cleaning data...")
        attendance4 = cleanse_data(attendance4)
        
        # Transform club names
        logger.info("Transforming club names...")
        attendance4 = transform_club_names(attendance4)
        
        # Columns to check for empty rows
        empty_check_columns = [
            'season', 'league_tier', 'match_date', 'home_club',
            'away_club', 'home_goals', 'away_goals', 'attendance'
        ]
        
        # Columns to check for non-numeric values
        numeric_check_columns = ['home_goals']#, 'away_goals', 'attendance']
        
        # Check for empty rows
        logger.info("Checking for empty rows...")
        empty_counts = check_empty_rows(attendance4, empty_check_columns)
        
        # Check for non-numeric values
        logger.info("Checking for non-numeric values...")
        non_numeric_values = check_non_numeric(attendance4, numeric_check_columns)

        # Print summary
        logger.info("\nSummary of findings:")
        logger.info("\nEmpty rows by column:")
        for col, count in empty_counts.items():
            logger.info(f"{col}: {count} empty rows")
            
        logger.info("\nNon-numeric values by column:")
        for col, values in non_numeric_values.items():
            logger.info(f"{col}: {values}")
            
        # Convert non_numeric_values to DataFrame and save
        logger.info("Saving non-numeric values to CSV...")
        output_path = Path("../../CleansedData/Interim/attendance4.csv")
        attendance4.to_csv(output_path, index=False)
        logger.info(f"Saved attendance4 values to {output_path}")
            
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 