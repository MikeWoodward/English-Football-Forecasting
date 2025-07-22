#!/usr/bin/env python3
"""
Heatmap animation Charts Visualization Module

This module provides functionality to read data and create animated heatmap
charts using matplotlib for data visualization and analysis. It creates
animated heatmaps showing score frequency distributions across different
seasons and league tiers.
"""

# Standard library imports for logging and system operations
import logging
import sys

# Third-party imports for data manipulation and visualization
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.animation import FuncAnimation

# Configure logging to track program execution and errors
# This sets up logging to display timestamps, log levels, and messages
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
        # Log the start of data reading process
        logger.info(f"Reading data from {file_path}")

        # Read CSV with low_memory=False to avoid dtype warnings
        # This prevents pandas from making assumptions about data types
        data = pd.read_csv(file_path, low_memory=False)

        # Log successful data loading with basic statistics
        logger.info(
            f"Successfully loaded {len(data)} rows and "
            f"{len(data.columns)} columns"
        )
        return data

    except FileNotFoundError as e:
        # Handle case where file doesn't exist
        # Log error with line number for debugging
        logger.error(
            f"File not found: {file_path} at line "
            f"{e.__traceback__.tb_lineno}"
        )
        raise

    except pd.errors.EmptyDataError as e:
        # Handle case where file is empty
        # This can happen if the CSV file has no data rows
        logger.error(
            f"File is empty: {file_path} at line "
            f"{e.__traceback__.tb_lineno}"
        )
        raise

    except pd.errors.ParserError as e:
        # Handle case where file cannot be parsed as CSV
        # This catches malformed CSV files
        logger.error(
            f"Error parsing CSV file: {file_path} at line "
            f"{e.__traceback__.tb_lineno}"
        )
        raise


