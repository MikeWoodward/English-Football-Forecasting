#!/usr/bin/env python3
"""
3D Bar Charts Visualization Module

This module provides functionality to read data and create 3D bar charts
using matplotlib for data visualization and analysis.
"""

import logging
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Configure logging for debugging and monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_data(*, file_path: str) -> pd.DataFrame:
    """
    Read data from CSV file.

    Args:
        file_path: Path to the CSV file to read.

    Returns:
        DataFrame containing the loaded data.

    Raises:
        FileNotFoundError: If the specified file doesn't exist.
        pd.errors.EmptyDataError: If the file is empty.
        pd.errors.ParserError: If the file cannot be parsed as CSV.
    """
    try:
        # Log the file reading operation
        logger.info(f"Reading data from {file_path}")
        data = pd.read_csv(file_path)
        # Log successful data loading with dimensions
        logger.info(
            f"Successfully loaded {len(data)} rows and "
            f"{len(data.columns)} columns"
        )
        return data
    except FileNotFoundError as e:
        # Handle missing file error with line number
        logger.error(
            f"File not found: {file_path} at line "
            f"{e.__traceback__.tb_lineno}"
        )
        raise
    except pd.errors.EmptyDataError as e:
        # Handle empty file error with line number
        logger.error(
            f"File is empty: {file_path} at line "
            f"{e.__traceback__.tb_lineno}"
        )
        raise
    except pd.errors.ParserError as e:
        # Handle CSV parsing error with line number
        logger.error(
            f"Error parsing CSV file: {file_path} at line "
            f"{e.__traceback__.tb_lineno}"
        )
        raise


