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
from bokeh.models import ColumnDataSource, HoverTool, BoxAnnotation, LegendItem, Legend
import os
import webbrowser
import bokeh

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_data() -> pd.DataFrame:
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
        csv_path =os.path.join("..",
                                   "..",
                                   "Data preparation",
                                   "Data",
                                   "match_attendance_discipline.csv")
        
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


def plot_goals_per_game(*, matches: pd.DataFrame, std: bool = True) -> tuple[str, str]:
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

            # Get unique league tiers and sort them for consistent ordering
    leagues = sorted(goals_per_game['league_tier'].unique())

        # Create color palette for different league tiers
    # Use Category10 palette with at least 3 colors, max 10
    palette = Category10[
        max(3, min(10, len(leagues)))
    ]

    # Map each league tier to a color from the palette
    color_map = {
        league: palette[i % len(palette)]
        for i, league in enumerate(leagues)
    }
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
    leagues = sorted(goals_per_game['league_tier'].unique())
    colors = Category10[len(leagues)]

    # Create color mapping
    color_map = {league: colors[i] for i, league in enumerate(leagues)}

    # Create legend items
    legend_list = []
    for league in leagues:
        league_data = goals_per_game[goals_per_game['league_tier'] == league]
        # Create ColumnDataSource for the league data to enable hover
        # tooltips
        source = ColumnDataSource(league_data)
        renderers = []

        # Create line plot for each league
        line = p.line(
            x='season_start',
            y='total_goals_mean',
            color=color_map[league],
            line_width=2,
            source=source
        )
        renderers.append(line)

        if std:
            area = p.varea(
                x=league_data['season_start'],
                y1=(league_data['total_goals_mean'] - 
                    league_data['total_goals_std']),
                y2=(league_data['total_goals_mean'] + 
                    league_data['total_goals_std']),
                color=color_map[league],
                fill_alpha=0.3
            )
            renderers.append(area)

        # Add scatter points
        points = p.scatter(
            x='season_start',
            y='total_goals_mean',
            fill_color=color_map[league],
            line_color=color_map[league],
            size=8,
            source=ColumnDataSource(league_data)
        )
        renderers.append(points)

        # Add both scatter and line renderers to legend for this league
        legend_list.append(LegendItem(
            label=f"{league}",
            renderers=renderers
        ))

    # Create and configure the legend
    legend = Legend(
        items=legend_list,
        location="center",
        border_line_color="black",
        border_line_width=1,
        click_policy="hide",
        title="League\ntier",
    )
    p.add_layout(legend, "right")

    # Add hover tooltip for all data points
    p.add_tools(HoverTool(
        tooltips=[
            ("League", "@league_tier"),
            ("Season", "@season_start"),
            ("Mean Goals", "@total_goals_mean{0.2f}")
        ]
    ))

    # Rotate x-axis labels for better readability
    p.xaxis.major_label_orientation = 45

    logger.info("Goals per game plot created successfully")
    return components(p)


def plot_goal_difference_per_game(*, matches: pd.DataFrame) -> tuple[str, str]:
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
    # Create color palette for different league tiers
    # Use Category10 palette with at least 3 colors, max 10
    palette = Category10[
        max(3, min(10, len(leagues)))
    ]

    # Map each league tier to a color from the palette
    color_map = {
        league: palette[i % len(palette)]
        for i, league in enumerate(leagues)
    }


    # Create legend items
    legend_list = []

    for league in leagues:
        league_data = goal_diff_per_game[
            goal_diff_per_game['league_tier'] == league
        ]

        # Create ColumnDataSource for the league data to enable hover
        # tooltips
        source = ColumnDataSource(league_data)
        # Create line plot for each league
        line = p.line(
            x='season_start',
            y='goal_difference',
            color=color_map[league],
            line_width=2,
            source=source
        )

        # Add scatter points
        points = p.scatter(
            x='season_start',
            y='goal_difference',
            fill_color=color_map[league],
            line_color=color_map[league],
            size=8,
            source=source
        )
        renderers = [line, points]
        legend_list.append(LegendItem(
            label=f"{league}",
            renderers=renderers
        ))

    # Create and configure the legend
    legend = Legend(
        items=legend_list,
        location="center",
        border_line_color="black",
        border_line_width=1,
        click_policy="hide",
        title="League\ntier",
    )
    p.add_layout(legend, "right")

    # Add hover tooltip for all data points
    p.add_tools(HoverTool(
        tooltips=[
            ("League", "@league_tier"),
            ("Season", "@season_start"),
            ("Goal Difference", "@goal_difference{0.2f}")
        ]
    ))

    # Rotate x-axis labels for better readability
    p.xaxis.major_label_orientation = 45

    logger.info("Goal difference per game plot created successfully")
    return components(p)


if __name__ == "__main__":
    try:
        # Read the match data
        matches = read_data()

        # Create the plots
        goals_plot_std_script, goals_plot_std_div = plot_goals_per_game(matches=matches, std=True)
        goals_plot_no_std_script, goals_plot_no_std_div = plot_goals_per_game(matches=matches, std=False)
        goal_diff_plot_script, goal_diff_plot_div = plot_goal_difference_per_game(matches=matches)

        divs = [goals_plot_std_div, goals_plot_no_std_div, goal_diff_plot_div]
        scripts = [goals_plot_std_script, goals_plot_no_std_script, goal_diff_plot_script]

        # Save divs and scripts to files
        for index, div in enumerate(divs):
            with open(f"Plots/div_{index}.txt", "w") as f:
                f.write("<div align='center'>\n")
                f.write(div)
                f.write("\n")
                f.write("</div>\n")
        for index, script in enumerate(scripts):
            with open(f"Plots/script_{index}.txt", "w") as f:
                f.write(script)

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

        # save html to file
        with open("Plots/goals.html", "w") as f:
            # Header equivalent - include Bokeh script imports
            f.write("<!-- Script imports -->\n")
            f.write(imported_scripts)
            # Body equivalent - add HTML content
            f.write("<!-- HTML body -->\n")
            # Text content
            f.write(f"""<p>{lorem}</p>\n""")
            for div in divs:
                # Plot container with center alignment
                f.write("<div align='center'>\n")
                f.write(div)
                f.write("\n")
                f.write("</div>\n")
                f.write(f"""<p>{lorem}</p>\n""")
            # Chart scripts for interactive functionality
            f.write("<!-- Chart scripts -->\n")
            for script in scripts:
                f.write(script)
                f.write("\n")

        # Open the generated plot in the default web browser
        webbrowser.open(
            'file:///' + os.path.abspath(
                os.path.join("Plots", "goals.html")
            )
    )


        logger.info("Analysis completed successfully")

    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise 