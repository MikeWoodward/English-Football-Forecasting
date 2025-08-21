"""
Goals vs years in league analysis module.

This module analyzes the relationship between goals scored and years spent in
the league. It processes match data to calculate how many consecutive seasons
each club has been in their current league tier and identifies promotion/
relegation events.
"""

# Import required libraries for data manipulation and system operations
import pandas as pd
import os
import sys
import logging
from bokeh.plotting import figure, show
import numpy as np
from bokeh.models import (HoverTool, ColumnDataSource, RadioButtonGroup,
                          Slider, Div, Legend, LegendItem, Spacer, CustomJS)
from bokeh.layouts import column
from scipy.optimize import curve_fit
from bokeh.embed import components

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from Utility_code.analysis_utilities import (save_plots)

# Create Logs directory if it doesn't exist
# This ensures we have a place to store log files for debugging and
# monitoring
logs_dir = "Logs"
if not os.path.exists(path=logs_dir):
    os.makedirs(path=logs_dir)

# Configure logging to both file and console
# This allows us to track program execution and debug issues
log_file = os.path.join(logs_dir, "goals_vs_years_analysis.log")
logging.basicConfig(
    level=logging.INFO,  # Set logging level to INFO to capture important
    # events
    format='%(asctime)s - %(levelname)s - %(message)s',  # Define log
    # format
    handlers=[
        logging.FileHandler(filename=log_file),  # Write logs to file
        logging.StreamHandler()  # Also display logs in console
    ]
)
# Create a logger instance for this module
logger = logging.getLogger(name=__name__)


def process_data(*, matches: pd.DataFrame) -> pd.DataFrame:
    """
    Process the aggregated match data to add years in league information.

    This function calculates how many consecutive seasons each club has been
    in their current league tier and identifies promotion/relegation events.

    Args:
        matches: DataFrame containing match data with columns:
               season, league_tier, match_date, home_club, away_club,
               home_goals, away_goals

    Returns:
        DataFrame with additional columns:
        - season_start: Starting year of the season (extracted from season
          string)
        - seasons_in_league: Number of consecutive seasons in current tier
        - league_change: Indicates "Promotion", "Relegation", or NaN
    """

    # Select only the required columns for analysis
    # This reduces memory usage and focuses on relevant data
    columns = [
        'season', 'league_tier', 'match_date', 'home_club', 'away_club',
        'home_goals', 'away_goals'
    ]
    matches = matches.loc[:, columns]

    # Create separate dataframes for home and away teams
    # This allows us to treat each team's performance separately
    home = matches.loc[:, ['season', 'league_tier', 'home_club', 'home_goals',
                           'away_goals']].copy()
    # Rename columns to standardize the data structure
    home = home.rename(columns={
        'home_club': 'club_name',  # Standardize club name column
        'home_goals': 'for_goals',  # Goals scored by the club
        'away_goals': 'against_goals'  # Goals conceded by club
    })

    # Create away team dataframe with same structure
    away = matches.loc[:, ['season', 'league_tier', 'away_club', 'home_goals',
                           'away_goals']].copy()
    # Rename columns for away teams (note: goals are swapped for away
    # perspective)
    away = away.rename(columns={
        'away_club': 'club_name',  # Standardize club name column
        'away_goals': 'for_goals',  # Goals scored by club (away goals)
        'home_goals': 'against_goals'  # Goals conceded by club (home goals)
    })

    # Combine home and away data into a single dataframe
    # This gives us one row per team per match
    total = pd.concat(objs=[home, away])

    # Aggregate goals by club, season, and league tier
    # This gives us total goals for and against each club per
    # season
    total = total.groupby(by=['season', 'league_tier', 'club_name']).agg(
        func={
            'for_goals': 'sum',  # Total goals scored by club
            'against_goals': 'sum'  # Total goals conceded by club
        }).reset_index().sort_values(by=['club_name', 'season',
                                         'league_tier'])

    # Calculate net goals (goals scored minus goals conceded)
    # This gives us a measure of overall performance
    total['net_goals'] = total['for_goals'] - total['against_goals']

    # Extract starting year from season string (e.g., "2020-21" -> 2020)
    # This is needed for chronological analysis
    total['season_start'] = (total.loc[:, 'season']
                             .str.split(pat='-')  # Split on hyphen
                             .str[0]  # Take first part (year)
                             .astype(dtype=int))  # Convert to integer

    # Sort data chronologically by club and season for proper analysis
    total = total.sort_values(by=['club_name', 'season_start'])

    # Create a dataframe to cope with promotion into leagues from outside
    # - gets missing years
    # This handles clubs that may have gaps in their league history
    presence = total.groupby(by='club_name').agg(
        first_season=('season_start', 'min'),
        last_season=('season_start', 'max'),
    ).reset_index()
    # Create a range of seasons for each club from before first to after last
    presence['season_start'] = presence.apply(
        lambda x: np.arange(x['first_season'] - 1,
                            x['last_season'] + 1),
        axis=1)
    # Remove the aggregated columns and expand the season ranges
    presence = presence.drop(columns=['first_season', 'last_season']).explode(
        'season_start')
    # Remove wartime seasons where football was suspended
    wartime_years = [1915, 1916, 1917, 1918, 1939, 1940, 1941, 1942, 1943,
                     1944, 1945]
    presence = presence[~presence['season_start'].isin(wartime_years)]
    # Merge to add missing seasons for clubs
    total = pd.merge(left=total,
                     right=presence,
                     on=['club_name', 'season_start'],
                     how='outer').sort_values(by=['club_name', 'season_start'])
    # Placeholder value for league_tiers we don't have data for
    total['league_tier'] = total['league_tier'].fillna(100)

    # Calculate league tier changes to identify promotion/relegation events
    # This creates a transition marker when a club changes leagues
    total['transition'] = (total.groupby(by='club_name')['league_tier']
                           .diff() != 0)

    # Create unique group IDs for consecutive seasons in the same league
    # This helps us track how long a club stays in each league tier
    total['groupID'] = (total.groupby(by='club_name')['transition']
                        .cumsum()  # Cumulative sum of transitions
                        .bfill())  # Back-fill to handle NaN values

    # Calculate the number of consecutive seasons each club has been in
    # their current league tier
    total['seasons_in_league'] = (total.groupby(by=['club_name', 'groupID'])
                                  ['groupID'].cumcount() + 1)  # Count + 1

    # Calculate league change direction (promotion vs relegation)
    # Negative difference indicates promotion (lower tier number = higher
    # league)
    total['league_change_boundary'] = -(total.groupby(by='club_name')
                                        ['league_tier'].diff())
    # Mark promotion events (positive change in
    # league_change_boundary)
    total.loc[total['league_change_boundary'] > 0, "league_change"] = (
        "Promotion"
    )
    # Mark relegation events (negative change in
    # league_change_boundary)
    total.loc[total['league_change_boundary'] < 0, "league_change"] = (
        "Relegation"
    )

    # Remove placeholder rows (where league_tier = 100)
    # These were temporary entries for missing seasons
    total = total[total['league_tier'] != 100]

    # Remove temporary columns used for calculations
    total = total.drop(columns=['transition', 'groupID',
                                'league_change_boundary'])

    # Now, add the curve fit
    def log_linear_func(x, a, b):
        """
        A function representing a linear relationship with respect to the
        logarithm of x.
        y = a * log(x) + b
        """
        return a * np.log(x) + b

    # Initialize list to store fitted curve data
    fitted_data = []

    # Iterate through each season and league tier to fit curves
    for season in total['season_start'].unique():
        # Filter data for current season
        selected_season = total[total['season_start'] == season]

        for league in selected_season['league_tier'].unique():
            # Filter data for current league tier, excluding relegated teams
            # (as they may have different dynamics)
            selected_data = selected_season[
                (selected_season['league_tier'] == league)
                & (selected_season['league_change'] != 'Relegation')]
            x_in = selected_data['seasons_in_league'].tolist()

            # If there's only one x-value, skip the curve fitting and just
            # show a mean
            if len(set(x_in)) == 1:
                # Add to list with mean values instead of fitted curve
                fitted_data.append({
                    'league_tier': league,
                    'season_start': season,
                    'seasons_in_league': [x_in[0]],
                    'for_goals_fit': [selected_data['for_goals'].mean()],
                    'against_goals_fit': [
                        selected_data['against_goals'].mean()],
                    'net_goals_fit': [selected_data['net_goals'].mean()]
                })
                continue

            # Fit curve for goals scored
            y_for = selected_data['for_goals'].tolist()
            popt, pcov = curve_fit(log_linear_func,
                                   x_in,
                                   y_for)
            a_fit, b_fit = popt
            y_for_fit = log_linear_func(x_in, a_fit, b_fit)

            # Fit curve for goals conceded
            y_against = selected_data['against_goals'].tolist()
            popt, pcov = curve_fit(log_linear_func,
                                   x_in,
                                   y_against)
            a_fit, b_fit = popt
            y_against_fit = log_linear_func(x_in, a_fit, b_fit)

            # Fit curve for net goals
            y_net = selected_data['net_goals'].tolist()
            popt, pcov = curve_fit(log_linear_func,
                                   x_in,
                                   y_net)
            a_fit, b_fit = popt
            y_net_fit = log_linear_func(x_in, a_fit, b_fit)

            # Add fitted data to list
            fitted_data.append({
                'league_tier': league,
                'season_start': season,
                'seasons_in_league': x_in,
                'for_goals_fit': y_for_fit,
                'against_goals_fit': y_against_fit,
                'net_goals_fit': y_net_fit
            })

    # Convert fitted data list to DataFrame and expand the lists
    fitted_data = pd.DataFrame(fitted_data).explode([
        'seasons_in_league',
        'for_goals_fit',
        'against_goals_fit',
        'net_goals_fit'
    ])
    return total, fitted_data