def prepare_data(*, match_data: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare and modify the match data for 3D visualization.

    Args:
        match_data: Raw match data DataFrame to be processed.

    Returns:
        Modified DataFrame ready for 3D visualization.
    """
    try:
        logger.info("Preparing data for 3D visualization")

        # Create a copy to avoid modifying the original data
        prepared_data = match_data.copy()

        # Combine home and away goals into a single score string
        prepared_data['score'] = (
            prepared_data['home_goals'].astype(str) + "-" +
            prepared_data['away_goals'].astype(str)
        )

        # Group by season, league tier, and score to count occurrences
        score_frequencies = (
            prepared_data.groupby(["season", 'league_tier', 'score'])
            .agg(score_count=pd.NamedAgg(column='score', aggfunc='count'))
            .reset_index()
        )

        # Calculate total matches per season and league tier for normalization
        normalize = score_frequencies.groupby(['season', 'league_tier']).agg(
            total_score_count=pd.NamedAgg(
                column='score_count', aggfunc='sum'
            )
        )
        # Merge total counts back to calculate frequencies
        score_frequencies = score_frequencies.merge(
            normalize, on=['season', 'league_tier'], how='left'
        )
        # Calculate frequency as proportion of total matches
        score_frequencies['frequency'] = (
            score_frequencies['score_count'] /
            score_frequencies['total_score_count']
        )
        # Extract home and away goals from score string for plotting
        score_frequencies['home_goals'] = (
            score_frequencies['score'].str.split('-').str[0].astype(int)
        )
        score_frequencies['away_goals'] = (
            score_frequencies['score'].str.split('-').str[1].astype(int)
        )
        # Remove temporary columns used for calculations
        score_frequencies = score_frequencies.drop(
            columns=['score_count', 'total_score_count']
        )

        logger.info(
            f"Data preparation complete. Shape: {prepared_data.shape}"
        )
        return score_frequencies

    except Exception as e:
        # Handle any unexpected errors during data preparation
        logger.error(
            f"Error preparing data: {str(e)} at line "
            f"{e.__traceback__.tb_lineno}"
        )
        raise


def create_3d_bar_chart(*, data: pd.DataFrame) -> None:
    """
    Create and display a 3D bar chart.

    Args:
        data: DataFrame containing the data to plot.
    """
    try:
        # Define chart settings for different seasons and league tiers
        settings = [
            {
                'season': '1960-1961',  # Early season for comparison
                'league_tier': 1,
                'position': 121,  # Subplot position (1 row, 2 columns, pos 1)
                'max_home_goals': 0,  # Will be calculated dynamically
                'max_away_goals': 0   # Will be calculated dynamically
            },
            {
                'season': '2024-2025',  # Recent season for comparison
                'league_tier': 1,
                'position': 122,  # Subplot position (1 row, 2 columns, pos 2)
                'max_home_goals': 0,  # Will be calculated dynamically
                'max_away_goals': 0   # Will be calculated dynamically
            }
        ]

        # Initialize variables to track maximum values across all charts
        max_home_goals = 0
        max_away_goals = 0
        max_frequency = 0

        # First pass: calculate maximum values for consistent scaling
        for setting in settings:
            # Filter data for current season and league tier
            plot_data = data[data['season'] == setting['season']]
            plot_data = plot_data[
                plot_data['league_tier'] == setting['league_tier']
            ]
            # Update maximum values for consistent axis scaling
            max_home_goals = max(max_home_goals, plot_data['home_goals'].max())
            max_away_goals = max(max_away_goals, plot_data['away_goals'].max())
            max_frequency = max(max_frequency, plot_data['frequency'].max())

        # Second pass: update settings with calculated maximums
        for setting in settings:
            setting['max_home_goals'] = max_home_goals
            setting['max_away_goals'] = max_away_goals

        # Create the main figure for all subplots
        fig = plt.figure(figsize=(9, 4))

        # Loop over each chart setting to create subplots
        for setting in settings:

            # Filter data for current season and league tier
            plot_data = data[data['season'] == setting['season']]
            plot_data = plot_data[
                plot_data['league_tier'] == setting['league_tier']
            ]

            # Extract data for 3D plotting
            x_data = plot_data['home_goals'].to_list()  # X-axis: home goals
            y_data = plot_data['away_goals'].to_list()  # Y-axis: away goals
            z_data = np.zeros_like(x_data)  # Z-axis base: all bars start at 0
            dx = np.ones_like(x_data)   # Bar width: all bars have width 1
            dy = np.ones_like(y_data)   # Bar depth: all bars have depth 1
            dz = plot_data['frequency'].to_list()  # Bar height: frequency

            # Create 3D subplot with specified position
            ax = fig.add_subplot(setting['position'], projection='3d')

            # Set axis limits for consistent scaling across charts
            ax.set_ylim(setting['max_away_goals'] + 1, 0)  # Reverse Y-axis
            # X-axis with padding
            ax.set_xlim(0, setting['max_home_goals'] + 1)
            ax.set_zlim(0, max_frequency + 0.01)  # Z-axis with padding

            # Create 3D bars with specified properties
            ax.bar3d(
                x_data,  # X coordinates of bar centers
                y_data,  # Y coordinates of bar centers
                z_data,  # Z coordinates of bar bases
                dx,      # Bar widths
                dy,      # Bar depths
                dz,      # Bar heights
                color='lightcoral',  # Bar color
                shade=True  # Enable shading for 3D effect
            )

            # Set axis labels and title for the subplot
            ax.set_xlabel('Home Goals')
            ax.set_ylabel('Away Goals')
            ax.set_zlabel('Frequency')
            ax.set_title(
                f'Season: {setting["season"]}, '
                f'\nLeague Tier: {setting["league_tier"]}'
            )

        # Display all charts
        plt.show()

        logger.info("Successfully created 3D bar chart")

    except Exception as e:
        # Handle any errors during chart creation
        logger.error(
            f"Error creating 3D bar chart: {str(e)} at line "
            f"{e.__traceback__.tb_lineno}"
        )
        raise


if __name__ == "__main__":
    # Main execution block
    logger.info("Starting 3D bar chart visualization")

    # Define the input data file path
    data_file = "Data/merged_match_data.csv"

    try:
        # Read the match data from CSV file
        match_data = read_data(file_path=data_file)

        # Display basic information about the loaded data
        logger.info(f"Data shape: {match_data.shape}")
        logger.info(f"Columns: {list(match_data.columns)}")

        # Transform the raw data into frequency data for visualization
        score_frequencies = prepare_data(match_data=match_data)

        # Create and display the 3D bar charts
        create_3d_bar_chart(data=score_frequencies)

    except Exception as e:
        # Handle any errors in the main execution flow
        logger.error(
            f"Error in main execution: {str(e)} at line "
            f"{e.__traceback__.tb_lineno}"
        )
        # Exit with error code 1 to indicate failure
        sys.exit(1)
