#!/usr/bin/env python3
"""
Extract ground names from matches attendance data.

This script reads the matches_attendance.csv file and extracts ground names
for further processing in the EPL predictor database creation pipeline.
"""

import logging
import pandas as pd
from pathlib import Path
import sys


def setup_logging() -> None:
    """Configure logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ground_extraction.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def read_matches_data(*, file_path: str = '../2 Data preparation/Data/matches_attendance.csv') -> pd.DataFrame:
    """
    Read matches attendance data from CSV file.
    
    Args:
        file_path: Path to the matches_attendance.csv file
        
    Returns:
        pandas.DataFrame: The matches data
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        pd.errors.EmptyDataError: If the CSV file is empty
        pd.errors.ParserError: If the CSV file cannot be parsed
    """
    try:
        logging.info(f"Reading matches data from {file_path}")
        matches = pd.read_csv(file_path)
        logging.info(f"Successfully loaded {len(matches)} records")
        return matches
    except FileNotFoundError as e:
        logging.error(f"File not found at line {e.__traceback__.tb_lineno}: "
                     f"{file_path}")
        raise
    except pd.errors.EmptyDataError as e:
        logging.error(f"Empty data file at line {e.__traceback__.tb_lineno}: "
                     f"{file_path}")
        raise
    except pd.errors.ParserError as e:
        logging.error(f"CSV parsing error at line {e.__traceback__.tb_lineno}: "
                     f"{str(e)}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error at line {e.__traceback__.tb_lineno}: "
                     f"{str(e)}")
        raise


def main() -> None:
    """Main function to extract ground names from matches data."""
    setup_logging()
    
    try:
        # Read the matches data
        matches = read_matches_data()
        
        # Display basic information about the dataset
        logging.info(f"Dataset shape: {matches.shape}")
        logging.info(f"Columns: {list(matches.columns)}")
        
        # Display first few rows
        logging.info("First 5 rows of the dataset:")
        logging.info(f"\n{matches.head()}")
        
        # Check for ground-related columns
        ground_columns = [col for col in matches.columns 
                         if 'ground' in col.lower() or 'venue' in col.lower()]
        
        if ground_columns:
            logging.info(f"Found ground-related columns: {ground_columns}")
        else:
            logging.info("No obvious ground-related columns found")
            
    except Exception as e:
        logging.error(f"Script failed at line {e.__traceback__.tb_lineno}: "
                     f"{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