def plot_data(*,
              tenure: pd.DataFrame,
              tenure_fitted: pd.DataFrame) -> None:
    """
    Create a scatter plot using Bokeh to visualize the relationship between
    goals scored and years spent in the league.

    This function creates an interactive scatter plot showing how goals scored
    relate to the number of consecutive seasons a club has been in their
    current league tier.

    Args:
        tenure: DataFrame containing processed match data with
                columns including for_goals, seasons_in_league,
                club_name, and league_tier
        tenure_fitted: DataFrame containing fitted curve data

    Returns:
        None. The function displays the plot in a web browser.
    """

    # Add colors to the data based on promotion/relegation status
    # Green for promotion, red for relegation, blue for no change
    tenure.loc[tenure['league_change'] == "Promotion",
               'color'] = "green"
    tenure.loc[tenure['league_change'] == "Relegation",
               'color'] = "red"
    tenure.loc[tenure['league_change'].isnull(),
               'color'] = "blue"

    # Create ColumnDataSource objects for Bokeh plotting
    # These provide efficient data access for the interactive plots
    tenure_all = ColumnDataSource(tenure)
    tenure_fitted_all = ColumnDataSource(tenure_fitted)

    # Set initial display parameters
    year = tenure['season_start'].max()  # Default year to display
    league = 1   # Default league tier to display
    plot_height = 200
    plot_width = 600

    # Select the data to plot for the initial view
    tenure_selected = ColumnDataSource(
        tenure[(tenure['league_tier'] == league)
               & (tenure['season_start'] == year)])
    tenure_fitted_selected = ColumnDataSource(
        tenure_fitted[(tenure_fitted['league_tier'] == league)
                      & (tenure_fitted['season_start'] == year)])

    # Create plots for each goal metric (for, against, net)
    plots = []
    for index, metric in enumerate(['for_goals', 'against_goals',
                                   'net_goals']):

        # Format metric name for display
        metric_text = metric.replace('_', ' ').title()

        # Create the plot figure
        plot = figure(
            title=(f"{metric_text} vs Years in League. League: {league}, "
                   f"Year: {year}"),
            y_axis_label=f"{metric_text} scored",
            x_axis_type="log",  # Use logarithmic scale for years in league
            x_axis_label="Seasons in League" if metric == 'net_goals' else None,
            width=plot_width,
            height=plot_height,
            toolbar_location="left")

        # Add scatter plot points
        scatter = plot.scatter(x='seasons_in_league',
                               y=metric,
                               source=tenure_selected,
                               size=4,
                               color='color')

        # Add fitted curve line
        line = plot.line(
            x='seasons_in_league',
            y=f'{metric}_fit',
            alpha=0.25,
            color='black',
            source=tenure_fitted_selected
        )

        # Add hover tool for interactive data exploration
        plot.add_tools(HoverTool(
            tooltips=[
                ("Club", "@club_name"),
                ("Seasons in League", "@seasons_in_league"),
                ("Goals Scored", "@for_goals"),
                ("Goals Conceded", "@against_goals"),
                ("Net Goals", "@net_goals")
            ],
            renderers=[scatter]
            ))

        # Create and configure the legend (only for against_goals plot)
        if metric == 'against_goals':
            # Create invisible renderers to drive legend entries
            r_promotion = plot.scatter(x='seasons_in_league',
                                       y=metric,
                                       color="green",
                                       source=tenure_selected,
                                       size=0)
            r_relegation = plot.scatter(x='seasons_in_league',
                                        y=metric,
                                        color="red",
                                        source=tenure_selected,
                                        size=0)
            r_neither = plot.scatter(x='seasons_in_league',
                                     y=metric,
                                     color="blue",
                                     source=tenure_selected,
                                     size=0)
            # Create legend with all categories
            legend = Legend(
                items=[LegendItem(label="Promotion",
                                  renderers=[r_promotion]),
                       LegendItem(label="Relegation",
                                  renderers=[r_relegation]),
                       LegendItem(label="No promotion\nor relegation",
                                  renderers=[r_neither]),
                       LegendItem(label="Log-linear fit",
                                  renderers=[line])],
                location="center",
                border_line_color="black",
                border_line_width=1,
            )
            plot.add_layout(legend, "right")

        plots.append(plot)

    # Add horizontal separators for visual organization
    horizontal_separator = Spacer(width=plot_width,
                                  height=15)
    plots.append(horizontal_separator)
    horizontal_separator = Spacer(width=plot_width,
                                  height=2,
                                  background='lightgray')
    plots.append(horizontal_separator)
    horizontal_separator = Spacer(width=plot_width,
                                  height=15)
    plots.append(horizontal_separator)

    # Add radio button group for selecting league tier
    league_names = ["League 1", "League 2", "League 3", "League 4", "League 5"]
    radio_button_group = RadioButtonGroup(labels=league_names, active=0,
                                          align="center")
    plots.append(radio_button_group)

    # Add Slider to select the year
    year_slider = Slider(
        start=tenure['season_start'].min(),
        end=tenure['season_start'].max(),
        value=year,
        step=1,
        width=plot_width,
        title="Season start year")
    plots.append(year_slider)

    # JavaScript callback to update charts when controls change
    callback_charts_update = CustomJS(
        args=dict(tenure_all=tenure_all,
                  tenure_selected=tenure_selected,
                  tenure_fitted_all=tenure_fitted_all,
                  tenure_fitted_selected=tenure_fitted_selected,
                  radio_button_group=radio_button_group,
                  year_slider=year_slider,
                  plot_for=plots[0],
                  plot_against=plots[1],
                  plot_net=plots[2]),
        code="""
            const league_tier = radio_button_group.active + 1
            const start_year = year_slider.value

            // Update the scatter points
            const new_data = {
                club_name: [],
                seasons_in_league: [],
                for_goals: [],
                against_goals: [],
                net_goals: [],
                color: []
            };
            // Loop through all data points and only keep those matching the
            // year and league_tier
            for (let i = 0; i < tenure_all.data.season_start.length; i++) {
                if (tenure_all.data.season_start[i] === start_year &&
                    tenure_all.data.league_tier[i] === league_tier) {
                    new_data.club_name.push(tenure_all.data.club_name[i]);
                    new_data.seasons_in_league.push(
                        tenure_all.data.seasons_in_league[i]);
                    new_data.for_goals.push(tenure_all.data.for_goals[i]);
                    new_data.against_goals.push(
                        tenure_all.data.against_goals[i]);
                    new_data.net_goals.push(tenure_all.data.net_goals[i]);
                    new_data.color.push(tenure_all.data.color[i]);
                }
            }
            tenure_selected.data = new_data;

            // Update the fitted points
            const new_data_fitted = {
                seasons_in_league: [],
                for_goals_fit: [],
                against_goals_fit: [],
                net_goals_fit: []
            };
            // Loop through all data points and only keep those matching the
            // year and league_tier
            for (let i = 0; i < tenure_fitted_all.data.season_start.length;
                 i++) {
                if (tenure_fitted_all.data.season_start[i] === start_year &&
                    tenure_fitted_all.data.league_tier[i] === league_tier) {
                    new_data_fitted.seasons_in_league.push(
                        tenure_fitted_all.data.seasons_in_league[i]);
                    new_data_fitted.for_goals_fit.push(
                        tenure_fitted_all.data.for_goals_fit[i]);
                    new_data_fitted.against_goals_fit.push(
                        tenure_fitted_all.data.against_goals_fit[i]);
                    new_data_fitted.net_goals_fit.push(
                        tenure_fitted_all.data.net_goals_fit[i]);
                }
            }
            tenure_fitted_selected.data = new_data_fitted;

            // Update the plots using emit
            tenure_selected.change.emit()
            tenure_fitted_selected.change.emit()

            // Update the chart titles
            plot_for.title.text = "For goals vs Years in League. League: " +
                league_tier + ", Year: " + start_year;
            plot_against.title.text = "Against goals vs Years in League. " +
                "League: " + league_tier + ", Year: " + start_year;
            plot_net.title.text = "Net goals vs Years in League. League: " +
                league_tier + ", Year: " + start_year;
        """)

    # Connect the JavaScript callback to the slider and radio button group
    # This makes the charts interactive by updating when slider or radio
    # button changes
    year_slider.js_on_change('value', callback_charts_update)
    radio_button_group.js_on_change('active', callback_charts_update)

    script, div = components(column(*plots))
    return [script], [div], ["goals_vs_years_in_league"]



