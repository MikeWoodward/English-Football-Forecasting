# Import required libraries for data manipulation and visualization
import pandas as pd
import sys
import traceback
import os
# Import Bokeh components for creating interactive web-based visualizations
from bokeh.plotting import figure, show, output_file
from bokeh.models import (
    ColumnDataSource, CustomJS, Slider, ColorBar, LinearColorMapper
)
from bokeh.layouts import column, row
from bokeh.transform import transform
from bokeh.palettes import Viridis256
# Import logging for debugging and monitoring application behavior
import logging
from bokeh.embed import components

# Configure logging for debugging and monitoring
# Sets up logging to display timestamp, log level, and message
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
        # Log the file reading operation for debugging purposes
        logger.info(f"Reading data from {file_path}")
        # Read CSV file into pandas DataFrame with low_memory=False for
        # better performance
        data = pd.read_csv(file_path, low_memory=False)
        # Log successful data loading with dimensions for verification
        logger.info(
            f"Successfully loaded {len(data)} rows and "
            f"{len(data.columns)} columns"
        )
        return data
    except FileNotFoundError:
        # Handle missing file error with line number for debugging
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        logger.error(
            f"File not found: {file_path} at line {line_number}"
        )
        raise
    except pd.errors.EmptyDataError:
        # Handle empty file error with line number for debugging
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        logger.error(
            f"File is empty: {file_path} at line {line_number}"
        )
        raise
    except pd.errors.ParserError:
        # Handle CSV parsing error with line number for debugging
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        logger.error(
            f"Error parsing CSV file: {file_path} at line {line_number}"
        )
        raise


