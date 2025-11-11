"""
Views for the trends app.
"""
from decimal import Decimal
from typing import Tuple, Union
import logging
import sys
import traceback
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.models import (
    ColumnDataSource,
    HoverTool,
    Legend,
    LegendItem,
)
from bokeh.models.annotations import BoxAnnotation
from bokeh.layouts import column
from bokeh.palettes import Category10
import numpy as np
from .models import (
    LeagueManager,
    AttendanceViolin,
)
import pandas as pd

PLOT_HEIGHT = 400

# Helper functions


def get_script_div_leagues_over_time(
    *,
    data: pd.DataFrame,
    title: str,
    y_axis_label: str,
    y_name: str,
    create_components: bool = True,
    show_wars: bool = True,
) -> Union[Tuple[str, str], figure]:
    """
    Get the script and div for the leagues over time chart.

    Args:
        data: DataFrame with league_tier, season_start, and y_name columns
        title: Chart title
        y_axis_label: Label for the y-axis
        y_name: Column name for the y-axis data
        create_components: Whether to create script and div components
        show_wars: Whether to show war period annotations

    Returns:
        Tuple of (script, div) if create_components is True,
        otherwise returns the plot figure
    """
    plot = figure(
        title=title,
        x_axis_label="Season start",
        y_axis_label=y_axis_label,
        height=PLOT_HEIGHT,
        sizing_mode="stretch_width",
        toolbar_location="right",
    )

    # Get the league tiers
    tiers = np.sort(data['league_tier'].unique())
    # Color for each league tier
    colors = Category10[len(tiers)]
    color_map = {league: colors[i] for i, league in enumerate(tiers)}

    # Create legend items
    legend_list = []

    # Now, build the chart by iterating through the league tiers
    for tier in tiers:
        league_data = data[data['league_tier'] == tier]
        # Create ColumnDataSource for the league data to enable hover
        # tooltips
        source = ColumnDataSource(league_data)
        renderers = []

        # Create line plot for each league
        line = plot.line(
            x='season_start',
            y=y_name,
            color=color_map[tier],
            line_width=2,
            source=source
        )
        renderers.append(line)

        # Add scatter points
        points = plot.scatter(
            x='season_start',
            y=y_name,
            fill_color=color_map[tier],
            line_color=color_map[tier],
            size=8,
            source=ColumnDataSource(league_data)
        )
        renderers.append(points)

        # Add both scatter and line renderers to legend for this league
        legend_list.append(LegendItem(
            label=f"{tier}",
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
    plot.add_layout(legend, "right")

    # Add hover tooltip for all data points
    plot.add_tools(HoverTool(
        tooltips=[
            ("League", "@league_tier"),
            ("Season", "@season_start"),
            (y_name, f"@{y_name}{{0.2f}}")
        ]
    ))

    if show_wars:
        # Add visual annotation for WWII period (1939-1945)
        # This helps identify potential data gaps or anomalies during wartime
        wwii_band = BoxAnnotation(
            left=1939,
            right=1945,
            fill_color='lightcoral',
            fill_alpha=0.3,
            name="wwii_band"
        )
        plot.add_layout(wwii_band)

        # Add visual annotation for WWI period (1914-1918)
        # Similar to WWII, helps identify wartime effects on football data
        wwi_band = BoxAnnotation(
            left=1914,
            right=1918,
            fill_color='lightcoral',
            fill_alpha=0.3,
            name="wwi_band"
        )
        plot.add_layout(wwi_band)

    # Rotate x-axis labels for better readability
    plot.xaxis.major_label_orientation = 45

    # Only create components when asked. Creating components binds the plot
    # to a Bokeh Document; that plot must not then be added to a different
    # Document
    # (e.g., via Tabs) or Bokeh will raise an ownership error.
    if create_components:
        script, div = components(plot)
        return script, div
    else:
        return plot


def get_attendance_violin_plot(
    *,
    data: pd.DataFrame,
    title: str,
    x_axis_label: str,
    x_name: str,
    y_axis_label: str,
    y_name: str,
    season_start: int,
    create_components: bool = True,
) -> Union[Tuple[str, str], figure]:
    """
    Get the script and div for the attendance violin plot.

    Args:
        data: DataFrame with league_tier, season_start, and data columns
        title: Chart title
        x_axis_label: Label for the x-axis
        x_name: Column name for the x-axis data
        y_axis_label: Label for the y-axis
        y_name: Column name for the y-axis data
        season_start: Season start year to filter data
        create_components: Whether to create script and div components

    Returns:
        Tuple of (script, div) if create_components is True,
        otherwise returns the plot figure
    """
    # Calculate attendance range for x-axis
    # Get min and max attendance values from the data
    attendance_max = int(data['attendance'].max())
    attendance_min = int(data['attendance'].min())
    # Calculate the range
    range = attendance_max - attendance_min
    # Add 5% padding on both sides for better visualization
    attendance_min = attendance_min - 0.05 * range
    attendance_max = attendance_max + 0.05 * range

    # Get unique league tiers and sort them
    tiers = np.sort(data['league_tier'].unique())
    # Assign colors to each league tier using Bokeh's Category10 palette
    colors = Category10[len(tiers)]
    color_map = {league: colors[i] for i, league in enumerate(tiers)}
    # List to store individual violin plots for each tier
    plots = []
    # Create a violin plot for each league tier
    for tier in tiers:
        # Filter data for this specific tier
        league_data = data[data['league_tier'] == tier]
        # Create ColumnDataSource with a named identifier
        # Note: name is used in JavaScript callback to identify the source
        # of the data for the plot
        source = ColumnDataSource(league_data,
                                  name=f"violin_attendance_data_tier_{tier}")
        # Calculate height for each plot (divide total height by number
        # of tiers)
        height = int(PLOT_HEIGHT / len(tiers))
        # Create a Bokeh figure for this tier's violin plot
        violin_plot = figure(
            title=f"Violin plot for league tier {tier} in {season_start}",
            # Only show x-axis label on the bottom plot (last tier)
            x_axis_label=x_axis_label if tier == tiers[-1] else None,
            # Set x-axis range to match calculated attendance range
            x_range=(attendance_min, attendance_max),
            # Add extra height to bottom plot to accommodate x-axis label
            height=height + 40 if tier == tiers[-1] else height,
            sizing_mode="stretch_width",
            toolbar_location="right",
            # Note: name is used in JavaScript callback to identify the plot
            # for the tier when updating dynamically
            name=f"violin_attendance_plot_tier_{tier}",
        )
        # Create the violin plot using varea (vertical area) glyph
        # This creates the violin shape by filling the area between y=0 and
        # y=probability_density
        violin_plot.varea(
            x=x_name,
            y1=0,
            y2=y_name,
            source=source,
            fill_color=color_map[tier],
            fill_alpha=0.3,
        )
        # Hide y-axis and y-grid for cleaner violin plot appearance
        violin_plot.yaxis.visible = False
        violin_plot.ygrid.visible = False
        # Only show x-axis on the bottom plot (last tier)
        violin_plot.xaxis.visible = False if tier != tiers[-1] else True
        plots.append(violin_plot)

    plots = column(plots,
                   sizing_mode="stretch_width")
    if create_components:
        script, div = components(plots)
        return script, div
    else:
        return plots


def error_page(
    request: HttpRequest,
    error_heading: str,
    error_text: str,
) -> HttpResponse:
    """
    Render an error page.

    Args:
        request: HTTP request object
        error_heading: Heading for the error message
        error_text: Text of the error message

    Returns:
        HTTP response with error page
    """
    context = {
        'error_heading': error_heading,
        'error_text': error_text
    }
    return render(
        request=request,
        template_name='trends/error.html',
        context=context
    )


@login_required
def trends_dashboard(request: HttpRequest) -> HttpResponse:
    """
    Display the trends dashboard with chart selection menu.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        HTTP response with dashboard page
    """
    context = {
        'title': 'Trends Analysis',
        'charts': [
            {
                'name': 'Goals by season and league tier',
                'url': 'trends:goals_over_time',
                'description': (
                    'Goal scoring trends across seasons and leagues'
                )
            },
            {
                'name': 'Home advantage over time',
                'url': 'trends:home_advantage_over_time',
                'description': (
                    'Home advantage trends across seasons and leagues'
                )
            },
            {
                'name': 'Draw fraction over time',
                'url': 'trends:draw_fraction_over_time',
                'description': 'Draw fraction by season and league tier'
            },
            {
                'name': 'Discipline over time',
                'url': 'trends:discipline_over_time',
                'description': (
                    'Mean red cards, yellow cards, and fouls per match by season and league tier'
                )
            },
            {
                'name': 'Attendance over time',
                'url': 'trends:attendance_over_time',
                'description': (
                    'Mean attendance per match by season and league tier'
                )
            },
            {
                'name': 'Inequality - win fraction standard deviation',
                'url': 'trends:inequality_win_fraction_sd_over_time',
                'description': (
                    'Win fraction standard deviation by '
                    'season and league tier. A measure of league inequality'
                )
            }
        ]
    }
    return render(
        request=request,
        template_name='trends/dashboard.html',
        context=context,
    )


@login_required
def goals_over_time(request: HttpRequest) -> HttpResponse:
    """
    Display a Bokeh chart showing goals over time from the Football database.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        HTTP response with goals over time chart page
    """
    try:
        # Get data from the database using Django model manager
        goals = LeagueManager().get_mean_goals_per_league_per_season()
        goals = pd.DataFrame.from_records(goals)
    except Exception as e:
        error_message = "Error retrieving goals over time data."
        error_details = f"Error details: {e}"
        return error_page(
            request=request,
            error_heading=error_message,
            error_text=error_details,
        )
    # At this poiunt, we know that the data is valid, so build the plot
    script, div = get_script_div_leagues_over_time(
        data=goals,
        title="Mean goals/match by season start for each league tier",
        y_axis_label="Mean goals/match",
        y_name="mean_goals",
        create_components=True,
    )

    context = {
        'title': 'Goals scored by season and league',
        'script': script,
        'div': div,
        'chart_controls': """
        The legend on the right is interactive, by clicking on the legend
        items you can turn them on and off. To the right of the legend is a
        toolbar you can use to zoom in and out of the chart, move around the
        chart, etc. Lastly, by hovering over the data points you can see the
        league, season, and mean goals for that data point.
        """,
        'description': """
        This chart shows the mean number of goals scored per game per season
        for the top five tiers of the English football league. <br/><br/>

        The light coral colored bands represent World Wars I and II. The
        league was officially suspended during the wars, though it did
        continue in a highly modified form.<br/><br/>

        Note how the mean number decreases from the start of the league to
        about 1924. This might be driven by increasing professionalism in
        the game. In 1925, the league made a change to the offside rule with
        the intent of increasing the number of goals scored. The number of
        goals did increase immediately after this change. It decreased again
        over time, perhaps as a result of tactics evolving. <br/><br/>

        The fifth tier (currently called the National League), has
        consistently a higher mean number of goals than the other tiers.
        This might be because of more unequal teams in this tier than the
        others (though see the comments on recent trends in the Premier
        League). <br/><br/>

        Since about 2009, the mean number of goals per game has been
        increasing in the Premier League but not in the other tiers. This
        might be driven by inequalities in this league; there is good
        evidence that this tier is less equal than the others.
        """.replace('\n', '').replace("<br/>", "\n")
    }
    return render(
        request=request,
        template_name='trends/chart_detail.html',
        context=context,
    )


@login_required
def home_advantage_over_time(request: HttpRequest) -> HttpResponse:
    """
    Display a Bokeh chart showing home advantage trends over time from the Football database.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        HTTP response with home advantage chart page
    """
    try:
        # Get data from the database using Django model manager
        home_win_fraction = LeagueManager().get_home_win_fraction()
        home_win_fraction = pd.DataFrame.from_records(home_win_fraction)
        home_win_goals = LeagueManager().get_home_goal_advantage()
        home_win_goals = pd.DataFrame.from_records(home_win_goals)
    except Exception as e:
        error_message = "Error retrieving home advantage data."
        error_details = f"Error details: {e}"
        return error_page(
            request=request,
            error_heading=error_message,
            error_text=error_details,
        )
    # Create separate plot components for Bootstrap tabs
    script_hwf, div_hwf = get_script_div_leagues_over_time(
        data=home_win_fraction,
        title="Home win fraction by season start for each league tier",
        y_axis_label="Home win fraction",
        y_name="home_win_fraction",
        create_components=True,
    )
    script_hwg, div_hwg = get_script_div_leagues_over_time(
        data=home_win_goals,
        title="Home goal advantage by season start for each league tier",
        y_axis_label="Home goal advantage",
        y_name="home_goal_advantage",
        create_components=True,
    )

    context = {
        'title': 'Home Advantage Analysis',
        'script_hwf': script_hwf,
        'div_hwf': div_hwf,
        'script_hwg': script_hwg,
        'div_hwg': div_hwg,
        'chart_controls': """
        There are two charts on this page, use the tabs to switch between them.
        The legend on the right is interactive, by clicking on the legend items you can turn them on and off. To the right
        of the legend is a toolbar you can use to zoom in and out of the chart, move around the chart, etc. Lastly, by hovering
        over the data points you can see the league, season, and home win fraction for that data point.
        """,
        'description': """
        The chart on the tab "Home win fraction" shows the home win fraction by season start for each league tier.
        This is teh fraction of all wins that were at home. If there were no home advantage, we would expect this
        fraction to be 0.5. <br/>
        As you can see, the win fraction has been declining steadily since the end of WWII, disappearing entirely for
        some leagues during COVID. The COVID effect suggests that spectators are part of the home club advantage. However,
        home advantage does not track the attendance charts, and the decline in home advantage has been roughly
        linear over the last fifty years whereas attenadance figures have not. I don't have a full explanation for home
        advantage. <br/><br/>

        The chart on the tab "Home win goals difference" shows the difference in goals scored by the home team and the
        away team by season start for each league tier. It quantifies home many goals home advantage is worth.  It's on
        a steady decline post WWII and may disappear entirely over the next few decades.
        """.replace('\n', '').replace("<br/>", "\n")
    }
    return render(
        request=request,
        template_name='trends/home_advantage_chart.html',
        context=context,
    )


@login_required
def draw_fraction_over_time(request: HttpRequest) -> HttpResponse:
    """
    Display a Bokeh chart showing draw fraction over time from the Football
    database.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        HTTP response with draw fraction chart page
    """
    try:
        # Get data from the database using Django model manager
        draw_fraction = LeagueManager().get_draw_fraction()
        draw_fraction = pd.DataFrame.from_records(draw_fraction)
    except Exception as e:
        error_message = "Error retrieving draw fraction data."
        error_details = f"Error details: {e}"
        return error_page(
            request=request,
            error_heading=error_message,
            error_text=error_details,
        )

    script, div = get_script_div_leagues_over_time(
        data=draw_fraction,
        title=(
            "Draw fraction by season start for each league tier"
        ),
        y_axis_label="Draw fraction",
        y_name="draw_fraction",
        create_components=True,
    )

    context = {
        'title': 'Draw Fraction Analysis',
        'script': script,
        'div': div,
        'chart_controls': (
            """
            The legend on the right is interactive. Click items to toggle.
            Use the toolbar to zoom and pan. Hover to see season, league,
            and draw fraction values.
            """
        ),
        'description': (
            """
            This chart shows the fraction of matches ending in a draw by
            season start for each league tier. The light coral colored bands represent World Wars I and II.
            The league was officially suspended during the wars, though it did continue in a highly modified form.<br/><br/>
            The draw fraction starts of low (1888-1889) and increases steadily until about 1924. In 1925, there was a change
            to the offside rule, which might have decreased the draw fraction. The draw fraction increased substantially
            for the 1968-1969 season, which coincided with a rules change to allow the use of substitutions for any reason.
            Sinnce then, the draw fraction for most leagues has been on a slight decline. The exception is the Premier League,
            where the draw fraction has seen a marked decline since the early 2000s. This might be driven by increasing
            (financial and otherwise) inequalities in the league. We'll explore this in the inequality analysis.
            """
        ).replace('\n', '').replace("<br/>", "\n"),
    }
    return render(
        request=request,
        template_name='trends/chart_detail.html',
        context=context,
    )


@login_required
def inequality_win_fraction_sd_over_time(request: HttpRequest) -> HttpResponse:
    """
    Display a Bokeh chart showing inequality (win fraction std dev) over time.

    Uses the same SQL as draw fraction for now.

    Args:
        request: HTTP request object

    Returns:
        HTTP response with inequality chart page
    """
    try:
        inequality = (
            LeagueManager().get_win_fraction_sd_over_time()
        )
        inequality = pd.DataFrame.from_records(inequality)
        inequality = inequality.sort_values(
            by=['league_tier', 'season_start']
        )
    except Exception:
        return error_page(
            request=request,
            error_heading="Error retrieving inequality data",
            error_text=(
                "Error retrieving win fraction standard deviation data from "
                "the database."
            ),
        )

    script, div = get_script_div_leagues_over_time(
        data=inequality,
        title=(
            "Inequality - win fraction standard deviation by season start "
            "for each league tier"
        ),
        y_axis_label="Win fraction std dev",
        y_name="win_fraction_sd",
        create_components=True,
    )

    context = {
        'title': 'Inequality - Win Fraction Standard Deviation',
        'script': script,
        'div': div,
        'chart_controls': (
            """
            The legend on the right is interactive. Click items to toggle.
            Use the toolbar to zoom and pan. Hover for details.
            """
        ),
        'description': (
            """
            The standard deviation of the win fraction measures the spread of win fractions across the clubs in a league
            for a season. A low win fraction standard deviation indicates the clubs are faily closely matched, a high
            standard deviation indicates the clubs are unequally matched. The trend in the win fraction standard dviation
            over time is a measure of the inequality in the league over time. <br/><br/>
            The data shows declining inquality in the earliest years of the league (1888-1889 onwards). This is as expected;
            the league was new and clubs were professionalizing. Notably the first tier became more equal with relegation
            to the second tier. <br/><br/>
            The top tier shows a marked increase in inequality after the introduction of the Premier League in the 1992-1993 season.
            A deeper analysis shows money in this league is concentrated to the top few clubs. <br/><br/>
            At the other end, tier 5, we can see an increase in win fraction standard deviation over the last few years. This
            league has also seen an influx of money to a few clubs, most famously Wrexham.
            """
        ).replace('\n', '').replace("<br/>", "\n"),
    }
    return render(
        request=request,
        template_name='trends/chart_detail.html',
        context=context,
    )


@login_required
def discipline_over_time(request: HttpRequest) -> HttpResponse:
    """
    Display a Bokeh chart showing mean red cards per match over time.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        HTTP response with discipline chart page
    """
    try:
        red_card_data = LeagueManager().get_red_card_data()
        red_card_data = pd.DataFrame.from_records(red_card_data)
        red_card_data = red_card_data[red_card_data['mean_red_cards'].notna()]
    except Exception as e:
        error_message = "Error retrieving red card data."
        error_details = f"Error details: {e}"
        return error_page(
            request=request,
            error_heading=error_message,
            error_text=error_details,
        )
    try:
        yellow_card_data = LeagueManager().get_yellow_card_data()
        yellow_card_data = pd.DataFrame.from_records(yellow_card_data)
        yellow_card_data = yellow_card_data[yellow_card_data['mean_yellow_cards'].notna(
        )]
    except Exception as e:
        error_message = "Error retrieving yellow card data."
        error_details = f"Error details: {e}"
        return error_page(
            request=request,
            error_heading=error_message,
            error_text=error_details,
        )
    try:
        foul_data = LeagueManager().get_foul_data()
        foul_data = pd.DataFrame.from_records(foul_data)
        foul_data = foul_data[foul_data['mean_fouls'].notna()]
    except Exception as e:
        error_message = "Error retrieving foul data."
        error_details = f"Error details: {e}"
        return error_page(
            request=request,
            error_heading="Error retrieving discipline data",
            error_text="Error retrieving discipline data from the database.",
        )

    # Create separate plot components for Bootstrap tabs
    script_red, div_red = get_script_div_leagues_over_time(
        data=red_card_data,
        title=(
            "Mean red cards/match by season start for each league tier"
        ),
        y_axis_label="Mean red cards/match",
        y_name="mean_red_cards",
        create_components=True,
        show_wars=False,
    )

    script_yellow, div_yellow = get_script_div_leagues_over_time(
        data=yellow_card_data,
        title=(
            "Mean yellow cards/match by season start for each league tier"
        ),
        y_axis_label="Mean yellow cards/match",
        y_name="mean_yellow_cards",
        create_components=True,
        show_wars=False,
    )

    script_foul, div_foul = get_script_div_leagues_over_time(
        data=foul_data,
        title=(
            "Mean fouls/match by season start for each league tier"
        ),
        y_axis_label="Mean fouls/match",
        y_name="mean_fouls",
        create_components=True,
        show_wars=False,
    )

    context = {
        'title': 'Discipline Over Time',
        'script_red': script_red,
        'div_red': div_red,
        'script_yellow': script_yellow,
        'div_yellow': div_yellow,
        'script_foul': script_foul,
        'div_foul': div_foul,
        'chart_controls': (
            """
            The legend on the right is interactive. Click items to toggle.
            Use the toolbar to zoom and pan. Hover for season and value.
            """
        ),
        'description': (
            """
            I don't have a full data set for disciplinary data, here's all the data I've been able to find.<br/><br/>
            The red card data shows a steady decline over time, with the National League (tier 5) showiing the highest rate. The National
            League is the lowest tier and isn't usually even considered "league football". It's possible then that the players are
            less disciplined, so are awarded more red cards. Bear in mind, players awarded a red card are sent off, reducing their
            team to 10 men, a very significant disadvantage. Clubs are therefore incentived not to get red cards.<br/><br/>
            The yellow card data is more complex and shows an uptick over the last few years and a COVID dip. It's possible the
            COVID dip is due to then absence of fans in the stadiums.  The uptick could be due to more risk taking by players or players
            "downgrading" thjeir risk behavior from red cards to yellow cards. <br/><br/>
            The foul data has been more or less constant ove the last twenty years.
            """
        ).replace('\n', '').replace("<br/>", "\n"),
    }
    return render(
        request=request,
        template_name='trends/discipline_chart.html',
        context=context,
    )


@login_required
def attendance_over_time(request: HttpRequest) -> HttpResponse:
    """
    Display a Bokeh chart showing mean attendance per match over time.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        HTTP response with attendance chart page
    """
    # Total attendance
    try:
        total_attendance = LeagueManager().get_total_attendance_data()
        total_attendance = pd.DataFrame.from_records(total_attendance)

        script_season, div_season = get_script_div_leagues_over_time(
            data=total_attendance,
            title=(
                "Total season attendance by season start for each league tier"
            ),
            y_axis_label="Total season attendance",
            y_name="total_attendance",
            create_components=True,
            show_wars=True,
        )
    except Exception as e:
        error_message = "Error retrieving total attendance data."
        error_details = f"Error details: {e}"
        return error_page(
            request=request,
            error_heading=error_message,
            error_text=error_details,
        )

    # Mean attendance
    try:
        mean_attendance = LeagueManager().get_mean_attendance_data()
        mean_attendance = pd.DataFrame.from_records(mean_attendance)

        script_mean, div_mean = get_script_div_leagues_over_time(
            data=mean_attendance,
            title=(
                "Mean attendance per match by season start for each league tier"
            ),
            y_axis_label="Mean attendance per match",
            y_name="mean_attendance",
            create_components=True,
            show_wars=True,
        )
    except Exception as e:
        error_message = "Error retrieving mean attendance data."
        error_details = f"Error details: {e}"
        return error_page(
            request=request,
            error_heading=error_message,
            error_text=error_details,
        )

    # Attendance violin
    try:
        # Get max year from mean_attendance data for violin plot
        violin_year = 2023
        attendance_violin = (
            AttendanceViolin.objects.get_attendance_violin_data(
                season_start=violin_year
            )
        )
        attendance_violin = pd.DataFrame.from_records(attendance_violin)
        # Make sure the types are right
        attendance_violin['attendance'] = (
            attendance_violin['attendance'].astype(int)
        )
        attendance_violin['probability_density'] = (
            attendance_violin['probability_density'].astype(float)
        )

        min_year, max_year = (
            AttendanceViolin.objects.get_attendance_violin_season_range()
        )

        script_violin, div_violin = get_attendance_violin_plot(
            data=attendance_violin,
            title="Attendance violin plot",
            x_axis_label="Attendance",
            x_name="attendance",
            y_axis_label="Probability density",
            y_name="probability_density",
            season_start=violin_year,
            create_components=True,
        )

    except Exception as e:
        error_message = "Error retrieving attendance violin data."
        error_details = f"Error details: {e}"
        return error_page(
            request=request,
            error_heading=error_message,
            error_text=error_details
        )

    context = {
        'title': 'Attendance Over Time',
        'script_season': script_season,
        'div_season': div_season,
        'script_mean': script_mean,
        'div_mean': div_mean,
        'script_violin': script_violin,
        'div_violin': div_violin,
        'violin_min_year': min_year,
        'violin_max_year': max_year,
        'chart_controls': (
            """
            The legend on the right is interactive. Click items to toggle.
            Use the toolbar to zoom and pan. Hover for season and value.
            """
        ),
        'description': (
            """
            The total and mean (per game) attendance figures tell the same story. <br/><br/>
            Attendance increased from the league start to about 1948 as the game became a professional sport and a
            mass spectator sport. <br/><br/>
            Unfortunately, hooliganism led to a decline in attendance and there were valid safety concerns for fans.
            There were some significant and tragicevents in the 1980s:
            the Bradford City stadium fire in 1985, the Heysel Stadium disaster in 1989, and the Hillsborough disaster in 1989.
            These events involved large scale loss of life. The English game had reached a nadir by the end of the 1980s.<br/><br/>
            Subsequently, clubs and the government worked to improve safety and the match-going experience. In more
            recent years, clubs have focused on creating a family-friendly atmosphere. The public rewarded these efforts
            with increased attendance.<br/><br/>
            The data clearly shows the COVID dip in 2020 when league games were played behind closed doors, so
            attendance was zero.<br/><br/>
            The attendance violin plots show the emergence of a league-within-a-league for the Premier League over the last few years.
            They also show attendance is not equally distributed across the leagues. The higher you go, the more people
            attend games.
            """
        ).replace('\n', '').replace("<br/>", "\n"),
    }
    return render(
        request=request,
        template_name='trends/attendance_chart.html',
        context=context,
    )


@login_required
def attendance_violin_json(
    request: HttpRequest,
) -> JsonResponse:
    """
    Return attendance violin data as JSON.

    Only visible to logged in users.

    Args:
        request: HTTP request object with optional 'season_start' query
            parameter

    Returns:
        JsonResponse: JSON response containing attendance violin data
        with fields: league_tier, attendance, and probability_density
    """
    logger = logging.getLogger(__name__)
    try:
        # Get season_start from query parameters
        season_start_param = request.GET.get('season_start')
        if not season_start_param:
            return JsonResponse(
                {
                    'error': (
                        'Missing required parameter: season_start. '
                        'Please provide season_start as a query parameter.'
                    )
                },
                status=400,
                safe=False
            )
        try:
            season_start = int(season_start_param)
        except ValueError:
            return JsonResponse(
                {
                    'error': (
                        f'Invalid season_start parameter: '
                        f'{season_start_param}. Must be an integer.'
                    )
                },
                status=400,
                safe=False
            )
        # Get data from the database using Django model manager
        attendance_violin_data = (
            AttendanceViolin.objects.get_attendance_violin_data(
                season_start=season_start
            )
        )
        # Restructure data and convert Decimal type to float if appropriate. Creating this
        # structure:
        # {'1': {'attendance': [...], 'probability_density': [...]},
        # '2': {'attendance': [...], 'probability_density': [...]},
        # '3': {'attendance': [...], 'probability_density': [...]},
        # '4': {'attendance': [...], 'probability_density': [...]},
        # '5': {'attendance': [...], 'probability_density': [...]}}
        data = {}
        for item in attendance_violin_data:
            if item['league_tier'] not in data:
                data[item['league_tier']] = {
                    'attendance': [],
                    'probability_density': []
                }
            data[item['league_tier']]['attendance'].append(
                float(item['attendance']))
            data[item['league_tier']]['probability_density'].append(
                float(item['probability_density']))
        return JsonResponse({'data': data}, safe=False)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        error_line = (
            traceback.extract_tb(exc_tb)[-1].line
            if traceback.extract_tb(exc_tb) else "N/A"
        )
        error_message = (
            f"Error retrieving attendance violin data. "
            f"Exception occurred at line {line_number}: {str(e)}. "
            f"Line content: {error_line}"
        )
        logger.error(error_message)
        return JsonResponse(
            {'error': error_message},
            status=500,
            safe=False
        )