if __name__ == "__main__":
    # Main execution block - only runs when script is executed directly

    # Construct the path to the input CSV file
    # Navigate up two directories to reach the data preparation folder
    csv_path = os.path.join("..",
                            "..",
                            "2 Data preparation",
                            "Data",
                            "matches_attendance_discipline.csv")

    # Log the data source for debugging and audit purposes
    logger.info(msg=f"Reading data from {csv_path}")

    try:
        # Read the CSV file into a pandas DataFrame
        # low_memory=False allows pandas to determine optimal data
        # types
        matches = pd.read_csv(filepath_or_buffer=csv_path, low_memory=False)
    except FileNotFoundError as e:
        # Log error with line number and stop processing
        logger.error(msg=f"File not found at line "
                         f"{e.__traceback__.tb_lineno}: {csv_path}")
        raise
    except Exception as e:
        # Log any other errors with line number and stop processing
        logger.error(msg=f"Error reading file at line "
                         f"{e.__traceback__.tb_lineno}: {str(e)}")
        raise

    # Process the raw match data to add years in league information
    # This is the main analysis function that calculates league tenure
    tenure, tenure_fitted = process_data(matches=matches)

    # Create and display the interactive visualization
    scripts, divs, titles = plot_data(tenure=tenure, tenure_fitted=tenure_fitted)

    # Save the plots
    save_plots(scripts=scripts, 
               divs=divs, 
               titles=titles, 
               file_name="goals_vs_years_in_league.html")

