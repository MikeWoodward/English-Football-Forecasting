#!/usr/bin/env python3
"""
Goals Analysis Module

This module provides functions to analyze football match data including
goals per game and goal differences across different leagues and seasons.
"""

import logging
import pandas as pd
from bokeh.plotting import figure, show
from bokeh.embed import file_html, components
from bokeh.resources import CDN
from bokeh.layouts import column
from bokeh.palettes import Category10
from bokeh.models import ColumnDataSource, HoverTool, BoxAnnotation


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_data(*, csv_path: str = "Data/merged_match_data.csv") -> pd.DataFrame:
    """
    Read match data from CSV file into a pandas DataFrame.

    Args:
        csv_path: Path to the CSV file containing match data.

    Returns:
        pd.DataFrame: DataFrame containing match data with columns:
            season, league_tier, match_date, home_goals, away_goals, etc.

    Raises:
        FileNotFoundError: If the CSV file is not found.
        pd.errors.EmptyDataError: If the CSV file is empty.
        pd.errors.ParserError: If there are parsing errors in the CSV.
    """
    try:
        logger.info(f"Reading data from {csv_path}")
        matches = pd.read_csv(csv_path, low_memory=False)
        matches['season_start'] = (
            matches['season']
            .str.split('-')
            .str[0]
            .astype(int)
        )
        logger.info(
            f"Successfully loaded {len(matches)} matches"
        )
        return matches
    except FileNotFoundError as e:
        logger.error(f"File not found: {csv_path}")
        raise FileNotFoundError(f"CSV file not found at {csv_path}") from e
    except pd.errors.EmptyDataError as e:
        logger.error(f"CSV file is empty: {csv_path}")
        raise pd.errors.EmptyDataError(f"CSV file is empty: {csv_path}") from e
    except pd.errors.ParserError as e:
        logger.error(f"Error parsing CSV file: {csv_path}")
        raise pd.errors.ParserError(f"Error parsing CSV file: {csv_path}") from e


def plot_goals_per_game(*, matches: pd.DataFrame, std: bool = True) -> figure:
    """
    Create a Bokeh plot showing total goals per game by league and season.

    Args:
        matches: DataFrame containing match data with columns:
            season, league_tier, home_goals, away_goals.

    Returns:
        figure: Bokeh figure object showing goals per game trends.
    """
    logger.info("Creating goals per game plot")

    # Calculate total goals per match
    matches['total_goals'] = matches['home_goals'] + matches['away_goals']

    # Group by season and league_tier, calculate mean goals per game
    goals_per_game = (
        matches.groupby(['season_start', 'league_tier'])
        .agg(
            total_goals_mean=pd.NamedAgg(
                column="total_goals", aggfunc="mean"
            ),
            total_goals_std=pd.NamedAgg(
                column="total_goals", aggfunc="std"
            )
        )
        .reset_index()
    )

    title = "Mean Goals Per Game by League and Season"
    if std:
        title += " with Standard Deviation"

    # Create figure
    p = figure(
        width=600,
        height=400,
        title=title,
        x_axis_label="Season",
        y_axis_label="Mean Goals Per Game",
        tools="pan,box_zoom,wheel_zoom,reset,save"
    )

    # Add visual annotation for WWII period (1939-1945)
    # This helps identify potential data gaps or anomalies during wartime
    wwii_band = BoxAnnotation(
        left=1939, right=1945,
        fill_color='lightcoral', fill_alpha=0.3
    )
    p.add_layout(wwii_band)

    # Add visual annotation for WWI period (1914-1918)
    # Similar to WWII, helps identify wartime effects on football data
    wwi_band = BoxAnnotation(
        left=1914, right=1918,
        fill_color='lightcoral', fill_alpha=0.3
    )
    p.add_layout(wwi_band)

    # Get unique leagues for color coding
    leagues = goals_per_game['league_tier'].unique()
    colors = Category10[len(leagues)]

    # Create legend items
    legend_items = []

    for league, color in zip(leagues, colors):
        league_data = goals_per_game[goals_per_game['league_tier'] == league]

        # Create line plot for each league
        line = p.line(
            x='season_start',
            y='total_goals_mean',
            line_color=color,
            line_width=2,
            legend_label=f"{league}",
            source=ColumnDataSource(league_data)
        )

        if std:
            p.varea(
                x=league_data['season_start'],
                y1=(league_data['total_goals_mean'] - 
                    league_data['total_goals_std']),
                y2=(league_data['total_goals_mean'] + 
                    league_data['total_goals_std']),
                legend_label=f"{league}",
                fill_color=color,
                fill_alpha=0.3
            )

        # Add scatter points
        points = p.scatter(
            x='season_start',
            y='total_goals_mean',
            fill_color=color,
            size=8,
            legend_label=f"{league}",
            source=ColumnDataSource(league_data)
        )

        legend_items.append((f"{league}", [line, points]))

    # Configure legend to be interactive (click to hide/show series)
    p.legend.title = 'League\nTier'
    p.legend.click_policy = "hide"
    p.legend.location = "right"
    p.legend.orientation = "vertical"
    p.legend.spacing = 10
    p.legend.margin = 20
    p.legend.padding = 10
    p.legend.border_line_color = "black"
    p.legend.border_line_width = 1
    p.legend.background_fill_color = "white"
    p.legend.background_fill_alpha = 0.8

    # Hack to place the legend outside the plot
    p.add_layout(p.legend[0], 'right')

    # Add hover tool
    hover = HoverTool(
        tooltips=[
            ("Season", "@season_start"),
            ("League Tier", "@league_tier"),
            ("Mean Goals/Game", "@total_goals_mean{0.2f}")
        ]
    )
    p.add_tools(hover)

    # Rotate x-axis labels for better readability
    p.xaxis.major_label_orientation = 45

    logger.info("Goals per game plot created successfully")
    return p


