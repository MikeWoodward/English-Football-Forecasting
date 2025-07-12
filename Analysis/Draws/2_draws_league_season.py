"""
Analysis of draw fractions by league and season.

This module provides functions to analyze how the fraction of draws varies
across different leagues and seasons, including confidence interval
calculations and visualization.
"""

import logging
import pandas as pd
from bokeh.plotting import figure, show, column
from bokeh.palettes import Category10
from bokeh.embed import file_html, components
from bokeh.resources import CDN
from typing import Dict, Any
from bokeh.models import BoxAnnotation, Span, Div
import numpy as np
import os
# Configure logging for tracking execution progress and debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_data(*, file_path: str) -> pd.DataFrame:
    """
    Read CSV data file and return a Pandas dataframe.

    Args:
        file_path: Path to the CSV file containing match data.

    Returns:
        pd.DataFrame: DataFrame containing the match data.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        pd.errors.EmptyDataError: If the CSV file is empty.
        pd.errors.ParserError: If the CSV file cannot be parsed.
    """
    try:
        logger.info(
            f"Reading data from {file_path}"
        )
        data = pd.read_csv(file_path, low_memory=False)
        logger.info(
            f"Successfully loaded {len(data)} rows of data"
        )
        return data
    except FileNotFoundError:
        # Handle case where file doesn't exist
        logger.error(
            f"File not found: {file_path}"
        )
        raise
    except pd.errors.EmptyDataError:
        # Handle case where CSV file is empty
        logger.error(
            f"CSV file is empty: {file_path}"
        )
        raise
    except pd.errors.ParserError as e:
        # Handle CSV parsing errors
        logger.error(
            f"Error parsing CSV file {file_path}: {e}"
        )
        raise
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(
            f"Unexpected error reading file {file_path}: {e}"
        )
        raise


def analyze_draws(*, data: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze draw fractions for each league and season with confidence
    intervals.

    Args:
        data: DataFrame containing match data with columns for league,
            season, and match result.

    Returns:
        Dict containing analysis results with draw fractions and confidence
        intervals for each league-season combination.

    Raises:
        ValueError: If required columns are missing from the data.
        KeyError: If expected data structure is not found.
    """
    try:
        logger.info(
            "Starting draw fraction analysis"
        )

        # Create result columns based on goal differences
        # 'draw' if goals are equal, 'win' if home scored more, 'loss' otherwise
        data['home_result'] = data.apply(
            lambda x: (
                'draw' if x['home_goals'] == x['away_goals'] else
                'win' if x['home_goals'] > x['away_goals'] else 'loss'
            ),
            axis=1
        )
        # Create away team result (mirror of home result)
        data['away_result'] = data.apply(
            lambda x: (
                'draw' if x['away_goals'] == x['home_goals'] else
                'win' if x['away_goals'] > x['home_goals'] else 'loss'
            ),
            axis=1
        )
        # Extract the starting year from season format (e.g., "2020-2021" -> 2020)
        data['season_start'] = (
            data['season']
            .str.split('-')
            .str[0]
            .astype(int)
        )

        # Create groupby object for aggregating by league tier and season
        league_tier_season_groupby = data.groupby(
            ['league_tier', 'season_start']
        )

        # Calculate count of each result type (win/loss/draw) per league and season
        draw_fraction = (
            league_tier_season_groupby.agg(
                {'home_result': 'value_counts'}
            ).rename(
                columns={'home_result': 'result_count'}
            ).reset_index()
        )

        # Calculate total matches played per league and season
        matches_per_season = (
            league_tier_season_groupby.size().to_frame(
                'matches_played'
            ).reset_index()
        )

        # Merge result counts with total matches to get proportions
        match_results = pd.merge(
            draw_fraction, matches_per_season,
            on=['season_start', 'league_tier'],
            how="inner"
        )

        # Calculate proportion of each result type
        match_results['proportion'] = (
            match_results['result_count'] /
            match_results['matches_played']
        )

        # Calculate standard deviation of proportion using binomial distribution
        # SE = sqrt(p * (1-p) / n) where p is proportion and n is sample size
        match_results['proportion_std'] = np.sqrt(
            match_results['proportion'] *
            (1 - match_results['proportion']) /
            match_results['matches_played']
        )

        # Calculate standard deviation band
        match_results['proportion_lower'] = (
            match_results['proportion'] -
            match_results['proportion_std']
        )
        match_results['proportion_upper'] = (
            match_results['proportion'] +
            match_results['proportion_std']
        )

        # Filter to show only draw results (since we're analyzing draw fractions)
        match_results = match_results[
            match_results['home_result'] == 'draw'
        ]

        logger.info("Draw fraction analysis completed")
        return match_results

    except KeyError as e:
        # Handle missing required columns in the data
        logger.error(
            f"Missing required column in data: {e}"
        )
        raise
    except ValueError as e:
        # Handle invalid data format or values
        logger.error(
            f"Invalid data format: {e}"
        )
        raise
    except Exception as e:
        # Catch any other unexpected errors during analysis
        logger.error(
            f"Unexpected error in draw analysis: {e}"
        )
        raise


def analyze_win_fraction(*, match_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze win fractions for each team and season.

    Args:
        match_data: DataFrame containing match data with columns for team,
            season, and match result.

    Returns:
        Dict containing analysis results with win fractions and confidence
        intervals for each team-season combination.

    Raises:
        ValueError: If required columns are missing from the data.
        KeyError: If expected data structure is not found.
    """

    # Extract the starting year from season format (e.g., "2020-2021" -> 2020)
    match_data['season_start'] = (
        match_data['season']
        .str.split('-')
        .str[0]
        .astype(int)
    )

    # Home team win fraction
    match_data['home_result'] = match_data.apply(
        lambda x: (
            'draw' if x['home_goals'] == x['away_goals'] else
            'win' if x['home_goals'] > x['away_goals'] else 'loss'
        ),
        axis=1
    )
    match_data['away_result'] = match_data.apply(
        lambda x: (
            'draw' if x['away_goals'] == x['home_goals'] else
            'win' if x['away_goals'] > x['home_goals'] else 'loss'
        ),
        axis=1
    )

    home_clubs = (
        match_data[['season_start', 'league_tier', 'home_club',
                   'home_result', 'match_date']].rename(
            columns={'home_club': 'club', 'home_result': 'result'}
        )
    )
    # Prepare home club results with standardized column names
    away_clubs = (
        match_data[['season_start', 'league_tier', 'away_club',
                   'away_result', 'match_date']].rename(
            columns={'away_club': 'club', 'away_result': 'result'}
        )
    )
    # Merge and sort
    clubs = pd.concat([
        home_clubs, away_clubs
    ]).sort_values(
        by=['season_start', 'league_tier', 'club', 'match_date']
    )
    # Calculate results fraction
    club_proportion = clubs[['season_start', 'league_tier', 'club',
                            'result']].groupby(
        ['season_start', 'league_tier', 'club']
    ).value_counts(normalize=True).reset_index(name='proportion')
    # Focus on wins
    club_proportion_wins = club_proportion[
        club_proportion['result'] == 'win'
    ]
    # Work out the win standard deviation
    clubs_wins_std = (
        club_proportion_wins[['season_start', 'league_tier',
                              'proportion']]
        .groupby(['season_start', 'league_tier'])
        .std()
        .reset_index()
        .sort_values(by=['season_start', 'league_tier'])
    )
    return clubs_wins_std


def plot_draw_results(*, draw_fraction: Dict[str, Any], ci: bool = True) -> None:
    """
    Create and display a plot of draw fractions vs season for each league.

    Args:
        analysis_results: Dictionary containing the analysis results from
                         analyze_draws function.

    Raises:
        ValueError: If analysis_results is missing required data.
        KeyError: If expected keys are not found in analysis_results.
    """
    try:
        logger.info("Creating draw fraction visualization")

        # Get unique league tiers and sort them for consistent ordering
        leagues = sorted(draw_fraction['league_tier'].unique())

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

        # Set title based on whether confidence intervals are shown
        title = (
            "Draw Fraction vs Season for All League Tiers - with std - interactive chart"
            if ci else "Draw Fraction vs Season for All League Tiers - no std - interactive chart"
        )

        # Create the main figure with appropriate dimensions and labels
        p = figure(
            title=title,
            x_axis_label="Season",
            y_axis_label="Draw Fraction",
            width=600,
            height=400
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

        # Add vertical reference lines for significant years
        # 1981 and 1992 may represent important changes in football rules
        line_1968 = Span(
            location=1968, dimension='height',
            line_color='blue', line_width=2
        )
        line_1981 = Span(
            location=1981, dimension='height',
            line_color='blue', line_width=2
        )
        line_1992 = Span(
            location=1992, dimension='height',
            line_color='blue', line_width=2
        )
        p.add_layout(line_1968)
        p.add_layout(line_1981)
        p.add_layout(line_1992)

        # Plot data for each league tier
        for league in leagues:
            # Filter data for current league tier
            league_data = draw_fraction[
                draw_fraction['league_tier'] == league
            ]

            # Plot the main trend line connecting draw fractions over time
            p.line(
                league_data['season_start'],
                league_data['proportion'],
                legend_label=f"{league}",
                line_width=2,
                color=color_map[league]
            )

            # Add confidence interval bands if requested
            if ci:
                p.varea(
                    x=league_data['season_start'],
                    y1=league_data['proportion_lower'],
                    y2=league_data['proportion_upper'],
                    legend_label=f"{league}",
                    fill_color=color_map[league],
                    fill_alpha=0.3
                )

            # Add scatter points to show individual data points
            p.scatter(
                league_data['season_start'],
                league_data['proportion'],
                legend_label=f"{league}",
                size=8,
                color=color_map[league]
            )

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

        return p

        logger.info("Visualization completed")

    except KeyError as e:
        # Handle missing required keys in the data
        logger.error(
            f"Missing required key in analysis_results: {e}"
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


def plot_win_fraction(*, win_fraction_std: Dict[str, Any]) -> None:
    """
    Create and display a plot of win fractions vs season for each league.
    """

    try:
        logger.info("Creating draw fraction visualization")

        # Get unique league tiers and sort them for consistent ordering
        leagues = sorted(win_fraction_std['league_tier'].unique())

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

        # Set title based on whether confidence intervals are shown
        title = "Win Fraction std vs Season for All League Tiers - interactive chart"

        # Create the main figure with appropriate dimensions and labels
        p = figure(
            title=title,
            x_axis_label="Season",
            y_axis_label="Win Fraction std",
            width=600,
            height=400
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

        # Add vertical reference lines for significant years
        # 1981 and 1992 may represent important changes in football rules
        line_1968 = Span(
            location=1968, dimension='height',
            line_color='blue', line_width=2
        )
        line_1981 = Span(
            location=1981, dimension='height',
            line_color='blue', line_width=2
        )
        line_1992 = Span(
            location=1992, dimension='height',
            line_color='blue', line_width=2
        )
        p.add_layout(line_1968)
        p.add_layout(line_1981)
        p.add_layout(line_1992)

        # Plot data for each league tier
        for league in leagues:
            # Filter data for current league tier
            league_data = win_fraction_std[
                win_fraction_std['league_tier'] == league
            ]

            # Plot the main trend line connecting draw fractions over time
            p.line(
                league_data['season_start'],
                league_data['proportion'],
                legend_label=f"{league}",
                line_width=2,
                color=color_map[league]
            )

            # Add scatter points to show individual data points
            p.scatter(
                league_data['season_start'],
                league_data['proportion'],
                legend_label=f"{league}",
                size=8,
                color=color_map[league]
            )

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

        return p

        logger.info("Visualization completed")

    except KeyError as e:
        # Handle missing required keys in the data
        logger.error(
            f"Missing required key in analysis_results: {e}"
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


if __name__ == "__main__":
    # Main execution block - demonstrates how to use the analysis functions
    try:
        # Read the match data from CSV file
        match_data = read_data(
            file_path=os.path.join("Data", "merged_match_data.csv")
        )

        # Perform statistical analysis of draw fractions
        draw_fraction = analyze_draws(data=match_data)

        # Create visualizations with confidence intervals
        draw_plot_ci = plot_draw_results(draw_fraction=draw_fraction)

        # Create visualizations without confidence intervals
        draw_plot_no_ci = plot_draw_results(
            draw_fraction=draw_fraction, ci=False
        )

        # Analyze win fraction standard deviation by teams
        win_fraction_std = analyze_win_fraction(match_data=match_data)
        win_fraction_plot = plot_win_fraction(
            win_fraction_std=win_fraction_std
        )

        # Chart layout as columns
        layout = column(
            Div(text="Placeholder"),
            draw_plot_ci,
            Div(text="Placeholder"),
            draw_plot_no_ci,
            Div(text="Placeholder"),
            win_fraction_plot,
            Div(text="Placeholder"),
        )

        html = file_html(layout, CDN, "my plot")
        # save html to file
        with open("Plots/plot.html", "w") as f:
            f.write(html)

        for index, plot in enumerate([draw_plot_ci, draw_plot_no_ci, win_fraction_plot]):
            script, div = components(plot)
            with open(f"Plots/script_{index}.txt", "w") as f:
                f.write(script)
            with open(f"Plots/div_{index}.txt", "w") as f:
                f.write(div)

        show(layout)

    except Exception as e:
        # Log any errors that occur during main execution
        logger.error(
            f"Error in main execution: {e}"
        )
        raise 