def prepare_data(*, match_data: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare and modify the match data for heatmap visualization.

    This function processes raw match data to create score frequency
    distributions that can be visualized as heatmaps. It groups data by
    season and league tier, calculates score frequencies, and normalizes
    the data.

    Args:
        match_data: Raw match data DataFrame to be processed.

    Returns:
        Modified DataFrame ready for heatmap visualization with columns:
        - season: The football season
        - league_tier: The league tier/division
        - home_goals: Number of goals scored by home team
        - away_goals: Number of goals scored by away team
        - frequency: Normalized frequency of each score combination
    """
    try:
        # Log the start of data preparation process
        logger.info("Preparing data for heatmap visualization")

        # Create a copy to avoid modifying the original data
        # This prevents side effects on the input DataFrame
        prepared_data = match_data.copy()

        # Combine home and away goals into a single score string (e.g., "2-1")
        # This creates a unique identifier for each score combination
        prepared_data['score'] = (
            prepared_data['home_goals'].astype(str) + "-" +
            prepared_data['away_goals'].astype(str)
        )

        # Group by season, league tier, and score to count occurrences
        # This creates a frequency table of all score combinations
        # The result shows how many times each score occurred in each
        # season/tier
        score_frequencies = (
            prepared_data.groupby(["season", 'league_tier', 'score'])
            .agg(score_count=pd.NamedAgg(column='score', aggfunc='count'))
            .reset_index()
        )

        # Calculate total matches per season and league tier for normalization
        # This is needed to convert raw counts to relative frequencies
        normalize = score_frequencies.groupby(['season', 'league_tier']).agg(
            total_score_count=pd.NamedAgg(
                column='score_count', aggfunc='sum'
            )
        )

        # Merge the normalization data back to calculate relative frequencies
        # This joins the total counts with individual score counts
        score_frequencies = score_frequencies.merge(
            normalize, on=['season', 'league_tier'], how='left'
        )

        # Calculate normalized frequency (proportion of total matches)
        # This converts raw counts to percentages/proportions
        score_frequencies['frequency'] = (
            score_frequencies['score_count'] /
            score_frequencies['total_score_count']
        )

        # Split the score string back into separate home and away goal columns
        # for easier plotting and analysis
        # This extracts the numeric values from strings like "2-1"
        score_frequencies['home_goals'] = (
            score_frequencies['score'].str.split('-').str[0].astype(int)
        )
        score_frequencies['away_goals'] = (
            score_frequencies['score'].str.split('-').str[1].astype(int)
        )

        # Remove intermediate columns that are no longer needed
        # This cleans up the DataFrame for final output
        score_frequencies = score_frequencies.drop(
            columns=['score_count', 'total_score_count', 'score']
        )

        # Log completion of data preparation
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


def create_animated_heatmap(*, data: pd.DataFrame) -> None:
    """
    Create and display an animated heatmap chart.

    This function creates an animated heatmap showing how score frequencies
    change across different seasons for a specific league tier. The heatmap
    uses home goals on the x-axis, away goals on the y-axis, and frequency
    as the color intensity.

    Args:
        data: DataFrame containing the processed score frequency data.
    """
    try:
        # Select which league tier to visualize (can be modified)
        # This determines which league division to show in the animation
        league_tier = 1

        # Filter data for the selected league tier
        # This creates a subset containing only data for the specified tier
        data_tier = data[data['league_tier'] == league_tier]

        # Get the maximum values for setting axis limits and color scaling
        # These values are used to set consistent scales across all frames
        max_home_goals = data_tier['home_goals'].max()
        max_away_goals = data_tier['away_goals'].max()
        max_frequency = data_tier['frequency'].max()

        # Create dummy frame for missing home_goals and away_goals
        # This ensures all possible score combinations are represented
        # even if they didn't occur in the actual data
        dummy = pd.DataFrame(
            [[0] for a in range(0, max_home_goals + 1)
             for b in range(0, max_away_goals + 1)],
            columns=['frequency'],
            index=pd.MultiIndex.from_tuples(
                [(a, b) for a in range(0, max_home_goals + 1)
                 for b in range(0, max_away_goals + 1)],
                names=['home_goals', 'away_goals']
            )
        )

        # Get all unique seasons and sort them chronologically
        # This creates the sequence of frames for the animation
        seasons = np.sort(data_tier['season'].unique())

        def generate_data(season):
            """
            Generate a 2D array (pivot table) for a specific season.

            This function takes the score frequency data for a given season
            and creates a 2D array where rows represent away goals, columns
            represent home goals, and values are the frequencies.

            Args:
                season: The season to generate data for.

            Returns:
                2D numpy array representing the score frequency matrix.
            """
            # Filter data for the specific season
            # This extracts only the data for the current animation frame
            df = data_tier[
                (data_tier['season'] == season)
            ][['home_goals', 'away_goals', 'frequency']]

            # Fill in missing home_goals and away_goals by re-indexing and
            # adding zeros from the dummy frame. Do not remove na values.
            # This ensures the heatmap has consistent dimensions across all
            # frames
            df = df.set_index(['home_goals', 'away_goals'])
            df = df + dummy
            df = df.reset_index()

            # Create a pivot table and convert to numpy array
            # This creates a matrix where missing combinations are filled
            # with NaN, which will be displayed as empty cells in the
            # heatmap
            pivot_data = df.pivot(
                index='away_goals',
                columns='home_goals',
                values='frequency'
            ).to_numpy()
            return pivot_data

        # Create the main figure and set its size
        # The figure size determines the overall dimensions of the plot
        fig = plt.figure(figsize=(7, 5))

        # Add a main title for the entire figure
        # This provides context about what the animation shows
        title = f'Animated scores heatmaps for league tier {league_tier}'
        fig.suptitle(title, fontsize=16, fontweight='bold')

        # Create the subplot for the heatmap
        # This is where the actual heatmap will be displayed
        ax = fig.add_subplot(111)

        # Generate initial data for the first season
        # This creates the starting frame of the animation
        initial_data = generate_data(seasons[0])

        # Create the initial heatmap image
        # cmap='viridis' provides a good color scheme for frequency data
        # aspect='auto' allows the heatmap to stretch to fill the axes
        # animated=True enables animation updates
        # vmin/vmax set the color scale range for consistent coloring
        im = ax.imshow(
            initial_data,
            cmap='viridis',
            aspect='auto',
            animated=True,
            vmin=0,
            vmax=max_frequency
        )

        # Set the initial title and axis labels
        # These provide context for what the axes represent
        ax.set_title(f'Season: {seasons[0]}')
        ax.set_xlabel('Home Goals')
        ax.set_ylabel('Away Goals')

        # Set axis limits to match the data range
        # This ensures consistent scaling across all animation frames
        ax.set_xlim(-0.5, max_home_goals + 0.5)
        ax.set_ylim(-0.5, max_away_goals + 0.5)

        # Add a colorbar to show the frequency scale
        # This helps interpret the color intensity values
        plt.colorbar(im, ax=ax)

        def animate(frame):
            """
            Animation function called for each frame.

            This function updates the heatmap data and title for each season
            in the animation sequence.

            Args:
                frame: The current frame number (index into seasons array).

            Returns:
                List of artists that were modified (required for animation).
            """
            # Get the season for the current frame
            # This determines which season's data to display
            season = seasons[frame]

            # Generate new data for this season
            # This creates the frequency matrix for the current frame
            df = generate_data(season)

            # Update the heatmap data
            # This changes the color intensities to reflect the new season
            im.set_data(df)

            # Update the title to show the current season
            # This helps viewers track which season is being displayed
            ax.set_title(f'Season: {season}')

            # Return the modified artist (required for matplotlib animation)
            # This tells matplotlib which parts of the plot to redraw
            return [im]

        # Create and run the animation
        print("Creating animation... This may take a moment.")

        # FuncAnimation parameters:
        # - fig: The figure to animate
        # - animate: The function that updates each frame
        # - frames: Number of frames (one per season)
        # - interval: Time between frames in milliseconds (2 seconds)
        # - blit: Whether to use blitting for performance (False for
        #   heatmaps)
        # - repeat: Whether to loop the animation (False = play once)
        anim = FuncAnimation(
            fig,
            animate,
            frames=len(seasons),
            interval=2000,
            blit=False,
            repeat=False
        )

        # Save the animation as a GIF file
        # This creates a file that can be shared or embedded in documents
        # The filename includes the league tier for easy identification
        anim.save(
            f'heatmap_animation_league_tier_{league_tier}.gif',
            writer='pillow', fps=1
        )

        # Display the animation in a window
        # Uncomment the line below if you want to see the animation in a
        # window
        # plt.tight_layout()
        plt.show()

        # Inform user that animation is complete
        print("Animation complete! Close the window to end the program.")

    except Exception as e:
        # Handle any errors that occur during animation creation
        logger.error(
            f"Error creating 3D bar chart: {str(e)} at line "
            f"{e.__traceback__.tb_lineno}"
        )
        raise


if __name__ == "__main__":
    # Main execution block - this runs when the script is executed directly
    # This is the entry point for the program
    logger.info("Starting heatmap animation visualization")

    # Path to the data file containing match statistics
    # This should point to a CSV file with match data
    data_file = "Data/merged_match_data.csv"

    try:
        # Step 1: Read the raw match data from CSV file
        # This loads the initial data that will be processed
        match_data = read_data(file_path=data_file)

        # Display basic information about the loaded data
        # This helps verify that the data was loaded correctly
        logger.info(f"Data shape: {match_data.shape}")
        logger.info(f"Columns: {list(match_data.columns)}")

        # Step 2: Prepare the data for visualization
        # This processes the raw data into score frequency distributions
        # that can be used to create the heatmap
        score_frequencies = prepare_data(match_data=match_data)

        # Step 3: Create and display the animated heatmap
        # This generates the final visualization
        create_animated_heatmap(data=score_frequencies)

    except Exception as e:
        # Handle any errors that occur during execution
        # This ensures the program exits gracefully with an error message
        logger.error(
            f"Error in main execution: {str(e)} at line "
            f"{e.__traceback__.tb_lineno}"
        )
        sys.exit(1)
