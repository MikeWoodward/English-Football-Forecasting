#!/usr/bin/env python3
"""
FootballWebPages attendance data cleansing script.

This script reads FootballWebPages attendance CSV files from the RawData
directory, transforms club names, and outputs
the cleansed data to the CleansedData directory.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import List
from utilities import transform_club_names

# Configure logging with timestamp, module name, and log level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_footballwebpages_files(*, data_dir: Path) -> pd.DataFrame:
    """
    Read all FootballWebPages attendance CSV files into a single DataFrame.
    
    Args:
        data_dir (Path): Path to the directory containing CSV files.
        
    Returns:
        pd.DataFrame: Combined DataFrame from all CSV files.
        
    Raises:
        FileNotFoundError: If the data directory doesn't exist.
        ValueError: If no CSV files are found or if data loading fails.
    """
    logger.info(f"Reading FootballWebPages files from {data_dir}")
    
    # Check if directory exists
    if not data_dir.exists():
        error_msg = f"Data directory not found: {data_dir}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    # Get all CSV files in the directory
    csv_files = list(data_dir.glob("*.csv"))
    
    if not csv_files:
        error_msg = f"No CSV files found in {data_dir}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Found {len(csv_files)} CSV files to process")
    
    # Read and combine all CSV files
    dataframes: List[pd.DataFrame] = []
    
    for csv_file in sorted(csv_files):
        try:
            logger.info(f"Reading {csv_file.name}")
            df = pd.read_csv(csv_file)
            dataframes.append(df)
            logger.info(f"Successfully read {csv_file.name}: {df.shape}")
        except Exception as e:
            error_msg = (
                f"Error reading {csv_file.name} at line {e.__traceback__.tb_lineno}: "
                f"{str(e)}"
            )
            logger.error(error_msg)
            raise
    
    # Combine all dataframes
    combined_df = pd.concat(dataframes, ignore_index=True)
    logger.info(f"Combined DataFrame shape: {combined_df.shape}")
    
    return combined_df


def main() -> None:
    """
    Main function to cleanse FootballWebPages attendance data.
    
    Reads CSV files, transforms club names, and outputs cleansed data.
    Stops processing if club name transformation fails.
    """
    try:
        # Define input and output paths
        input_dir = Path("../../RawData/Matches/FootballWebPages_Attendance")
        output_file = Path("../../CleansedData/Interim/footballwebpages.csv")
        
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Read all FootballWebPages files
        fwb = read_footballwebpages_files(data_dir=input_dir)
        
        logger.info("Transforming home club names...")
        fwb = transform_club_names(
            df=fwb,
            source_name="home_club",
            target_name="home_club"
        )
        
        logger.info("Transforming away club names...")
        fwb = transform_club_names(
            df=fwb,
            source_name="away_club",
            target_name="away_club"
        )
        
        # Output the cleansed data
        logger.info(f"Writing cleansed data to {output_file}")
        fwb.to_csv(output_file, index=False)
        logger.info(f"Successfully wrote {len(fwb)} records to {output_file}")
        
    except Exception as e:
        logger.error(f"Error in main function at line {e.__traceback__.tb_lineno}: {str(e)}")
        raise


if __name__ == "__main__":
    main() 