def prepare_data(*, match_data: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare and modify the match data for 3D visualization.

    This function processes raw match data to create frequency distributions
    of football scores across different seasons and league tiers.

    Args:
        match_data: Raw match data DataFrame to be processed.

    Returns:
        Modified DataFrame ready for 3D visualization with columns:
        season, league_tier, home_goals, away_goals, frequency.
    """
    try:
        # Log the start of data preparation process
        logger.info("Preparing data for 3D visualization")

        # Create a copy to avoid modifying the original data
        # (defensive programming practice)
        prepared_data = match_data.copy()

        # Combine home and away goals into a single score string for grouping
        # Format: "home_goals-away_goals" (e.g., "2-1", "0-0")
        prepared_data['score'] = (
            prepared_data['home_goals'].astype(str) + "-" +
            prepared_data['away_goals'].astype(str)
        )

        # Group by season, league tier, and score to count occurrences
        # This creates frequency data for each unique score combination
        score_frequencies = (
            prepared_data.groupby(["season", 'league_tier', 'score'])
            .agg(score_count=pd.NamedAgg(column='score', aggfunc='count'))
            .reset_index()
        )

        # Calculate total matches per season and league tier for normalization
        # This is needed to convert raw counts to proportions/frequencies
        normalize = score_frequencies.groupby(['season', 'league_tier']).agg(
            total_score_count=pd.NamedAgg(
                column='score_count', aggfunc='sum'
            )
        )
        # Merge total counts back to calculate frequencies
        # This joins the total counts with individual score counts
        score_frequencies = score_frequencies.merge(
            normalize, on=['season', 'league_tier'], how='left'
        )
        # Calculate frequency as proportion of total matches
        # This normalizes the data so frequencies sum to 1 for each
        # season/tier
        score_frequencies['frequency'] = (
            score_frequencies['score_count'] /
            score_frequencies['total_score_count']
        )
        # Extract home and away goals from score string for plotting
        # Split the "home-away" string and convert to integers for axis
        # labels
        score_frequencies['home_goals'] = (
            score_frequencies['score'].str.split('-').str[0].astype(int)
        )
        score_frequencies['away_goals'] = (
            score_frequencies['score'].str.split('-').str[1].astype(int)
        )
        # Remove temporary columns used for calculations to clean up the data
        score_frequencies = score_frequencies.drop(
            columns=['score_count', 'total_score_count']
        )

        # Log successful completion with final data shape
        logger.info(
            f"Data preparation complete. Shape: {prepared_data.shape}"
        )
        return score_frequencies

    except Exception as e:
        # Handle any unexpected errors during data preparation with line
        # number
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        logger.error(
            f"Error preparing data: {str(e)} at line {line_number}"
        )
        raise


def create_heatmap_plot(*,
                        league_tier: int,
                        plot_width: int,
                        plot_height: int,
                        max_frequency: float,
                        max_home_goals: int,
                        max_away_goals: int,
                        source_year: ColumnDataSource):
    """
    Create the main heatmap plot with all visual elements.

    This function creates a single heatmap plot for a specific league tier
    with proper styling, color mapping, and axis configuration.

    Args:
        league_tier: The league tier to display (1 = top tier).
        plot_width: Width of the plot in pixels.
        plot_height: Height of the plot in pixels.
        max_frequency: Maximum frequency value for color scaling.
        max_home_goals: Maximum home goals for axis limits.
        max_away_goals: Maximum away goals for axis limits.
        source_year: ColumnDataSource for current year data.

    Returns:
        plot_1: The created Bokeh plot object.
    """
    # Create the main Bokeh figure with specified dimensions and styling
    plot_1 = figure(
        title=f"Score Frequency - Tier {league_tier}",
        x_axis_label="Home Goals",
        y_axis_label="Away Goals",
        width=plot_width,
        height=plot_height,
        toolbar_location="above"
    )

    # Set up color mapping using Viridis palette for consistent
    # visualization
    # This maps frequency values to colors (0 = light, max_frequency =
    # dark)
    color_mapper = LinearColorMapper(
        palette=Viridis256,
        low=0,
        high=max_frequency
    )

    # Create rectangular elements for the heatmap
    # Each rectangle represents a score combination (home_goals vs
    # away_goals)
    # The color intensity represents the frequency of that score
    plot_1.rect(
        x='home_goals',
        y='away_goals',
        width=1,
        height=1,
        source=source_year,
        fill_color=transform('frequency', color_mapper),
        line_color='white',
        line_width=1
    )

    # Configure axis properties for better visualization
    # Set tick marks to show integer values for goals
    plot_1.xaxis.ticker = list(range(max_home_goals + 1))
    plot_1.yaxis.ticker = list(range(max_away_goals + 1))
    # Remove grid lines for cleaner appearance
    plot_1.xgrid.visible = False
    plot_1.ygrid.visible = False
    # Set axis limits with small padding for better visual spacing
    plot_1.x_range.start = -0.5
    plot_1.x_range.end = max_home_goals + 0.5
    plot_1.y_range.start = -0.5
    plot_1.y_range.end = max_away_goals + 0.5

    return plot_1


def plot_heatmap(*, score_frequency,
                 output_filename="football_scores_heatmap.html"):
    """
    Create and display an interactive football score frequency heatmap.

    This function creates an interactive Bokeh heatmap visualization that
    shows the frequency of different football score combinations. Users
    can interact with a slider to view data from different years.

    Args:
        score_frequency (pd.DataFrame): DataFrame containing football score
            frequency data with columns: season, league_tier, home_goals,
            away_goals, frequency.
        output_filename (str): Name of the HTML file to save the
            visualization.

    Returns:
        None: Displays the heatmap in browser and saves to HTML file.
    """

    # Calculate data ranges for axis scaling and slider configuration
    # Extract start year from season strings (e.g., "1888-1889" -> 1888)
    score_frequency['start_year'] = (
        score_frequency['season'].str.split('-').str[0].astype(int)
    )

    # Define plot dimensions for consistent layout
    plot_height = 450
    plot_width = 550

    # Set the initial year to display (most recent year)
    start_year = 2024

    # Filter data to only include the specified league tier (1 = top tier)
    # Note: This line appears to be incomplete in the original code

    # Get the maximum frequency for color scaling across all data
    max_frequency = score_frequency['frequency'].max()
    # Get the maximum home and away goals for axis limits
    max_home_goals = score_frequency['home_goals'].max()
    max_away_goals = score_frequency['away_goals'].max()

    # Create Bokeh data sources for interactive functionality
    # source_all contains all data for filtering by year
    source_1_all = ColumnDataSource(
        score_frequency[score_frequency['league_tier'] == 1]
    )
    source_2_all = ColumnDataSource(
        score_frequency[score_frequency['league_tier'] == 2]
    )
    source_3_all = ColumnDataSource(
        score_frequency[score_frequency['league_tier'] == 3]
    )
    source_4_all = ColumnDataSource(
        score_frequency[score_frequency['league_tier'] == 4]
    )

    # source contains only the data for the currently selected year
    # These will be updated dynamically when the slider changes
    source_1_year = ColumnDataSource(
        score_frequency[(score_frequency['league_tier'] == 1) &
                        (score_frequency['start_year'] == start_year)]
    )
    source_2_year = ColumnDataSource(
        score_frequency[(score_frequency['league_tier'] == 2) &
                        (score_frequency['start_year'] == start_year)]
    )
    source_3_year = ColumnDataSource(
        score_frequency[(score_frequency['league_tier'] == 3) &
                        (score_frequency['start_year'] == start_year)]
    )
    source_4_year = ColumnDataSource(
        score_frequency[(score_frequency['league_tier'] == 4) &
                        (score_frequency['start_year'] == start_year)]
    )

    # Create the heatmap plots for each league tier using the helper
    # function
    # Each plot shows a different league tier in a 2x2 grid layout
    plot_1 = create_heatmap_plot(
        league_tier=1,
        plot_width=int(plot_width/2),
        plot_height=int(plot_height/2),
        max_frequency=max_frequency,
        max_home_goals=max_home_goals,
        max_away_goals=max_away_goals,
        source_year=source_1_year
    )

    plot_2 = create_heatmap_plot(
        league_tier=2,
        plot_width=int(plot_width/2),
        plot_height=int(plot_height/2),
        max_frequency=max_frequency,
        max_home_goals=max_home_goals,
        max_away_goals=max_away_goals,
        source_year=source_2_year
    )

    plot_3 = create_heatmap_plot(
        league_tier=3,
        plot_width=int(plot_width/2),
        plot_height=int(plot_height/2),
        max_frequency=max_frequency,
        max_home_goals=max_home_goals,
        max_away_goals=max_away_goals,
        source_year=source_3_year
    )

    plot_4 = create_heatmap_plot(
        league_tier=4,
        plot_width=int(plot_width/2),
        plot_height=int(plot_height/2),
        max_frequency=max_frequency,
        max_home_goals=max_home_goals,
        max_away_goals=max_away_goals,
        source_year=source_4_year
    )

    # Create interactive slider for year selection
    # Users can drag this to view data from different years
    year_slider = Slider(
        start=score_frequency['start_year'].min(),
        end=score_frequency['start_year'].max(),
        value=start_year,
        step=1,
        title="Season (Start Year)",
        width=plot_width
    )

    # Custom JavaScript callback function for interactive updates
    # This function runs when the user moves the year slider
    callback_1 = CustomJS(
        args=dict(source_1_year=source_1_year,
                  source_2_year=source_2_year,
                  source_3_year=source_3_year,
                  source_4_year=source_4_year,
                  source_1_all=source_1_all,
                  source_2_all=source_2_all,
                  source_3_all=source_3_all,
                  source_4_all=source_4_all,
                  plot_1=plot_1,
                  plot_2=plot_2,
                  plot_3=plot_3,
                  plot_4=plot_4),
        code="""
        // Get the selected year from the slider
        const year = this.value;
        const all_1_data = source_1_all.data;
        const all_2_data = source_2_all.data;
        const all_3_data = source_3_all.data;
        const all_4_data = source_4_all.data;

        // Initialize empty arrays for the filtered data
        const new_1_data = {
            home_goals: [],
            away_goals: [],
            frequency: []
        };
        const new_2_data = {
            home_goals: [],
            away_goals: [],
            frequency: []
        };
        const new_3_data = {
            home_goals: [],
            away_goals: [],
            frequency: []
        };
        const new_4_data = {
            home_goals: [],
            away_goals: [],
            frequency: []
        };

        // Filter data for the selected year
        // Loop through all data points and only keep those matching the
        // year
        for (let i = 0; i < all_1_data.start_year.length; i++) {
            if (all_1_data.start_year[i] === year) {
                new_1_data.home_goals.push(all_1_data.home_goals[i]);
                new_1_data.away_goals.push(all_1_data.away_goals[i]);
                new_1_data.frequency.push(all_1_data.frequency[i]);
            }
        }
        for (let i = 0; i < all_2_data.start_year.length; i++) {
            if (all_2_data.start_year[i] === year) {
                new_2_data.home_goals.push(all_2_data.home_goals[i]);
                new_2_data.away_goals.push(all_2_data.away_goals[i]);
                new_2_data.frequency.push(all_2_data.frequency[i]);
            }
        }
        for (let i = 0; i < all_3_data.start_year.length; i++) {
            if (all_3_data.start_year[i] === year) {
                new_3_data.home_goals.push(all_3_data.home_goals[i]);
                new_3_data.away_goals.push(all_3_data.away_goals[i]);
                new_3_data.frequency.push(all_3_data.frequency[i]);
            }
        }
        for (let i = 0; i < all_4_data.start_year.length; i++) {
            if (all_4_data.start_year[i] === year) {
                new_4_data.home_goals.push(all_4_data.home_goals[i]);
                new_4_data.away_goals.push(all_4_data.away_goals[i]);
                new_4_data.frequency.push(all_4_data.frequency[i]);
            }
        }

        // Update the data source with filtered data
        source_1_year.data = new_1_data;
        source_2_year.data = new_2_data;
        source_3_year.data = new_3_data;
        source_4_year.data = new_4_data;

        // Trigger the plot to redraw with new data
        source_1_year.change.emit();
        source_2_year.change.emit();
        source_3_year.change.emit();
        source_4_year.change.emit();
        """
    )

    # Connect the JavaScript callback to the slider
    # This makes the heatmap interactive by updating when slider changes
    year_slider.js_on_change('value', callback_1)

    # Create color mapper for the color bar (same as used in plots)
    color_mapper = LinearColorMapper(
        palette=Viridis256,
        low=0,
        high=max_frequency
    )

    # Create color bar to show the frequency scale
    color_bar = ColorBar(
        color_mapper=color_mapper,
        width=8,
        location=(0, 0),
        title="Frequency"
    )
    # Create a separate figure to hold the color bar
    color_bar_fig = figure(
        width=30, height=plot_height, toolbar_location=None,
        outline_line_color=None
    )
    color_bar_fig.add_layout(color_bar, 'right')
    # Hide axes and grid for clean color bar display
    color_bar_fig.axis.visible = False
    color_bar_fig.grid.visible = False

    # Create the final layout with plots in a 2x2 grid and slider below
    # The color bar is positioned to the right of the plots
    layout = row(column(
        row(plot_1, plot_2),
        row(plot_3, plot_4),
        year_slider
    ), color_bar_fig)

    # Save the interactive visualization to an HTML file
    output_file(os.path.join("Plots", output_filename))

    # Extract and save the JavaScript and HTML components separately
    # This allows for embedding the visualization in other web pages
    for index, plot in enumerate([layout]):
        script, div = components(plot)
        with open(f"Plots/script_{index}.txt", "w") as f:
            f.write(script)
            f.write("\n")
        with open(f"Plots/div_{index}.txt", "w") as f:
            f.write("<div align='center'>\n")
            f.write(div)
            f.write("\n</div>")

    # Display the interactive plot in the browser
    show(layout)


if __name__ == "__main__":
    # Main execution block - only runs if script is executed directly
    logger.info("Starting 3D bar chart visualization")

    # Define the input data file path relative to the script location
    data_file = "Data/merged_match_data.csv"

    try:
        # Read the match data from CSV file using the read_data function
        match_data = read_data(file_path=data_file)

        # Prepare the data for visualization using the prepare_data function
        prepared_data = prepare_data(match_data=match_data)

        # Create and display the heatmap
        plot_heatmap(score_frequency=prepared_data)
    except Exception as e:
        # Handle any errors in the main execution flow with line number
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        logger.error(
            f"Error in main execution: {str(e)} at line {line_number}"
        )
        # Exit with error code 1 to indicate failure
        sys.exit(1)