def plot_goal_difference_per_game(*, matches: pd.DataFrame) -> figure:
    """
    Create a Bokeh plot showing goal difference per game by league and season.

    Args:
        matches: DataFrame containing match data with columns:
            season, league_tier, home_goals, away_goals.

    Returns:
        figure: Bokeh figure object showing goal difference trends.
    """
    logger.info("Creating goal difference per game plot")

    # Calculate goal difference (absolute value of home goals - away goals)
    matches['goal_difference'] = abs(matches['home_goals'] - matches['away_goals'])

    # Group by season and league_tier, calculate mean goal difference
    goal_diff_per_game = (
        matches.groupby(['season_start', 'league_tier'])
        ['goal_difference']
        .mean()
        .reset_index()
    )

    # Create figure
    p = figure(
        width=600,
        height=400,
        title="Mean Goal Difference Per Game by League and Season",
        x_axis_label="Season",
        y_axis_label=(
            "Mean Goal Difference (Absolute Value of Home - Away)"
        ),
        tools="pan,box_zoom,wheel_zoom,reset,save"
    )

    # Add visual annotation for WWII period (1939-1945)
    # This helps identify potential data gaps or anomalies during wartime
    wwii_band = BoxAnnotation(
        left=1939, right=1945,
        fill_color='lightcoral', fill_alpha=0.3
    )
    p.add_layout(wwii_band)

    # Add visual annotation for WWI period (1914-1918)
    # Similar to WWII, helps identify wartime effects on football data
    wwi_band = BoxAnnotation(
        left=1914, right=1918,
        fill_color='lightcoral', fill_alpha=0.3
    )
    p.add_layout(wwi_band)

    # Get unique leagues for color coding
    leagues = goal_diff_per_game['league_tier'].unique()
    colors = Category10[len(leagues)]

    # Create legend items
    legend_items = []

    for league, color in zip(leagues, colors):
        league_data = goal_diff_per_game[
            goal_diff_per_game['league_tier'] == league
        ]

        # Create line plot for each league
        line = p.line(
            x='season_start',
            y='goal_difference',
            line_color=color,
            line_width=2,
            legend_label=f"{league}",
            source=ColumnDataSource(league_data)
        )

        # Add scatter points
        points = p.scatter(
            x='season_start',
            y='goal_difference',
            fill_color=color,
            size=8,
            legend_label=f"{league}",
            source=ColumnDataSource(league_data)
        )

        legend_items.append((f"{league}", [line, points]))

    # Configure legend to be interactive (click to hide/show series)
    p.legend.title = 'League\nTier'
    p.legend.click_policy = "hide"
    p.legend.location = "right"
    p.legend.orientation = "vertical"
    p.legend.spacing = 10
    p.legend.margin = 20
    p.legend.padding = 10
    p.legend.border_line_color = "black"
    p.legend.border_line_width = 1
    p.legend.background_fill_color = "white"
    p.legend.background_fill_alpha = 0.8

    # Hack to place the legend outside the plot
    p.add_layout(p.legend[0], 'right')

    # Add hover tool
    hover = HoverTool(
        tooltips=[
            ("Season", "@season_start"),
            ("League Tier", "@league_tier"),
            ("Avg Goal Difference", "@goal_difference{0.2f}")
        ]
    )
    p.add_tools(hover)

    # Rotate x-axis labels for better readability
    p.xaxis.major_label_orientation = 45

    logger.info("Goal difference per game plot created successfully")
    return p


if __name__ == "__main__":
    try:
        # Read the match data
        matches = read_data()

        # Create the plots
        goals_plot_std = plot_goals_per_game(matches=matches, std=True)
        goals_plot_no_std = plot_goals_per_game(matches=matches, std=False)
        goal_diff_plot = plot_goal_difference_per_game(matches=matches)

        layout = column(goals_plot_std, goals_plot_no_std, goal_diff_plot)

        html = file_html(layout, CDN, "my plot")
        # save html to file
        with open("Plots/plot.html", "w") as f:
            f.write(html)

        for index, plot in enumerate([
            goals_plot_std, goals_plot_no_std, goal_diff_plot
        ]):
            script, div = components(plot)
            with open(f"Plots/script_{index}.txt", "w") as f:
                f.write(script)
            with open(f"Plots/div_{index}.txt", "w") as f:
                f.write(div)

        # Display both plots together
        show(layout)

        logger.info("Analysis completed successfully")

    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise 