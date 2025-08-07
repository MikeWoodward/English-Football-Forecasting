#!/usr/bin/env python3
"""
Discipline analysis module.

This module contains functions for analyzing discipline-related data.
"""

import logging
import pandas as pd
import os
from typing import Dict
from bokeh.plotting import figure
from bokeh.models import Legend, LegendItem
from bokeh.embed import components
from bokeh.palettes import Category10
import bokeh
import webbrowser
# For interactive tooltips
from bokeh.models import HoverTool, ColumnDataSource

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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


def plot_total_discipline(*, discipline_data, plot_width, plot_height):
    """Plot the total discipline data."""
    discipline_totals = discipline_data.groupby(
        ['league_tier', 'season_start']
    ).agg(**{
        "Mean red cards": ('red_cards', 'mean'),
        "Mean yellow cards": ('yellow_cards', 'mean'),
        "Mean fouls": ('fouls', 'mean')
    }).reset_index()

    leagues = discipline_totals['league_tier'].unique()
    color_palette = _create_color_palette(leagues=leagues)

    divs = []
    scripts = []
    titles = []
    for discipline in ['Mean red cards', 'Mean yellow cards', 'Mean fouls']:
        title = f"{discipline} per match per league per season"
        plot = figure(
            title=title,
            x_axis_label="Season start",
            y_axis_label=f"{discipline}",
            width=plot_width,
            height=plot_height
        )
        legend_list = []
        for league in leagues:
            # Filter data for current league tier
            league_data = discipline_totals[
                discipline_totals['league_tier'] == league
            ]
            # Create ColumnDataSource for the league data to enable hover tooltips
            source = ColumnDataSource(league_data)
            # Create scatter plot points for the current league
            renderer_scatter = plot.scatter(
                x='season_start',
                y=discipline,
                size=8,
                color=color_palette[league],
                source=source
            )
            # Create line plot connecting the points for the current league
            renderer_line = plot.line(
                x='season_start',
                y=discipline,
                color=color_palette[league],
                line_width=2,
                source=source
            )
            # Add both scatter and line renderers to legend for this league
            legend_list.append(LegendItem(
                label=f"{league}",
                renderers=[renderer_scatter, renderer_line]
            ))

        # Add hover tooltip for all data points
        plot.add_tools(HoverTool(
            tooltips=[
                ("League", "@league_tier"),
                ("Season", "@season_start"),
                (discipline, "@{" + discipline + "}")
            ]
        ))

        legend = Legend(
            items=legend_list,
            location="center",
            border_line_color="black",
            border_line_width=1,
            click_policy="hide",
            title="League\ntier",
        )
        plot.add_layout(legend, "right")

        # Generate HTML components for the plot (script and div)
        script, div = components(plot)
        divs.append(div)
        scripts.append(script)
        titles.append(title)

    return divs, scripts, titles


def plot_away_bias(*, discipline_data, plot_width, plot_height):
    """Plot the away bias data."""
    discipline_totals = discipline_data.groupby(
        ['league_tier', 'season_start']
    ).agg(**{
        "Total red cards": ('red_cards', 'sum'),
        "Total yellow cards": ('yellow_cards', 'sum'),
        "Total fouls": ('fouls', 'sum'),
        "Away red cards": ('away_red_cards', 'sum'),
        "Away yellow cards": ('away_yellow_cards', 'sum'),
        "Away fouls": ('away_fouls', 'sum'),
    }).reset_index()
    discipline_totals['Away red cards fraction'] = (
        discipline_totals['Away red cards'] /
        discipline_totals['Total red cards']
    )
    discipline_totals['Away yellow cards fraction'] = (
        discipline_totals['Away yellow cards'] /
        discipline_totals['Total yellow cards']
    )
    discipline_totals['Away fouls fraction'] = (
        discipline_totals['Away fouls'] / discipline_totals['Total fouls']
    )

    leagues = discipline_totals['league_tier'].unique()
    color_palette = _create_color_palette(leagues=leagues)

    divs = []
    scripts = []
    titles = []
    for discipline in ['Away red cards fraction', 'Away yellow cards fraction',
                      'Away fouls fraction']:
        title = f"{discipline} per league per season"
        plot = figure(
            title=title,
            x_axis_label="Season start",
            y_axis_label=f"{discipline}",
            width=plot_width,
            height=plot_height
        )
        legend_list = []
        for league in leagues:
            # Filter data for current league tier
            league_data = discipline_totals[
                discipline_totals['league_tier'] == league
            ]
            # Create ColumnDataSource for the league data to enable hover tooltips
            source = ColumnDataSource(league_data)
            # Create scatter plot points for the current league
            renderer_scatter = plot.scatter(
                x='season_start',
                y=discipline,
                size=8,
                color=color_palette[league],
                source=source
            )
            # Create line plot connecting the points for the current league
            renderer_line = plot.line(
                x='season_start',
                y=discipline,
                color=color_palette[league],
                line_width=2,
                source=source
            )
            # Add both scatter and line renderers to legend for this league
            legend_list.append(LegendItem(
                label=f"{league}",
                renderers=[renderer_scatter, renderer_line]
            ))

        # Add hover tooltip for all data points
        plot.add_tools(HoverTool(
            tooltips=[
                ("League", "@league_tier"),
                ("Season", "@season_start"),
                (discipline, "@{" + discipline + "}")
            ]
        ))

        legend = Legend(
            items=legend_list,
            location="center",
            border_line_color="black",
            border_line_width=1,
            click_policy="hide",
            title="League\ntier",
        )
        plot.add_layout(legend, "right")

        # Generate HTML components for the plot (script and div)
        script, div = components(plot)
        divs.append(div)
        scripts.append(script)
        titles.append(title)

    return divs, scripts, titles


def save_plots(*, divs, scripts, titles):
    """Save the plots to the HTML folder."""
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
    with open(os.path.join("Plots", "discipline.html"), "w") as f:
        # Header equivalent - include Bokeh script imports
        f.write("<!-- Script imports -->\n")
        f.write(imported_scripts)
        # Body equivalent - add HTML content
        f.write("<!-- HTML body -->\n")
        # Text content
        f.write(f"""<p>{lorem}</p>\n""")

        for index, div in enumerate(divs):
            # Plot container with center alignment
            f.write(f"<!-- Plot {titles[index]} -->\n")
            f.write("<div align='center'>\n")
            f.write(div)
            f.write("\n")
            f.write("</div>\n")
            f.write(f"""<p>{lorem}</p>\n""")

        # Chart scripts for interactive functionality
        f.write("<!-- Chart scripts -->\n")
        for index, script in enumerate(scripts):
            f.write(f"<!-- Plot {titles[index]} -->\n")
            f.write(script)
            f.write("\n")

    # Write each of the scripts to a separate file
    for index, script in enumerate(scripts):
        with open(os.path.join("Plots", f"script_{index+1}.txt"), "w") as f:
            f.write(f"<!--Chart script {titles[index]}-->\n")
            f.write(script)
    # Write all scripts to a combo file
    with open(os.path.join("Plots", "scripts.txt"), "w") as f:  
        f.write("<!-- Discipline scripts -->\n")
        f.write("<!------------------------>\n")
        for index, script in enumerate(scripts):
            f.write(f"<!--Chart script {titles[index]}-->\n")
            f.write(script)
            f.write("\n")

    # Write each of the divs to a separate file
    for index, div in enumerate(divs):
        with open(os.path.join("Plots", f"div_{index+1}.txt"), "w") as f:
            f.write(f"<!-- Plot {titles[index]} -->\n")
            f.write("<div align='center'>\n")
            f.write("    " + div)
            f.write("\n")
            f.write("</div>\n")

    # Open the generated plot in the default web browser
    webbrowser.open(
        'file:///' + os.path.abspath(
            os.path.join("Plots", "discipline.html")
        )
    )


if __name__ == "__main__":
    """Main execution block."""
    logger.info("Starting discipline analysis")

    # Read in the discipline data
    discipline_file_name = os.path.join(
        "..", "..", "2 Data preparation", "Data",
        "match_attendance_discipline.csv"
    )
    discipline_data = pd.read_csv(discipline_file_name, low_memory=False)

    # Select the subset we're going to analyze.
    # League_tiers 1 to 4 only.
    discipline_data = discipline_data[
        discipline_data['league_tier'].isin([1, 2, 3, 4])
    ]

    # Add extra fields we need
    discipline_data['season_start'] = discipline_data['season'].apply(
        lambda x: x.split('-')[0]
    ).astype(int)
    discipline_data['red_cards'] = (
        discipline_data['home_red_cards'] + discipline_data['away_red_cards']
    )
    discipline_data['yellow_cards'] = (
        discipline_data['home_yellow_cards'] +
        discipline_data['away_yellow_cards']
    )
    discipline_data['fouls'] = (
        discipline_data['home_fouls'] + discipline_data['away_fouls']
    )

    # Plot total discipline charts
    plot_width = 600
    plot_height = 400
    divs1, scripts1, titles1 = plot_total_discipline(
        discipline_data=discipline_data,
        plot_width=plot_width,
        plot_height=plot_height
    )
    divs2, scripts2, titles2 = plot_away_bias(
        discipline_data=discipline_data,
        plot_width=plot_width,
        plot_height=plot_height
    )
    divs = divs1 + divs2
    scripts = scripts1 + scripts2
    titles = titles1 + titles2

    # Save to folder
    save_plots(divs=divs, scripts=scripts, titles=titles)

    logger.info("Discipline analysis completed")
