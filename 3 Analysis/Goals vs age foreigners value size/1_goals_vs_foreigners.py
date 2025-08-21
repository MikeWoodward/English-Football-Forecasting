#!/usr/bin/env python3
"""
Goals vs Foreigners Analysis

This module analyzes the relationship between goals scored and foreign players in
English football. It creates interactive visualizations to explore how team
performance (goals scored, conceded, and net goals) relates to foreign player count.
"""

# Standard library imports for system operations and logging
import logging
import sys
import os
from datetime import datetime
from typing import Optional

# Data manipulation and analysis libraries
import pandas as pd
from scipy import stats
import statsmodels.api as sm

# Add parent directory to path for imports from utility modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Interactive visualization libraries
from bokeh.models import (HoverTool, ColumnDataSource, RadioButtonGroup,
                          Slider, CustomJS,
                          Band)
from bokeh.layouts import column
from bokeh.embed import components
from bokeh.plotting import figure

from Utility_code.analysis_utilities import (
    save_plots,
    wide_to_long_matches
)


def setup_logging(
    *,
    log_level: int = logging.INFO,
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> None:
    """
    Configure logging for the application.

    This function sets up a comprehensive logging system that writes to both
    console and file with timestamps. It creates a Logs directory if it doesn't
    exist and generates unique log files for each analysis run.

    Args:
        log_level: The logging level to use (default: INFO)
        log_format: The format string for log messages
    """
    # Create Logs directory if it doesn't exist
    if not os.path.exists("Logs"):
        os.makedirs("Logs")

    # Create a logger instance and set its level
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear any existing handlers to avoid duplicate log entries
    logger.handlers.clear()

    # Create formatter for consistent log message formatting
    formatter = logging.Formatter(log_format)

    # Create console handler for real-time logging output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Create file handler with timestamp in filename for persistent logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"Logs/analysis_{timestamp}.log"

    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Add both handlers to the logger for dual output
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


def add_linear_fits(*,
                    data_local: pd.DataFrame,
                    metrics: list[str]) -> None:
    """
    Calculate linear fits for goals vs the specified column across all
    league tiers and seasons.

    This function performs linear regression analysis for each combination
    of league tier and season, fitting models for goals scored, conceded,
    and net goals. It adds statistical measures (R-squared, p-values) and
    confidence intervals to the original dataframe for visualization.

    Args:
        data_local: DataFrame containing processed match data with
                   columns including for_goals, against_goals, net_goals,
                   league_tier, season_start, and 'x' column
        metrics: List of goal metrics to analyze (e.g., ['for_goals',
                'against_goals', 'net_goals'])

    Note:
        This function modifies the input dataframe in-place by adding
        new columns for fitted values, confidence intervals, p-values,
        and R-squared values.
    """
    # Iterate through each unique league tier in the dataset
    for league_tier in data_local['league_tier'].unique():
        # Filter data for current league tier to analyze separately
        data_league = data_local[data_local['league_tier'] == league_tier]

        # Iterate through each season within the current league tier
        for season_start in data_league['season_start'].unique():
            # Filter data for current season within league tier for analysis
            data_season = data_league[data_league['season_start'] == season_start]

            # Add constant term for linear regression (intercept term)
            X_const = sm.add_constant(data_season['x'])

            # Store basic information for this combination (unused but kept for
            # reference)
            interim = {
                'league_tier': league_tier,
                'season_start': season_start,
                'x': data_season['x']
            }

            # Fit regression models for each goal metric (scored, conceded, net)
            for metric in metrics:
                # Fit the Ordinary Least Squares (OLS) model for current metric
                model = sm.OLS(data_season[metric], X_const)
                results = model.fit()

                # Get predictions with 95% confidence intervals for uncertainty bands
                predictions = (results
                              .get_prediction(X_const)
                              .summary_frame(alpha=0.05))  # 95% confidence level

                # Store fitted values (predicted goals) for plotting trend lines
                data_local.loc[(data_local['league_tier'] == league_tier)
                             & (data_local['season_start'] == season_start),
                             metric + '_fit'] = predictions['mean']

                # Store lower confidence interval bounds for uncertainty bands
                data_local.loc[(data_local['league_tier'] == league_tier)
                             & (data_local['season_start'] == season_start),
                             metric + '_lci'] = predictions['mean_ci_lower']

                # Store upper confidence interval bounds for uncertainty bands
                data_local.loc[(data_local['league_tier'] == league_tier)
                             & (data_local['season_start'] == season_start),
                             metric + '_uci'] = predictions['mean_ci_upper']

                # Store p-value for slope coefficient (index 1 is slope, 0 is intercept)
                # Used to assess statistical significance of the relationship
                data_local.loc[(data_local['league_tier'] == league_tier)
                             & (data_local['season_start'] == season_start),
                             metric + '_p'] = results.pvalues.iloc[1]

                # Store R-squared value for model fit quality assessment
                data_local.loc[(data_local['league_tier'] == league_tier)
                             & (data_local['season_start'] == season_start),
                             metric + '_r2'] = results.rsquared


def plot_data(*,
              data: pd.DataFrame,
              column_name: str) -> dict:
    """
    Create interactive scatter plots using Bokeh to visualize relationships between
    goals and the specified column across different league tiers and seasons.

    This function creates three interactive scatter plots showing how goals scored,
    goals conceded, and net goals relate to the specified column (e.g., foreigner_count,
    age, market_value, etc.). It includes linear regression fits with confidence
    intervals and interactive controls for filtering by league tier and season.

    Args:
        data: DataFrame containing processed match data with columns including
              for_goals, against_goals, net_goals, club_name, league_tier, and
              season_start
        column_name: Name of the column to plot on x-axis (e.g., 'foreigner_count',
                   'age')

    Returns:
        dict: Dictionary containing script, plots, and controls components for HTML
              embedding
    """

    # Data Preparation and Setup
    # --------------------------

    # Create local copy of data, filtering out rows with null values in column_name
    # This ensures we only analyze complete data points
    data_local = data[data[column_name].notnull()].copy()

    # Create generic 'x' column for JavaScript compatibility in interactive plots
    # This allows the same JavaScript code to work with any column name
    data_local['x'] = data_local[column_name]

    # Define the goal metrics to analyze (scored, conceded, and net goals)
    metrics = ['for_goals', 'against_goals', 'net_goals']

    # Plot Configuration
    # ------------------

    # Format column name for display in plot titles (convert underscores to spaces,
    # capitalize)
    title_text = column_name.replace('_', ' ').title()

    # Set plot dimensions for consistent layout
    plot_height = 200
    plot_width = 600

    # Find minimum year with data for slider range configuration
    min_year = data_local[data_local[column_name].notnull()]['season_start'].min()

    # Set initial display parameters for interactive controls
    year = data_local['season_start'].max()  # Default to most recent year
    league = 1   # Default to league tier 1 (Premier League)

    # Perform linear regression analysis for all league-tier and season combinations
    # This adds fitted values, confidence intervals, p-values, and R-squared to
    # the dataframe
    add_linear_fits(data_local=data_local, metrics=metrics)

    # Sort data by league tier, season, and x values for proper confidence band
    # rendering
    # This ensures smooth confidence interval bands in the plots
    data_local = data_local.sort_values(by=['league_tier', 'season_start', 'x'])

    # Create ColumnDataSource objects for Bokeh plotting
    # These provide efficient data access for the interactive plots
    data_all = ColumnDataSource(data_local)

    # Create initial data selection for default view (league 1, most recent year)
    # This sets up the initial state of the interactive plots
    data_selected = ColumnDataSource(
        data_local[(data_local['league_tier'] == league)
                  & (data_local['season_start'] == year)])

    # Plot Creation
    # -------------

    # Create plots for each goal metric (scored, conceded, net goals)
    plots = []
    for index, metric in enumerate(metrics):

        # Format metric name for display in titles (convert underscores to spaces,
        # capitalize)
        metric_text = metric.replace('_', ' ').title()

        # Create the plot figure with statistical information in title
        # Title includes league tier, year, R-squared, and p-value for quick assessment
        plot = figure(
            title=(f"{metric_text} vs {title_text}. League: {league}. "
                   f"Year: {year}. "
                   f"r2={data_selected.data[metric + '_r2'].tolist()[0]:.2f}. "
                   f"p-value={data_selected.data[metric + '_p'].tolist()[0]:.2f}."),
            y_axis_label=f"{metric_text} scored",
            x_axis_label=column_name if metric == 'net_goals' else None,
            # Only show x-label on bottom plot
            width=plot_width,
            height=plot_height,
            toolbar_location="left")

        # Add scatter plot points for actual data points
        # Note: Using 'x' instead of column_name for JavaScript compatibility in
        # interactive updates
        scatter = plot.scatter(x='x',
                              y=metric,
                              source=data_selected,
                              size=4,
                              color='black')

        # Add linear regression fit line showing the trend
        line = plot.line(x='x',
                         y=metric + '_fit',
                         source=data_selected,
                         color='blue')

        # Add 95% confidence interval band around the fit line for uncertainty
        # visualization
        band = Band(base="x",
                    lower=metric + '_lci',
                    upper=metric + '_uci',
                    source=data_selected,
                    fill_alpha=0.05,
                    fill_color="blue",
                    line_color="blue")
        plot.add_layout(band)

        # Add hover tool for interactive data exploration
        # Shows club name, x-value, and all goal metrics when hovering over points
        plot.add_tools(HoverTool(
            tooltips=[
                ("Club", "@club_name"),
                (title_text, "@x"),
                ("Goals Scored", "@for_goals"),
                ("Goals Conceded", "@against_goals"),
                ("Net Goals", "@net_goals")
            ],
            renderers=[scatter]
        ))

        # Add plot to the list for layout arrangement
        plots.append(plot)

    # Interactive Controls Setup
    # --------------------------

    # Create radio button group for selecting league tier (1-5)
    # Allows users to switch between different English football divisions
    league_names = ["League Tier 1", "League Tier 2", "League Tier 3",
                    "League Tier 4", "League Tier 5"]
    radio_button_group = RadioButtonGroup(labels=league_names,
                                         active=0,  # Default to first option
                                         align="center")

    # Create slider for selecting the year/season
    # Allows users to explore data across different seasons
    year_slider = Slider(
        start=min_year,
        end=data['season_start'].max(),
        value=year,  # Default to most recent year
        step=1,
        width=plot_width,
        title="Season start year")

    # JavaScript callback function to update charts when controls change
    # This enables real-time interactive updates without page refresh
    callback_charts_update = CustomJS(
        args=dict(data_all=data_all,
                  data_selected=data_selected,
                  radio_button_group=radio_button_group,
                  year_slider=year_slider,
                  plot_for=plots[0],
                  plot_against=plots[1],
                  plot_net=plots[2]),
        code="""
            // Get current selections from interactive controls
            const league_tier = radio_button_group.active + 1
            const start_year = year_slider.value

            // Initialize new data structure for filtered data
            const new_data = {
                club_name: [],
                x: [],
                for_goals: [],
                for_goals_fit: [],
                for_goals_lci: [],
                for_goals_uci: [],
                for_goals_p: [],
                for_goals_r2: [],
                against_goals: [],
                against_goals_fit: [],
                against_goals_lci: [],
                against_goals_uci: [],
                against_goals_p: [],
                against_goals_r2: [],
                net_goals: [],
                net_goals_fit: [],
                net_goals_lci: [],
                net_goals_uci: [],
                net_goals_p: [],
                net_goals_r2: [],
            };

            // Filter data based on selected league tier and year
            // Loop through all data points and only keep those matching the selected
            // criteria
            for (let i = 0; i < data_all.data.season_start.length; i++) {
                if (data_all.data.season_start[i] === start_year &&
                    data_all.data.league_tier[i] === league_tier) {
                    // Add all relevant data fields for the filtered subset
                    new_data.club_name.push(data_all.data.club_name[i]);
                    new_data.x.push(data_all.data.x[i]);
                    new_data.for_goals.push(data_all.data.for_goals[i]);
                    new_data.for_goals_fit.push(data_all.data.for_goals_fit[i]);
                    new_data.for_goals_lci.push(data_all.data.for_goals_lci[i]);
                    new_data.for_goals_uci.push(data_all.data.for_goals_uci[i]);
                    new_data.for_goals_p.push(data_all.data.for_goals_p[i]);
                    new_data.for_goals_r2.push(data_all.data.for_goals_r2[i]);
                    new_data.against_goals.push(data_all.data.against_goals[i]);
                    new_data.against_goals_fit.push(data_all.data.against_goals_fit[i]);
                    new_data.against_goals_lci.push(data_all.data.against_goals_lci[i]);
                    new_data.against_goals_uci.push(data_all.data.against_goals_uci[i]);
                    new_data.against_goals_p.push(data_all.data.against_goals_p[i]);
                    new_data.against_goals_r2.push(data_all.data.against_goals_r2[i]);
                    new_data.net_goals.push(data_all.data.net_goals[i]);
                    new_data.net_goals_fit.push(data_all.data.net_goals_fit[i]);
                    new_data.net_goals_lci.push(data_all.data.net_goals_lci[i]);
                    new_data.net_goals_uci.push(data_all.data.net_goals_uci[i]);
                    new_data.net_goals_p.push(data_all.data.net_goals_p[i]);
                    new_data.net_goals_r2.push(data_all.data.net_goals_r2[i]);
                }
            }

            // Update the data source with filtered data
            data_selected.data = new_data;

            // Trigger plot updates by emitting change event
            data_selected.change.emit()

            // Update plot titles with new statistical information
            // Goals scored plot
            plot_for.title.text = plot_for.title.text.replace(/\\d{4}/, start_year);
            plot_for.title.text = plot_for.title.text.replace(/\\d{1}/, league_tier);
            const p_text_for = data_selected.data.for_goals_p[0].toFixed(2);
            const r2_text_for = data_selected.data.for_goals_r2[0].toFixed(2);
            plot_for.title.text = plot_for.title.text.replace(/\\d+\\.\\d{2}/, r2_text_for);
            plot_for.title.text = plot_for.title.text.replace(/\\d+\\.\\d{2}.$/, p_text_for + ".");

            // Goals conceded plot
            plot_against.title.text = plot_against.title.text.replace(/\\d{4}/, start_year);
            plot_against.title.text = plot_against.title.text.replace(/\\d{1}/, league_tier);
            const p_text_against = data_selected.data.against_goals_p[0].toFixed(2);
            const r2_text_against = data_selected.data.against_goals_r2[0].toFixed(2);
            plot_against.title.text = plot_against.title.text.replace(/\\d+\\.\\d{2}/, r2_text_against);
            plot_against.title.text = plot_against.title.text.replace(/\\d+\\.\\d{2}.$/, p_text_against + ".");

            // Net goals plot
            plot_net.title.text = plot_net.title.text.replace(/\\d{4}/, start_year);
            plot_net.title.text = plot_net.title.text.replace(/\\d{1}/, league_tier);
            const p_text_net = data_selected.data.net_goals_p[0].toFixed(2);
            const r2_text_net = data_selected.data.net_goals_r2[0].toFixed(2);
            plot_net.title.text = plot_net.title.text.replace(/\\d+\\.\\d{2}/, r2_text_net);
            plot_net.title.text = plot_net.title.text.replace(/\\d+\\.\\d{2}.$/, p_text_net + ".");
        """)

    # Connect the JavaScript callback to the interactive controls
    # This makes the charts interactive by updating when slider or radio button changes
    year_slider.js_on_change('value', callback_charts_update)
    radio_button_group.js_on_change('active', callback_charts_update)

    # Generate HTML components for embedding in web pages
    # Creates separate script and div elements for plots and controls
    script, divs = components((column(*plots),
                               column(radio_button_group, year_slider)))

    # Return dictionary containing all components for HTML embedding
    # Organized by type (script, plots, controls) for easy integration
    return {'script': {'script': script, 'title': column_name},
            'plots': {'div': divs[0], 'title': column_name + "_plots"},
            'controls': {'div': divs[1], 'title': column_name + "_controls"}
            }


if __name__ == "__main__":
    """
    Main execution block for the goals vs foreigners analysis.

    This script analyzes the relationship between team performance (goals) and
    foreign player characteristics in English football. It creates interactive
    visualizations that can be embedded in web pages for data exploration.
    """

    # Create necessary directories if they don't exist
    # Ensures the required folder structure is in place for outputs
    folders = ["Data", "Plots"]
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)

    try:
        # Set up logging for the analysis with timestamps and file output
        setup_logging()
        logging.info("Starting goals vs foreigners analysis")

        # Load match data from CSV file containing historical match results
        # This includes goals scored, conceded, and other match statistics
        matches = pd.read_csv(
            filepath_or_buffer="../../../EPL predictor/2 Data preparation/Data/matches.csv",
            low_memory=False)

        # Load TransferMarkt data containing foreign player information
        # Includes foreigner count, market values, ages, and squad sizes
        foreigners = pd.read_csv(
            filepath_or_buffer="../../../EPL predictor/1 Data downloads/TransferMarkt-values/Data/transfermarkt.csv",
            low_memory=False).drop(columns=["league_tier", "league"])

        # Transform data from wide to long format for analysis
        # Converts match data to a format suitable for statistical analysis
        matches = wide_to_long_matches(matches=matches)

        # Merge match data with TransferMarkt data by club and season
        # Combines performance metrics with team characteristics for analysis
        goals = matches.merge(foreigners, on=["club_name", "season"], how="left")

        # Create interactive visualizations for data exploration
        # Generate plots for foreigner count analysis with statistical fits
        foreigner_plots = plot_data(data=goals,
                                    column_name="foreigner_count")

        # Save interactive plots to HTML file for web embedding
        # Creates a self-contained HTML file with all interactive features
        save_plots(plots=[foreigner_plots],
                   file_name="foreigner_count.html")

    except Exception as e:
        # Log error with line number for debugging and troubleshooting
        # Provides detailed error information for development and maintenance
        logging.error(f"Analysis failed at line {e.__traceback__.tb_lineno}: "
                      f"{str(e)}")
        sys.exit(1)
