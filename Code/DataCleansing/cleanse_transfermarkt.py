#!/usr/bin/env python3
"""
Transfermarkt attendance data cleansing script.

This script reads Transfermarkt attendance CSV files from the RawData directory,
transforms club names, and outputs the result to the CleansedData directory.
"""

import logging
import pandas as pd
from pathlib import Path
from glob import glob
from utilities import transform_club_names

# Configure logging with timestamp, module name, and log level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_transfermarkt_files(*, data_path: str) -> pd.DataFrame:
    """
    Read all Transfermarkt attendance CSV files into a single DataFrame.
    
    Args:
        data_path (str): Path to the directory containing CSV files.
        
    Returns:
        pd.DataFrame: Combined DataFrame from all CSV files.
        
    Raises:
        FileNotFoundError: If no CSV files are found in the directory.
        pd.errors.EmptyDataError: If any CSV file is empty.
        Exception: For other file reading errors.
    """
    logger.info(f"Reading Transfermarkt files from: {data_path}")
    
    # Get all CSV files in the directory
    csv_files = glob(f"{data_path}/*.csv")
    
    if not csv_files:
        error_msg = f"No CSV files found in {data_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    logger.info(f"Found {len(csv_files)} CSV files")
    
    # Read and combine all CSV files
    dataframes = []
    for file_path in csv_files:
        try:
            logger.info(f"Reading file: {Path(file_path).name}")
            df = pd.read_csv(file_path)
            
            if df.empty:
                logger.warning(f"Empty file: {Path(file_path).name}")
                continue
                
            dataframes.append(df)
            logger.info(
                f"Successfully read {len(df)} rows from "
                f"{Path(file_path).name}"
            )
            
        except pd.errors.EmptyDataError:
            error_msg = f"Empty CSV file: {file_path}"
            logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = (
                f"Error reading file {file_path} at line "
                f"{getattr(e, 'lineno', 'unknown')}: {str(e)}"
            )
            logger.error(error_msg)
            raise
    
    if not dataframes:
        error_msg = "No valid data found in any CSV files"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Combine all dataframes
    combined_df = pd.concat(dataframes, ignore_index=True)
    logger.info(f"Combined DataFrame shape: {combined_df.shape}")
    
    return combined_df


def transform_club_names_with_validation(*, df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform home_club and away_club names using the utilities function.
    
    Args:
        df (pd.DataFrame): DataFrame containing club name columns.
        
    Returns:
        pd.DataFrame: DataFrame with transformed club names.
        
    Raises:
        ValueError: If club name transformation fails.
    """
    logger.info("Transforming home_club names...")
    
    # Transform home_club names
    df = transform_club_names(
        df=df,
        source_name="home_club",
        target_name="home_club"
    )
    
    # Check for unmatched home clubs
    unmatched_home = df[df['home_club'].isna()]['home_club'].unique()
    if len(unmatched_home) > 0:
        error_msg = f"Could not transform home_club names: {unmatched_home}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("Transforming away_club names...")
    
    # Transform away_club names
    df = transform_club_names(
        df=df,
        source_name="away_club",
        target_name="away_club"
    )
    
    # Check for unmatched away clubs
    unmatched_away = df[df['away_club'].isna()]['away_club'].unique()
    if len(unmatched_away) > 0:
        error_msg = f"Could not transform away_club names: {unmatched_away}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Rename the column match_day to match_day_of_week
    df = df.rename(columns={"match_day": "match_day_of_week"})

    logger.info("Club name transformation completed successfully")
    return df


def save_cleansed_data(*, df: pd.DataFrame, output_path: str) -> None:
    """
    Save the cleansed DataFrame to a CSV file.
    
    Args:
        df (pd.DataFrame): DataFrame to save.
        output_path (str): Path where the CSV file should be saved.
        
    Raises:
        Exception: If file writing fails.
    """
    logger.info(f"Saving cleansed data to: {output_path}")
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved {len(df)} rows to {output_path}")
    except Exception as e:
        error_msg = (
            f"Error writing file {output_path} at line "
            f"{getattr(e, 'lineno', 'unknown')}: {str(e)}"
        )
        logger.error(error_msg)
        raise


def main() -> None:
    """
    Main function to orchestrate the Transfermarkt data cleansing process.
    
    Reads CSV files, transforms club names, and saves the cleansed data.
    """
    logger.info("Starting Transfermarkt data cleansing process")
    
    try:
        # Define file paths
        input_path = "../../RawData/Matches/Transfermarkt_Attendance"
        output_path = "../../CleansedData/Interim/transfermarkt.csv"
        
        # Read all CSV files into a single DataFrame
        tfm = read_transfermarkt_files(data_path=input_path)
        
        # Transform club names
        tfm = transform_club_names_with_validation(df=tfm)
        
        # Save cleansed data
        save_cleansed_data(df=tfm, output_path=output_path)
        
        logger.info("Transfermarkt data cleansing completed successfully")
        
    except Exception as e:
        logger.error(f"Data cleansing failed: {str(e)}")
        raise


if __name__ == "__main__":
    main() 