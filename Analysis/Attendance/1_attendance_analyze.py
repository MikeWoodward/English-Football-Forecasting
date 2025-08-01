# Standard library imports for data manipulation and system operations
import pandas as pd
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Tuple

# Bokeh imports for interactive plotting and visualization
import bokeh
from bokeh.plotting import figure
from bokeh.layouts import column, row
from bokeh.io import show
from bokeh.embed import components
from bokeh.palettes import Category10
from bokeh.models import BoxAnnotation

from bokeh.models import (
    ColumnDataSource, CustomJS, Slider, ColorBar, LinearColorMapper, Div, HoverTool
)

# Scientific computing imports for statistical analysis
import numpy as np
from scipy import stats

# Browser automation for opening generated plots
import webbrowser


def setup_logging() -> logging.Logger:
    """
    Sets up logging configuration and creates Logs directory.

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create Logs directory if it doesn't exist
    logs_dir = Path("Logs")
    logs_dir.mkdir(exist_ok=True)

    # Create a unique log filename with timestamp to avoid overwriting
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = logs_dir / f"attendance_analysis_{timestamp}.log"

    # Configure logging with both file and console output
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),  # Write to file
            logging.StreamHandler()  # Also print to console
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_filename}")
    return logger


# Initialize logger at module level for use throughout the script
logger = setup_logging()


def read_data(file_name: str) -> Optional[pd.DataFrame]:
    """
    Reads in attendance data from a file and returns a Pandas dataframe.

    Args:
        file_name (str): Path to the attendance data file

    Returns:
        Optional[pd.DataFrame]: Raw attendance data or None if error occurs
    """
    logger.info(f"Starting to read data from file: {file_name}")

    try:
        # Try to read the file with pandas
        # This will automatically detect common formats like CSV, Excel, etc.
        data = pd.read_csv(file_name, low_memory=False)

        # If data is empty, raise an error
        if data.empty:
            error_msg = "Data is empty."
            logger.error(error_msg)
            print(error_msg)
            return None

        # Convert attendance to integer for numerical operations
        data['attendance'] = data['attendance'].astype(int)

        # Extract season start year from season format
        # (e.g., "2020-2021" -> 2020)
        data['season_start'] = (
            data['season'].apply(
                lambda x: x.split('-')[0]
            ).astype(int)
        )

        logger.info(f"Successfully loaded data from {file_name}")
        logger.info(f"Data shape: {data.shape}")
        logger.info(f"Columns: {list(data.columns)}")

        # Log data summary for debugging and validation
        logger.info(f"Data types: {dict(data.dtypes)}")
        logger.info(f"Missing values: {data.isnull().sum().to_dict()}")

        return data

    except FileNotFoundError:
        # Handle case where file doesn't exist
        error_msg = f"File '{file_name}' not found."
        logger.error(error_msg)
        print(error_msg)
        return None
    except Exception as e:
        # Handle any other unexpected errors during file reading
        error_msg = f"Error reading file '{file_name}': {str(e)}"
        logger.error(error_msg)
        print(error_msg)
        return None


def _create_color_palette(*, leagues: list) -> Dict[str, str]:
    """
    Create a color palette mapping for league tiers.

    Args:
        leagues: List of league tier names.

    Returns:
        Dictionary mapping league names to colors.
    """
    # Use Category10 palette with appropriate size (min 3, max 10 colors)
    palette = Category10[max(3, min(10, len(leagues)))]
    return {
        league: palette[i % len(palette)]
        for i, league in enumerate(leagues)
    }


def _add_historical_annotations(*, plot: figure) -> None:
    """
    Add historical annotations to the plot.

    Args:
        plot: Bokeh figure object to annotate.
    """
    # WWII period (1939-1945) - add visual band to show impact on attendance
    wwii_band = BoxAnnotation(
        left=1939, right=1945,
        fill_color='lightcoral', fill_alpha=0.3
    )
    plot.add_layout(wwii_band)

    # WWI period (1914-1918) - add visual band to show impact on attendance
    wwi_band = BoxAnnotation(
        left=1914, right=1918,
        fill_color='lightcoral', fill_alpha=0.3
    )
    plot.add_layout(wwi_band)


def _configure_legend(*, plot: figure) -> None:
    """
    Configure the legend for the plot.

    Args:
        plot: Bokeh figure object to configure.
    """
    # Set legend title and make it interactive
    plot.legend.title = 'League\nTier'
    plot.legend.click_policy = "hide"  # Allow clicking to hide/show series
    plot.legend.location = "right"
    plot.legend.orientation = "vertical"

    # Style the legend with borders and background
    plot.legend.border_line_color = "black"
    plot.legend.border_line_width = 1
    plot.legend.background_fill_color = "white"
    plot.legend.background_fill_alpha = 0.8

    # Place legend outside the plot area for better visibility
    plot.add_layout(plot.legend[0], 'right')


def _build_kdes(*, raw_data: pd.DataFrame) -> pd.DataFrame:
    """
    Build KDE (Kernel Density Estimation) data for each league tier and season.

    Args:
        processed_data (pd.DataFrame): Processed attendance data

    Returns:
        pd.DataFrame: DataFrame containing KDE results with columns:
                     x, y, league_tier, season_start
    """

    stripped_raw = raw_data[['league_tier', 'season_start', 'attendance']]

    # Create x-axis range for density estimation
    x = np.linspace(start=0,
                    stop=1.2*stripped_raw['attendance'].max(),
                    num=200)

    kdes = []   # List to hold kdes
    # Iterate through each league tier and season combination
    for league_tier in stripped_raw['league_tier'].unique():

        league_tier_data = stripped_raw[
                stripped_raw['league_tier'] == league_tier
        ]  

        for season in league_tier_data['season_start'].unique():

            # Filter data for specific league tier and season
            league_year_data = stripped_raw[
                (stripped_raw['league_tier'] == league_tier) &
                (stripped_raw['season_start'] == season)
            ]

            # Create x-axis range for density estimation
            x = np.linspace(start=league_year_data['attendance'].min(),
                            stop=league_year_data['attendance'].max(),
                            num=200) 

            # Filter data for specific league tier and season
            league_year_data = stripped_raw[
                (stripped_raw['league_tier'] == league_tier) &
                (stripped_raw['season_start'] == season)
            ]

            # COVID case, no games in a year.
            # If there is no attendance, skip the year.
            if league_year_data['attendance'].sum() == 0:
                kdes.append(pd.DataFrame({
                    'x': x,
                    'y': np.zeros(len(x)),
                    'league_tier': league_tier,
                    'season_start': season
                }))
                continue

            # Calculate kernel density estimation for attendance distribution
            pdf = stats.gaussian_kde(league_year_data['attendance'])
            y = pdf.evaluate(x)
            y /= sum(y)  # Normalize the KDE to 1

            kdes.append(pd.DataFrame({
                    'x': x,
                    'y': y,
                    'league_tier': league_tier,
                    'season_start': season
                }))

    kdes = pd.concat(kdes, ignore_index=True)
    return kdes


def plot_attendance_violin(raw_data: pd.DataFrame, plot_width: int, *, plot_height: int = 150):
    """
    Create violin plot visualization for attendance data.

    This function builds a KDE (Kernel Density Estimation) plot for each
    league tier and season to show the distribution of attendance values.

    Args:
        raw_data (pd.DataFrame): Processed attendance data
        plot_width (int): Width of the plot in pixels
        plot_height (int): Height of each subplot in pixels (default: 150)

    Returns:
        Tuple[str, str]: Bokeh script and div components
    """

    start_year = 2024

    # Build KDE data for all league tiers and seasons
    kde_data = _build_kdes(raw_data=raw_data)
    kde_data['y2'] = 0

    # Get unique league tiers and sort them for consistent ordering
    leagues = sorted(kde_data['league_tier'].unique())
    color_map = _create_color_palette(leagues=leagues)

    # Source data for the plot
    source_all_1 = ColumnDataSource(kde_data[(kde_data['league_tier'] == 1)])
    source_all_2 = ColumnDataSource(kde_data[(kde_data['league_tier'] == 2)])
    source_all_3 = ColumnDataSource(kde_data[(kde_data['league_tier'] == 3)])
    source_all_4 = ColumnDataSource(kde_data[(kde_data['league_tier'] == 4)])
    source_1 = ColumnDataSource(kde_data[(kde_data['league_tier'] == 1) & (kde_data['season_start'] == start_year)])
    source_2 = ColumnDataSource(kde_data[(kde_data['league_tier'] == 2) & (kde_data['season_start'] == start_year)])
    source_3 = ColumnDataSource(kde_data[(kde_data['league_tier'] == 3) & (kde_data['season_start'] == start_year)])
    source_4 = ColumnDataSource(kde_data[(kde_data['league_tier'] == 4) & (kde_data['season_start'] == start_year)])
        
    p1 = figure(
        title=f"Attendance distribution per season for tier 1 - {start_year}",
        x_axis_label="Attendance",
        y_axis_label="Density",
        width=plot_width,
        height=plot_height
        )
    p1.varea(
            x='x',
            y1='y',
            y2='y2',
            source=source_1,
            fill_color=color_map[1],
            fill_alpha=0.5
        )
    p2 = figure(
        title=f"Attendance distribution per season for tier 2 - {start_year}",
        x_axis_label="Attendance",
        y_axis_label="Density",
        width=plot_width,
        height=plot_height
        )
    p2.varea(
            x='x',
            y1='y',
            y2='y2',
            source=source_2,
            fill_color=color_map[2],
            fill_alpha=0.5
        )
    p3 = figure(
        title=f"Attendance distribution per season for tier 3 - {start_year}",
        x_axis_label="Attendance",
        y_axis_label="Density",
        width=plot_width,
        height=plot_height
    )   
    p3.varea(
            x='x',
            y1='y',
            y2='y2',
            source=source_3,
            fill_color=color_map[3],
            fill_alpha=0.5
        )   
    p4 = figure(
        title=f"Attendance distribution per season for tier 4 - {start_year}",
        x_axis_label="Attendance",
        y_axis_label="Density",
        width=plot_width,
        height=plot_height
    )       
    p4.varea(
            x='x',
            y1='y',
            y2='y2',
            source=source_4,
            fill_color=color_map[4],
            fill_alpha=0.5
        )   

    p1.yaxis.visible = False
    p1.ygrid.visible = False
    p2.yaxis.visible = False
    p2.ygrid.visible = False
    p3.yaxis.visible = False
    p3.ygrid.visible = False
    p4.yaxis.visible = False
    p4.ygrid.visible = False


    # Custom JavaScript callback function for interactive updates
    # This function runs when the user moves the year slider
    callback = CustomJS(
        args=dict(source_1=source_1, 
                  source_2=source_2,      
                  source_3=source_3, 
                  source_4=source_4, 
                  source_all_1=source_all_1, 
                  source_all_2=source_all_2, 
                  source_all_3=source_all_3, 
                  source_all_4=source_all_4, 
                  p1=p1,
                  p2=p2,
                  p3=p3,
                  p4=p4),
        code="""
        // Get the selected year from the slider
        const year = this.value;
        
        // Plot 1
        // Initialize empty arrays for the filtered data
        const new_data1 = {
            x: [],
            y: [],
            y2: []
        };
        const new_data2 = {
            x: [],
            y: [],
            y2: []
        };
        const new_data3 = { 
            x: [],
            y: [],
            y2: []
        };
        const new_data4 = {
            x: [],      
            y: [],
            y2: []
        };

        // Filter data for the selected year
        // Loop through all data points and only keep those matching the year
        for (let i = 0; i < source_all_1.data.season_start.length; i++) {
            if (source_all_1.data.season_start[i] === year) {
                new_data1.x.push(source_all_1.data.x[i]);
                new_data1.y.push(source_all_1.data.y[i]);
                new_data1.y2.push(source_all_1.data.y2[i]);
            }
            if (source_all_2.data.season_start[i] === year) {
                new_data2.x.push(source_all_2.data.x[i]);
                new_data2.y.push(source_all_2.data.y[i]);
                new_data2.y2.push(source_all_2.data.y2[i]);
            }
            if (source_all_3.data.season_start[i] === year) {
                new_data3.x.push(source_all_3.data.x[i]);
                new_data3.y.push(source_all_3. data.y[i]);
                new_data3.y2.push(source_all_3.data.y2[i]);
            }
            if (source_all_4.data.season_start[i] === year) {    
                new_data4.x.push(source_all_4.data.x[i]);
                new_data4.y.push(source_all_4.data.y[i]);
                new_data4.y2.push(source_all_4.data.y2[i]);
            }
        }

        // Update the data source with filtered data
        source_1.data = new_data1;
        source_2.data = new_data2;
        source_3.data = new_data3;
        source_4.data = new_data4;


        // Update plot title to reflect the selected year
        p1.title.text = "Attendance distribution per season for tier 1 - " + year;
        p2.title.text = "Attendance distribution per season for tier 2 - " + year;
        p3.title.text = "Attendance distribution per season for tier 3 - " + year;
        p4.title.text = "Attendance distribution per season for tier 4 - " + year;

        // Trigger the plot to redraw with new data
        source_1.change.emit();
        source_2.change.emit();
        source_3.change.emit();
        source_4.change.emit();
        """
    )
    # Create interactive slider for year selection
    # Users can drag this to view data from different years
    year_slider = Slider(
        start=kde_data['season_start'].min(),
        end=kde_data['season_start'].max(),
        value=start_year,
        step=1,
        title="Season (Start Year)",
        width=600
    )   

    # Connect the JavaScript callback to the slider
    # This makes the heatmap interactive
    year_slider.js_on_change('value', callback)

    layout = column(p1, p2, p3, p4, year_slider)

    # Generate HTML components for embedding
    script, div = components(layout)
    return script, div


def plot_attendance_time(raw_data: pd.DataFrame, plot_width: int, *, plot_height: int = 400) -> Tuple[str, str]:
    """
    Plots the data and saves charts to the Plots folder.

    Args:
        raw_data (pd.DataFrame): Raw attendance data
        plot_width (int): Width of the plot in pixels
        plot_height (int): Height of the plot in pixels (default: 400)

    Returns:
        Tuple[str, str]: Bokeh script and div components
    """
    logger.info("Starting plot creation and saving")

    # Aggregate data by league tier and season to get total attendance
    processed_data = (
        raw_data.groupby(['league_tier', 'season_start'])
        .agg({'attendance': 'sum'})
        .reset_index()
    )

    if processed_data is None or processed_data.empty:
        error_msg = "No data to plot."
        logger.error(error_msg)
        print(error_msg)
        return

    try:

        logger.info("Creating attendance time visualization")

        # Get unique league tiers and sort them for consistent ordering
        leagues = sorted(processed_data['league_tier'].unique())
        color_map = _create_color_palette(leagues=leagues)

        # Create the main figure with appropriate dimensions and labels
        p = figure(
            title="Total attendance per season and league",
            x_axis_label="Season start",
            y_axis_label="Total attendance",
            width=plot_width,
            height=plot_height
        )

        # Add historical annotations for context
        _add_historical_annotations(plot=p)

        # Plot data for each league tier
        for league in leagues:
            # Filter data for current league tier
            league_data = processed_data[
                processed_data['league_tier'] == league
            ]

            # Create ColumnDataSource for the league data
            source = ColumnDataSource(league_data)

            # Plot the main trend line connecting attendance over time
            p.line(
                x='season_start',
                y='attendance',
                legend_label=f"{league}",
                line_width=2,
                color=color_map[league],
                source=source
            )

            # Add scatter points to show individual data points
            p.scatter(
                x='season_start',
                y='attendance',
                legend_label=f"{league}",
                size=8,
                color=color_map[league],
                source=source
            )

        # Add hover tooltip for all data points
        p.add_tools(HoverTool(
            tooltips=[
                ("League", "@league_tier"),
                ("Season", "@season_start"),
                ("Attendance", "@attendance{0,0}")
            ]
        ))

        # Configure legend with proper styling
        _configure_legend(plot=p)

        # Generate HTML components for embedding
        script, div = components(p)

        logger.info("Attendance visualization completed")

        return script, div

    except KeyError as e:
        # Handle missing required keys in the data
        logger.error(
            f"Missing required key in match_data: {e}"
        )
        raise
    except ValueError as e:
        # Handle invalid data for plotting
        logger.error(
            f"Invalid data for plotting: {e}"
        )
        raise
    except Exception as e:
        # Catch any other unexpected errors during plotting
        logger.error(
            f"Unexpected error in plotting: {e}"
        )
        raise

def plot_attendance_stadium_capacity(stadium_capacity: pd.DataFrame, plot_width: int, *, plot_height: int = 400) -> Tuple[str, str]:
    """
    Plots the stadium capacity data.

    Args:
        stadium_capacity (pd.DataFrame): Stadium capacity data
        plot_width (int): Plot width
        plot_height (int): Height of each subplot in pixels (default: 400)

    Returns:
        Tuple[str, str]: Bokeh script and div components
    """

    logger.info("Starting stadium capacity visualization")

    # Get unique league tiers and sort them for consistent ordering
    leagues = sorted(stadium_capacity['league_tier'].unique())
    color_map = _create_color_palette(leagues=leagues)

    # Create the main figure with appropriate dimensions and labels
    # Tier 1
    # ------
    clubs = stadium_capacity[stadium_capacity['league_tier'] == 1]['club'].unique()
    p1 = figure(
        title="Stadium capacity tier 1 2024-2025",
        x_range=clubs,
        y_axis_label="Stadium capacity",
        width=int(plot_width/2),
        height=int(plot_height/2)
    )
    p1.xaxis.visible = False
    p1.xgrid.visible = False
    p1.vbar(x=stadium_capacity[stadium_capacity['league_tier'] == 1]['club'], 
            top=stadium_capacity[stadium_capacity['league_tier'] == 1]['capacity'], 
            color=color_map[1],
            width=0.9)

    # Tier 2
    # ------
    clubs = stadium_capacity[stadium_capacity['league_tier'] == 2]['club'].unique()
    p2 = figure(
        title="Stadium capacity tier 2 2024-2025",
        x_range=clubs,
        y_axis_label="Stadium capacity",
        width=int(plot_width/2),
        height=int(plot_height/2)
    )
    p2.xaxis.visible = False
    p2.xgrid.visible = False
    p2.vbar(x=stadium_capacity[stadium_capacity['league_tier'] == 2]['club'], 
            top=stadium_capacity[stadium_capacity['league_tier'] == 2]['capacity'], 
            color=color_map[2],
            width=0.9)

    # Tier 3
    # ------
    clubs = stadium_capacity[stadium_capacity['league_tier'] == 3]['club'].unique()
    p3 = figure(
        title="Stadium capacity tier 3 2024-2025",
        x_range=clubs,
        y_axis_label="Stadium capacity",
        width=int(plot_width/2),
        height=int(plot_height/2)
    )
    p3.xaxis.visible = False
    p3.xgrid.visible = False
    p3.vbar(x=stadium_capacity[stadium_capacity['league_tier'] == 3]['club'], 
            top=stadium_capacity[stadium_capacity['league_tier'] == 3]['capacity'], 
            color=color_map[3],
            width=0.9)

    # Tier 4
    # ------
    clubs = stadium_capacity[stadium_capacity['league_tier'] == 4]['club'].unique()
    p4 = figure(
        title="Stadium capacity tier 4 2024-2025",
        x_range=clubs,
        y_axis_label="Stadium capacity",
        width=int(plot_width/2),
        height=int(plot_height/2)
    )
    p4.xaxis.visible = False
    p4.xgrid.visible = False
    p4.vbar(x=stadium_capacity[stadium_capacity['league_tier'] == 4]['club'], 
            top=stadium_capacity[stadium_capacity['league_tier'] == 4]['capacity'], 
            color=color_map[4],
            width=0.9)

    layout = column(row(p1, p2), row(p3, p4))

    # Generate HTML components for embedding
    script, div = components(layout)
    return script, div



# Example usage and testing
if __name__ == "__main__":
    # Example of how to use the functions
    logger.info("Starting attendance analysis script")

    # Define path to raw data file
    raw_data_file: str = os.path.join(
        "..", "Data Preparation", 'Data', 'match_attendance.csv'
    )
    raw_data: Optional[pd.DataFrame] = read_data(file_name=raw_data_file)

    # Get stadium capacity data
    stadium_capacity_file: str = os.path.join("Data", "stadiumcapacity-20242025.csv")
    stadium_capacity: Optional[pd.DataFrame] = pd.read_csv(stadium_capacity_file, low_memory=False)
    stadium_capacity['capacity'] = stadium_capacity['capacity'].astype(int)
    stadium_capacity = stadium_capacity.sort_values(by=['league_tier', 'capacity'], ascending=False)

    # Generate both time series and violin plots
    plot_width = 600
    plot_height = 400
    script1, div1 = plot_attendance_time(raw_data=raw_data, plot_width=plot_width, plot_height=plot_height)
    script2, div2 = plot_attendance_violin(raw_data=raw_data, plot_width=plot_width, plot_height=150)
    script3, div3 = plot_attendance_stadium_capacity(stadium_capacity=stadium_capacity, plot_width=plot_width, plot_height=plot_height)

    # Get Bokeh version for proper script imports
    version = bokeh.__version__
    imported_scripts = (
        f"""<script src="https://cdn.bokeh.org/bokeh/release/"""
        f"""bokeh-{version}.min.js"></script>\n"""
        f"""<script src="https://cdn.bokeh.org/bokeh/release/"""
        f"""bokeh-widgets-{version}.min.js"></script>\n"""
        f"""<script src="https://cdn.bokeh.org/bokeh/release/"""
        f"""bokeh-tables-{version}.min.js"></script>\n"""
        f"""<script src="https://cdn.bokeh.org/bokeh/release/"""
        f"""bokeh-mathjax-{version}.min.js"></script>\n"""
    )

    # Sample text content for the HTML page
    lorem = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do "
        "eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim "
        "ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut "
        "aliquip ex ea commodo consequat. Duis aute irure dolor in "
        "reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla "
        "pariatur. Excepteur sint occaecat cupidatat non proident, sunt in "
        "culpa qui officia deserunt mollit anim id est laborum."
    )

    # Create HTML file with the generated plot
    with open(os.path.join("Plots", "attendance_time.html"), "w") as f:
        # Header equivalent - include Bokeh script imports
        f.write("<!-- Script imports -->\n")
        f.write(imported_scripts)
        # Body equivalent - add HTML content
        f.write("<!-- HTML body -->\n")
        # Text content
        f.write(f"""<p>{lorem}</p>\n""")
        # Plot container with center alignment
        f.write("<div align='center'>\n")
        f.write(div1)
        f.write("\n")
        f.write("</div>\n")
        f.write(f"""<p>{lorem}</p>\n""")
        f.write("<div align='center'>\n")
        f.write(div2)
        f.write("\n")
        f.write("</div>\n")
        f.write(f"""<p>{lorem}</p>\n""")
        f.write("<div align='center'>\n")
        f.write(div3)
        f.write("\n")
        f.write("</div>\n")
        # Additional text content
        f.write(f"""<p>{lorem}</p>\n""")
        # Chart scripts for interactive functionality
        f.write("<!-- Chart scripts -->\n")
        f.write(script1)
        f.write(script2)
        f.write(script3)

    # Open the generated plot in the default web browser
    webbrowser.open('file:///'
                    + os.path.abspath(os.path.join(
                        "Plots", "attendance_time.html"
                    ))
                    )

    logger.info("Script completed")
