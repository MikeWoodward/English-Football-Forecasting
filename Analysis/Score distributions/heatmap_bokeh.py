import pandas as pd
import sys
import traceback
import os
from bokeh.plotting import figure, show, output_file
from bokeh.models import (
    ColumnDataSource, CustomJS, Slider, ColorBar, LinearColorMapper, Div
)
from bokeh.layouts import column, row
from bokeh.transform import transform
from bokeh.palettes import Viridis256
import logging
from bokeh.embed import file_html, components

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
        # Read CSV file into pandas DataFrame
        data = pd.read_csv(file_path, low_memory=False)
        # Log successful data loading with dimensions for verification
        logger.info(
            f"Successfully loaded {len(data)} rows and "
            f"{len(data.columns)} columns"
        )
        return data
    except FileNotFoundError:
        # Handle missing file error with line number
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        logger.error(
            f"File not found: {file_path} at line {line_number}"
        )
        raise
    except pd.errors.EmptyDataError:
        # Handle empty file error with line number
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        logger.error(
            f"File is empty: {file_path} at line {line_number}"
        )
        raise
    except pd.errors.ParserError:
        # Handle CSV parsing error with line number
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        logger.error(
            f"Error parsing CSV file: {file_path} at line {line_number}"
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
        # Log the start of data preparation process
        logger.info("Preparing data for 3D visualization")

        # Create a copy to avoid modifying the original data
        # (defensive programming)
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
        # This normalizes the data so frequencies sum to 1 for each season/tier
        score_frequencies['frequency'] = (
            score_frequencies['score_count'] /
            score_frequencies['total_score_count']
        )
        # Extract home and away goals from score string for plotting
        # Split the "home-away" string and convert to integers for axis labels
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
        # Handle any unexpected errors during data preparation with line number
        exc_type, exc_value, exc_traceback = sys.exc_info()
        line_number = traceback.extract_tb(exc_traceback)[-1].lineno
        logger.error(
            f"Error preparing data: {str(e)} at line {line_number}"
        )
        raise


def plot_heatmap(*, score_frequency, output_filename="football_scores_heatmap.html"):
    """
    Create and display an interactive football score frequency heatmap.

    This function creates an interactive Bokeh heatmap visualization that shows
    the frequency of different football score combinations. Users can interact
    with a slider to view data from different years.

    Args:
        score_frequency (pd.DataFrame): DataFrame containing football score 
            frequency data with columns: season, league_tier, home_goals, 
            away_goals, frequency.
        output_filename (str): Name of the HTML file to save the visualization.

    Returns:
        None: Displays the heatmap in browser and saves to HTML file.
    """

    # Height and width of the plot
    plot_height = 450
    plot_width = 550

    # Filter data to only include the specified league tier (1 = top tier)
    league_tier = 1
    df = score_frequency[score_frequency['league_tier'] == league_tier]

    # Calculate data ranges for axis scaling and slider configuration
    # Extract start year from season strings (e.g., "1888-1889" -> 1888)
    df = df.copy()
    df['start_year'] = df['season'].str.split('-').str[0].astype(int)
    min_year = df['start_year'].min()
    max_year = df['start_year'].max()
    # Get the maximum frequency for color scaling
    max_frequency = df['frequency'].max()
    # Get the maximum home and away goals for axis limits
    max_home_goals = df['home_goals'].max()
    max_away_goals = df['away_goals'].max()

    # Create Bokeh data sources for interactive functionality
    # source_all contains all data for filtering
    source_all = ColumnDataSource(df)
    # source contains only the data for the currently selected year
    initial_data = df[df['start_year'] == min_year]
    source = ColumnDataSource(initial_data)

    # Create the main Bokeh figure with specified dimensions and styling
    p = figure(
        title=f"Football Score Frequency Heatmap - Tier {league_tier}",
        x_axis_label="Home Goals",
        y_axis_label="Away Goals",
        width=plot_width,
        height=plot_height, 
        toolbar_location="above"
    )

    # Set up color mapping using Viridis palette for consistent visualization
    # This maps frequency values to colors (0 = light, max_frequency = dark)
    color_mapper = LinearColorMapper(
        palette=Viridis256,
        low=0,
        high=max_frequency
    )

    # Create rectangular elements for the heatmap
    # Each rectangle represents a score combination (home_goals vs away_goals)
    # The color intensity represents the frequency of that score
    p.rect(
        x='home_goals',
        y='away_goals',
        width=1,
        height=1,
        source=source,
        fill_color=transform('frequency', color_mapper),
        line_color='white',
        line_width=1
    )

    # Add color bar to show the mapping between colors and frequency values
    color_bar = ColorBar(
        color_mapper=color_mapper,
        width=8,
        location=(0, 0),
        title="Frequency"
    )
    p.add_layout(color_bar, 'right')

    # Configure axis properties for better visualization
    # Set tick marks to show integer values for goals
    p.xaxis.ticker = list(range(max_home_goals + 1))
    p.yaxis.ticker = list(range(max_away_goals + 1))
    # Remove grid lines for cleaner appearance
    p.xgrid.visible = False
    p.ygrid.visible = False
    # Set axis limits
    p.x_range.start = -0.5
    p.x_range.end = max_home_goals + 0.5
    p.y_range.start = -0.5
    p.y_range.end = max_away_goals + 0.5

    # Create interactive slider for year selection
    # Users can drag this to view data from different years
    year_slider = Slider(
        start=min_year,
        end=max_year,
        value=min_year,
        step=1,
        title="Season (Start Year)",
        width=plot_width-120
    )

    # Custom JavaScript callback function for interactive updates
    # This function runs when the user moves the year slider
    callback = CustomJS(
        args=dict(source=source, source_all=source_all, plot=p),
        code="""
        // Get the selected year from the slider
        const year = this.value;
        const all_data = source_all.data;
        
        // Initialize empty arrays for the filtered data
        const new_data = {
            home_goals: [],
            away_goals: [],
            frequency: []
        };

        // Filter data for the selected year
        // Loop through all data points and only keep those matching the year
        for (let i = 0; i < all_data.start_year.length; i++) {
            if (all_data.start_year[i] === year) {
                new_data.home_goals.push(all_data.home_goals[i]);
                new_data.away_goals.push(all_data.away_goals[i]);
                new_data.frequency.push(all_data.frequency[i]);
            }
        }

        // Update the data source with filtered data
        source.data = new_data;

        // Update plot title to reflect the selected year
        plot.title.text = "Football Score Frequency Heatmap - " + year;

        // Trigger the plot to redraw with new data
        source.change.emit();
        """
    )

    # Connect the JavaScript callback to the slider
    # This makes the heatmap interactive
    year_slider.js_on_change('value', callback)

    # Create the final layout by arranging components
    # Put the slider in a row and stack it below the plot
    slider_row = row(Div(text="""""", width=35), 
                     year_slider,
                     Div(text="""""", width=85))
    layout = column(p, slider_row)

    # Save the interactive visualization to an HTML file
    output_file(os.path.join("Plots", output_filename))

    for index, plot in enumerate([layout]):
        script, div = components(plot)
        with open(f"Plots/script_{index}.txt", "w") as f:
            f.write(script)
        with open(f"Plots/div_{index}.txt", "w") as f:
            f.write(div)

    # Display the interactive plot in the browser
    show(layout)

    # Print informative messages about the visualization
    print(
        f"Football scores heatmap has been created and saved as "
        f"'{output_filename}'"
    )
    print(
        "The heatmap shows the frequency of different score combinations "
        "in football matches."
    )
    print(
        "Use the year slider to see how score patterns change from "
        "1980 to 2020."
    )
    print(
        "Darker colors indicate higher frequency of that particular "
        "score combination."
    )


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
