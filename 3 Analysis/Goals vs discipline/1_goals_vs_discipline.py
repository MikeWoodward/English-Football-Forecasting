"""
Goals vs Discipline Analysis Module.

This module contains functions for analyzing the relationship between
goals and discipline in the EPL predictor project.
"""

import logging
import os
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def chart_data(*, data_source: str) -> None:
    """
    Create charts for goals vs discipline analysis.
    
    This function will generate visualizations showing the relationship
    between goals scored and disciplinary actions in the dataset.
    
    Args:
        data_source: Path to the data source file or database connection.
    
    Returns:
        None: This function will display or save charts directly.
    
    Raises:
        FileNotFoundError: If the data source file is not found.
        ValueError: If the data source is invalid or empty.
    """
    # TODO: Implement chart creation logic
    pass


if __name__ == "__main__":
    # Example usage
    try:
        # Read in data
        csv_path =os.path.join("..",
                                   "..",
                                   "Data preparation",
                                   "Data",
                                   "matches_attendance_discipline.csv")
        
        logger.info(f"Reading data from {csv_path}")
        matches = pd.read_csv(csv_path, low_memory=False)

        # Select only the rows that have discipline data: home_red_cards, away_red_cards etc.
        matches = matches[matches["home_red_cards"].notna() 
                          & matches["away_red_cards"].notna()
                          & matches["home_yellow_cards"].notna()
                          & matches["away_yellow_cards"].notna()
                          & matches["home_fouls"].notna()
                          & matches["away_fouls"].notna()]


        chart_data(data_source="path/to/data.csv")
    except Exception as e:
        logger.error(f"Error in main execution at line {e.__traceback__.tb_lineno}: {e}")
        raise
