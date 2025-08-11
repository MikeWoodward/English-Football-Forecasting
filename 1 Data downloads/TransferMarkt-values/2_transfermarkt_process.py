"""
2_transfermarkt_process.py - TransferMarkt Data Processing Script

This script processes the downloaded TransferMarkt data files and prepares them
for analysis. It performs the following operations:
- Combines all CSV files from different seasons and tiers
- Cleans and standardizes the data
- Converts market values to numeric format
- Handles missing data and outliers
- Creates a consolidated dataset ready for analysis

Data Structure:
- Input: Multiple CSV files in Data-Download/ directory
- Output: Single processed CSV file with cleaned data

Usage:
    python 2_transfermarkt_process.py

Dependencies:
    - pandas: For data manipulation
    - numpy: For numerical operations
    - os: For file operations
    - logging: For logging operations
    
Author: Mike Woodward
Date: March 2024
Version: 1.0
"""

import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime
from pathlib import Path


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
    log_dir = 'Log'
    os.makedirs(log_dir, exist_ok=True)
    
    # Create timestamped log filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = os.path.join(
        log_dir, 
        f'transfermarkt_process_{timestamp}.log'
    )
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
    
    logging.info(f"Logging initialized. Log file: {log_filename}")


def get_data(
    *,
    data_folder: str = 'Data-Download'
) -> pd.DataFrame:
    """
    Read all CSV files from the specified data folder and merge them into a 
    single pandas DataFrame.
    
    This function searches for all CSV files in the data folder, reads each one,
    and concatenates them into a single DataFrame. It handles potential encoding
    issues and provides detailed logging of the process.
    
    Args:
        data_folder: Path to the folder containing CSV files. 
                    Defaults to 'Data-Download'.
    
    Returns:
        pd.DataFrame: Combined DataFrame containing all CSV data.
    
    Raises:
        FileNotFoundError: If the data folder doesn't exist.
        ValueError: If no CSV files are found in the folder.
    """
    # Check if data folder exists
    if not os.path.exists(data_folder):
        raise FileNotFoundError(
            f"Data folder '{data_folder}' not found at line "
            f"{get_data.__code__.co_firstlineno + 15}"
        )
    
    # Get all CSV files in the folder
    csv_files = [
        f for f in os.listdir(data_folder) 
        if f.endswith('.csv') and not f.startswith('.')
    ]
    
    if not csv_files:
        raise ValueError(
            f"No CSV files found in '{data_folder}' at line "
            f"{get_data.__code__.co_firstlineno + 22}"
        )
    
    logging.info(f"Found {len(csv_files)} CSV files in {data_folder}")
    
    # List to store all dataframes
    dataframes = []
    
    # Read each CSV file
    for csv_file in csv_files:
        try:
            file_path = os.path.join(data_folder, csv_file)
            logging.info(f"Reading file: {csv_file}")
            
            # Read CSV with error handling for encoding. squad_size, foreigner_count are ints. 
            # mean_age is a float so we need to convert it to int. total_market_value is a 
            # string for now, so we need to convert it to float.
            df = pd.read_csv(
                file_path,
                encoding='utf-8',
                on_bad_lines='warn',
                dtype={
                    'squad_size': int, 
                    'foreigner_count': int, 
                    'mean_age': float
                },
                na_values=['-', '']
            )
            
            # Convert total_market_value from string to float
            # Handle 'bn' (billions), 'm' (millions), and 'k' (thousands) suffixes
            market_values = df['total_market_value'].copy()
            
            # Remove currency symbols and commas
            market_values = market_values.replace({'\\$': '', '€': '', ',': ''}, regex=True)
            
            # Handle billions (bn)
            billions_mask = market_values.str.contains('bn', case=False, na=False)
            market_values[billions_mask] = (
                market_values[billions_mask]
                .str.replace('bn', '', case=False, regex=False)
                .astype(float) * 1_000_000_000
            )
            
            # Handle millions (m)
            millions_mask = market_values.str.contains('m', case=False, na=False)
            market_values[millions_mask] = (
                market_values[millions_mask]
                .str.replace('m', '', case=False, regex=False)
                .astype(float) * 1_000_000
            )
            
            # Handle billions (bn)
            billions_mask = market_values.str.contains('bn', case=False, na=False)
            market_values[billions_mask] = (
                market_values[billions_mask]
                .str.replace('bn', '', case=False, regex=False)
                .astype(float) * 1_000_000_000
            )
            # Handle thousands (k)
            thousands_mask = market_values.str.contains('k', case=False, na=False)
            market_values[thousands_mask] = (
                market_values[thousands_mask]
                .str.replace('k', '', case=False, regex=False)
                .astype(float) * 1_000
            )
            
            # Handle values without suffix (assume millions)
            no_suffix_mask = ~(billions_mask | millions_mask | thousands_mask)
            # Only convert non-NaN values
            valid_values = market_values[no_suffix_mask].dropna()
            if not valid_values.empty:
                market_values[no_suffix_mask] = market_values[no_suffix_mask].astype(float)
            
            df['total_market_value'] = market_values
            
            # Add filename as a column for tracking
            df['source_file'] = csv_file
            
            dataframes.append(df)
            logging.info(
                f"Successfully read {csv_file} with {len(df)} rows"
            )
            
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            try:
                df = pd.read_csv(
                    file_path,
                    encoding='latin-1',
                    on_bad_lines='warn',
                    dtype={
                        'squad_size': int, 
                        'foreigner_count': int, 
                        'mean_age': float
                    },
                    na_values=['-', '']
                )
                
                                                        # Convert total_market_value from string to float
            # Handle 'bn' (billions), 'm' (millions), 'k' (thousands), and missing values
            def convert_market_value(value):
                if pd.isna(value) or value == '':
                    return np.nan
                
                # Convert to string and handle NaN values
                try:
                    value_str = str(value).lower()
                except:
                    return np.nan
                
                # Remove currency symbols and commas
                value_str = value_str.replace('$', '').replace('€', '').replace(',', '')
                
                if 'bn' in value_str:
                    return float(value_str.replace('bn', '')) * 1_000_000_000
                elif 'm' in value_str:
                    return float(value_str.replace('m', '')) * 1_000_000
                elif 'k' in value_str:
                    return float(value_str.replace('k', '')) * 1_000
                else:
                    return float(value_str)
            
            # Apply conversion to all values
            df['total_market_value'] = df['total_market_value'].apply(convert_market_value)
            
            # Add filename as a column for tracking
            df['source_file'] = csv_file
            
            dataframes.append(df)
            logging.info(
                f"Successfully read {csv_file} with {len(df)} rows"
            )
            except Exception as e:
                logging.error(
                    f"Failed to read {csv_file} at line "
                    f"{e.__traceback__.tb_lineno}: {e}"
                )
                raise
        except Exception as e:
            logging.error(
                f"Failed to read {csv_file} at line "
                f"{e.__traceback__.tb_lineno}: {e}"
            )
            raise
    
    # Concatenate all dataframes
    if dataframes:
        combined_df = pd.concat(
            dataframes,
            ignore_index=True,
            sort=False
        )
        
        # Sort the dataframe by season, league_tier, and club_name
        combined_df = combined_df.sort_values(
            by=['season', 'league_tier', 'club_name'],
            ascending=[True, True, True]
        ).reset_index(drop=True)
        
        logging.info(
            f"Successfully combined {len(dataframes)} files into "
            f"DataFrame with {len(combined_df)} total rows"
        )
        logging.info(
            f"DataFrame sorted by season, league_tier, and club_name"
        )
        return combined_df
    else:
        raise ValueError(
            f"No valid CSV files could be read from '{data_folder}' at line "
            f"{get_data.__code__.co_firstlineno + 85}"
        )




if __name__ == "__main__":
    # Set up logging
    setup_logging()
    
    logging.info("Starting TransferMarkt data processing...")
    
    try:
        # Load and combine all CSV data
        logging.info("Loading data from CSV files...")
        combined_data = get_data()
        
        logging.info(f"Data loaded successfully. Shape: {combined_data.shape}")
        logging.info(f"Columns: {list(combined_data.columns)}")
        logging.info(f"Sample data:\n{combined_data.head()}")
        
        logging.info("TransferMarkt data processing completed successfully")
        
    except Exception as e:
        logging.error(
            f"Fatal error in main processing at line "
            f"{e.__traceback__.tb_lineno}: {e}"
        )
        exit(1)
