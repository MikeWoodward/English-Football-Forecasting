#!/usr/bin/env python3
"""
3D Bar Charts Visualization Module

This module provides functionality to read data and create 3D bar charts
using matplotlib for data visualization and analysis.
"""

import logging
import sys

# Import required libraries for data manipulation and visualization
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.animation import FuncAnimation

# Configure logging with timestamp, level, and message format
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
        # Read CSV file into pandas DataFrame
        data = pd.read_csv(file_path)
        # Log successful data loading with row and column counts
        logger.info(
            f"Successfully loaded {len(data)} rows and "
            f"{len(data.columns)} columns"
        )
        return data
    except FileNotFoundError as e:
        # Handle case where file doesn't exist
        logger.error(
            f"File not found: {file_path} at line "
            f"{e.__traceback__.tb_lineno}"
        )
        raise
    except pd.errors.EmptyDataError as e:
        # Handle case where file is empty
        logger.error(
            f"File is empty: {file_path} at line "
            f"{e.__traceback__.tb_lineno}"
        )
        raise
    except pd.errors.ParserError as e:
        # Handle case where file cannot be parsed as CSV
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

        # Combine home and away goals into a single score column (e.g., "2-1")
        prepared_data['score'] = (
            prepared_data['home_goals'].astype(str) + "-" +
            prepared_data['away_goals'].astype(str)
        )

        # Group data by season, league tier, and score to count occurrences
        # This creates a frequency table of score combinations
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
        # Merge the total counts back to the score frequencies
        score_frequencies = score_frequencies.merge(
            normalize, on=['season', 'league_tier'], how='left'
        )
        # Calculate frequency as proportion of total matches
        score_frequencies['frequency'] = (
            score_frequencies['score_count'] /
            score_frequencies['total_score_count']
        )
        # Extract home goals from score string (before the dash)
        score_frequencies['home_goals'] = (
            score_frequencies['score'].str.split('-').str[0].astype(int)
        )
        # Extract away goals from score string (after the dash)
        score_frequencies['away_goals'] = (
            score_frequencies['score'].str.split('-').str[1].astype(int)
        )
        # Remove intermediate columns, keeping only the final processed data
        score_frequencies = score_frequencies.drop(
            columns=['score_count', 'total_score_count', 'score']
        )

        logger.info(
            f"Data preparation complete. Shape: {prepared_data.shape}"
        )
        return score_frequencies

    except Exception as e:
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
        # Set the league tier to visualize (1 = Premier League)
        league_tier = 5

        # Filter data to only include the specified league tier
        data_tier = data[data['league_tier'] == league_tier]

        # Get the maximum values for setting consistent axis limits
        max_home_goals = data_tier['home_goals'].max()
        max_away_goals = data_tier['away_goals'].max()
        max_frequency = data_tier['frequency'].max()

        # Get unique seasons and sort them chronologically
        seasons = np.sort(data_tier['season'].unique())

        # Create the figure and 3D axis
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        # Define bar dimensions for 3D visualization
        bar_width = 1  # x-axis dimension (home goals)
        bar_depth = 1  # y-axis dimension (away goals)

        # Animation function that updates the chart for each frame
        def animate(frame):
            # Get the season for the current frame
            season = seasons[frame]
            # Filter data for the current season and league tier
            data_season_tier = data_tier[data_tier['season'] == season]

            # Calculate bar positions (centered on grid points)
            # Subtract half bar width/depth to center bars on grid positions
            xpos = [x - bar_width/2 for x in
                    data_season_tier['home_goals'].to_list()]
            ypos = [y - bar_depth/2 for y in
                    data_season_tier['away_goals'].to_list()]
            # All bars start from z=0 (ground level)
            zpos = np.zeros_like(xpos)
            # Bar heights are determined by frequency values
            dz = data_season_tier['frequency'].to_list()

            # Clear the previous frame
            ax.clear()

            # Create 3D bars with specified dimensions and styling
            ax.bar3d(x=xpos,           # x positions (home goals)
                     y=ypos,           # y positions (away goals)
                     z=zpos,           # z starting positions (all at 0)
                     dx=bar_width,     # bar width in x direction
                     dy=bar_depth,     # bar depth in y direction
                     dz=dz,            # bar height in z direction (frequency)
                     color='lightcoral',    # bar color
                     alpha=0.8,        # transparency level
                     edgecolor='black',     # bar edge color
                     linewidth=0.5)    # edge line thickness

            # Set axis labels and title
            ax.set_xlabel('Home Goals')
            ax.set_ylabel('Away Goals')
            ax.set_zlabel('Frequency')
            ax.set_title(
                f'Score frequencies for league tier {league_tier} in {season}'
            )

            # Set consistent axis limits across all frames for smooth animation
            ax.set_xlim(-bar_width, max_home_goals + bar_width)
            # Note: y-axis is inverted to match typical football score display
            ax.set_ylim(max_away_goals + bar_depth, -bar_depth)
            ax.set_zlim(0, max_frequency)

            return ax

        # Create animation with specified parameters
        anim = FuncAnimation(
            fig, animate, frames=len(seasons), interval=1000, blit=False
        )

        # Save animation as GIF file
        anim.save(
            f'3d_bar_animation_{league_tier}.gif',
            writer='pillow',
            fps=1
        )

        # Display the animation
        plt.show()

    except Exception as e:
        logger.error(
            f"Error creating 3D bar chart: {str(e)} at line "
            f"{e.__traceback__.tb_lineno}"
        )
        raise


if __name__ == "__main__":
    # Main execution block - only runs if script is executed directly
    logger.info("Starting 3D bar chart visualization")

    # Define the path to the data file
    data_file = "Data/merged_match_data.csv"

    try:
        # Step 1: Read the raw match data from CSV file
        match_data = read_data(file_path=data_file)

        # Step 2: Display basic information about the loaded data
        logger.info(f"Data shape: {match_data.shape}")
        logger.info(f"Columns: {list(match_data.columns)}")

        # Step 3: Prepare the data for 3D visualization
        # This includes calculating score frequencies and normalizing data
        score_frequencies = prepare_data(match_data=match_data)

        # Step 4: Create and display the 3D animated bar chart
        create_3d_bar_chart(data=score_frequencies)

    except Exception as e:
        # Handle any errors that occur during execution
        logger.error(
            f"Error in main execution: {str(e)} at line "
            f"{e.__traceback__.tb_lineno}"
        )
        # Exit with error code 1 to indicate failure
        sys.exit(1)
