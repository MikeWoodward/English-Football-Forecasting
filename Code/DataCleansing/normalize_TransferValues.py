"""Module for normalizing transfer values data from various CSV files.

This module provides functionality to read and process transfer values data from multiple
CSV files and normalize club names using a reference mapping.
"""

import os
from pathlib import Path
from typing import Optional

import pandas as pd
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_market_value(value: str) -> float:
    """Clean market value string and convert to float.

    Args:
        value (str): Market value string (e.g., '€44.65m', '€775k', '€1.05bn', or '-')

    Returns:
        float: Cleaned market value in millions of euros, or None for missing values
    """
    try:
        if value == '-':
            return None
            
        # Remove the euro symbol
        cleaned = value.replace('€', '')
        
        # Convert based on suffix
        if cleaned.endswith('bn'):
            # Convert billions to millions (e.g., 1.05bn -> 1050.0)
            number = float(cleaned.replace('bn', ''))
            return number * 1000
        elif cleaned.endswith('m'):
            # Convert millions (e.g., 44.65m -> 44.65)
            return float(cleaned.replace('m', ''))
        elif cleaned.endswith('k'):
            # Convert thousands to millions (e.g., 775k -> 0.775)
            return float(cleaned.replace('k', '')) / 1000
        else:
            return float(cleaned)
    except (ValueError, AttributeError) as e:
        logger.warning(f"Could not convert market value '{value}': {str(e)}")
        return None

def read_club_names_normalized(file_path: str = "../../CleansedData/Corrections and normalization/club_name_normalization.csv") -> pd.DataFrame:
    """Read and load the club name normalization mapping from CSV.

    Args:
        file_path (str): Path to the club name normalization CSV file.
            Defaults to "../../CleansedData/Corrections and normalization/club_name_normalization.csv".

    Returns:
        pd.DataFrame: DataFrame containing the club name normalization mapping.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        pd.errors.EmptyDataError: If the CSV file is empty.
    """
    try:
        club_names_normalized = pd.read_csv(file_path)
        logger.info(f"Successfully loaded club name normalization data from {file_path}")
        return club_names_normalized
    except FileNotFoundError:
        logger.error(f"Club name normalization file not found: {file_path}")
        raise
    except pd.errors.EmptyDataError:
        logger.error(f"Club name normalization file is empty: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading club name normalization file: {str(e)}")
        raise

def read_transfer_values(
    club_names_normalized: pd.DataFrame,
    input_dir: str = "../../RawData/Matches/TransferValues",
    output_dir: str = "../../CleansedData/Interim",
    output_file: str = "transfer-values.csv"
) -> Optional[pd.DataFrame]:
    """Read all transfer value CSV files from a directory and combine them into a single DataFrame.

    Args:
        club_names_normalized (pd.DataFrame): DataFrame containing the club name normalization mapping.
        input_dir (str): Directory containing transfer value CSV files.
            Defaults to "../../RawData/Matches/TransferValues".
        output_dir (str): Directory to save the combined DataFrame.
            Defaults to "../../CleansedData/Interim".
        output_file (str): Name of the output CSV file.
            Defaults to "transfer-values.csv".

    Returns:
        Optional[pd.DataFrame]: Combined DataFrame containing all transfer values,
            or None if no files were found or an error occurred.

    Raises:
        FileNotFoundError: If the input directory does not exist.
    """
    try:
        # Ensure input directory exists
        if not os.path.exists(input_dir):
            logger.error(f"Input directory does not exist: {input_dir}")
            raise FileNotFoundError(f"Directory not found: {input_dir}")

        # Get list of all CSV files in the directory
        csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
        
        if not csv_files:
            logger.warning(f"No CSV files found in {input_dir}")
            return None

        # Read and combine all CSV files
        dfs = []
        for file in csv_files:
            try:
                file_path = os.path.join(input_dir, file)
                df = pd.read_csv(file_path)
                dfs.append(df)
                logger.debug(f"Successfully read {file}")
            except Exception as e:
                logger.error(f"Error reading file {file}: {str(e)}")
                continue

        if not dfs:
            logger.error("No data frames were successfully read")
            return None

        # Combine all DataFrames
        transfer_values = pd.concat(dfs, ignore_index=True)
        logger.info(f"Successfully combined {len(dfs)} CSV files")

        # Normalize club names using the mapping
        transfer_values = transfer_values.merge(
            club_names_normalized[['club_name', 'club_name_normalized']],
            how='left',
            left_on='club_name',
            right_on='club_name'
        )
        
        # Drop original club_name column and rename club_name_normalized
        transfer_values = transfer_values.drop(columns=['club_name'])
        transfer_values = transfer_values.rename(columns={'club_name_normalized': 'club_name'})
        
        # Drop 'league' column
        transfer_values = transfer_values.drop(columns=['league'])
        
        # Rename columns
        transfer_values = transfer_values.rename(columns={
            'tier': 'league_tier',
            'total_market_value': 'total_market_value(euros-m)'
        })
        
        # Clean market value data
        transfer_values['total_market_value(euros-m)'] = transfer_values['total_market_value(euros-m)'].apply(clean_market_value)
        
        logger.info("Successfully normalized club names and cleaned market value data")

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Save combined DataFrame
        output_path = os.path.join(output_dir, output_file)
        transfer_values.to_csv(output_path, index=False)
        logger.info(f"Successfully saved combined transfer values to {output_path}")

        return transfer_values

    except Exception as e:
        logger.error(f"Error processing transfer values: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        # Read club name normalization data
        club_names_df = read_club_names_normalized()
        
        # Process transfer values with club name normalization
        transfer_values_df = read_transfer_values(club_names_df)
        
        if transfer_values_df is not None:
            print(f"Successfully processed {len(transfer_values_df)} transfer value records")
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}") 