"""
Grid plot module for 3D chart experiments.

This module is intended for creating grid-based visualizations.
"""

# Standard library imports for logging and system operations
import logging

from bokeh.plotting import figure, show, gridplot

# Third-party imports for data manipulation and visualization
import pandas as pd

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


def plot_score(*, data_tier: pd.DataFrame, home_goals: int, away_goals: int,
               max_frequency: float, min_start_year: int,
               max_start_year: int) -> figure:
    """
    Create a single score plot showing frequency over time.

    This function creates a minimal line plot showing how the frequency
    of a specific score combination (home_goals vs away_goals) changed
    over time.

    Args:
        data_tier: DataFrame containing filtered data for a specific league
        tier.
        home_goals: Number of home goals for the score combination.
        away_goals: Number of away goals for the score combination.
        max_frequency: Maximum frequency value for consistent y-axis scaling.
        min_start_year: Minimum year for x-axis range.
        max_start_year: Maximum year for x-axis range.

    Returns:
        Bokeh figure object representing the score plot.
    """
    # Filter data for specific home and away goal combination
    plot_data = data_tier[
        (data_tier['home_goals'] == home_goals) &
        (data_tier['away_goals'] == away_goals)
    ]

    # Create a line plot of frequency vs year
    plot = figure(
        title=None,
        width=80,
        height=80,
        # Remove tools
        tools="",
        toolbar_location=None
    )
    plot.line(plot_data['start_year'], plot_data['frequency'])

    plot.x_range.start = min_start_year
    plot.x_range.end = max_start_year
    plot.y_range.start = 0
    plot.y_range.end = max_frequency

    # Don't show x or y -axis
    plot.xaxis.visible = False
    plot.yaxis.visible = False

    plot.toolbar.logo = None

    # Add text annotation
    plot.text(
        x=[min_start_year],
        y=[max_frequency * 0.9],
        text=[f"Home: {home_goals}, Away: {away_goals}"],
        text_font_size="12px",
        text_color="black"
    )

    return plot


def create_grid_plot(*, data: pd.DataFrame) -> None:
    """
    Create a grid plot of the score frequencies.

    This function creates a grid of line plots showing how score frequencies
    change over time for different home and away goal combinations.

    Args:
        data: DataFrame containing processed score frequency data.
    """
    try:
        # Select league tier to visualize
        league_tier = 1
        data_tier = data[data['league_tier'] == league_tier]
        data_tier['start_year'] = (
            data_tier['season'].str.split('-').str[0].astype(int)
        )

        # Get maximum goals for grid dimensions
        max_home_goals = data_tier['home_goals'].max()
        max_away_goals = data_tier['away_goals'].max()
        max_frequency = data_tier['frequency'].max()
        min_start_year = data_tier['start_year'].min()
        max_start_year = data_tier['start_year'].max()

        logger.info(
            f"Creating grid plot for league tier {league_tier} with "
            f"max home goals: {max_home_goals}, max away goals: "
            f"{max_away_goals}"
        )

        # Create a grid of plots
        plots = []
        for ag in range(max_away_goals + 1):
            row = []
            for hg in range(max_home_goals + 1):
                # Filter data for specific home and away goal combination
                plot_data = data_tier[
                    (data_tier['home_goals'] == hg) &
                    (data_tier['away_goals'] == ag)
                ]

                # Create figure for this score combination
                plot = plot_score(
                    data_tier=data_tier,
                    home_goals=hg,
                    away_goals=ag,
                    max_frequency=max_frequency,
                    min_start_year=min_start_year,
                    max_start_year=max_start_year
                )

                row.append(plot)
            plots.insert(0, row)

        # Create the grid layout
        grid = gridplot(plots, width=200, height=150)

        # Show the grid plot
        show(grid)

        logger.info("Grid plot created and displayed successfully")

    except Exception as e:
        # Handle any errors during grid plot creation
        logger.error(
            f"Error creating grid plot: {str(e)} at line "
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

        # Step 3: Prepare the data for grid plot visualization
        # This includes calculating score frequencies and normalizing data
        score_frequencies = prepare_data(match_data=match_data)

        # Step 4: Create and display the grid plot
        create_grid_plot(data=score_frequencies)

    except Exception as e:
        # Handle any errors that occur during execution
        logger.error(f"Error: {str(e)}")
        raise
