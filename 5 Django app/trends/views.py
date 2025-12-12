"""
Views for the trends app.
"""
import json
import logging
import sys
import traceback
from decimal import Decimal
from typing import Tuple, Union

import numpy as np
import pandas as pd
from bokeh.embed import components
from bokeh.layouts import column
from bokeh.models import (
    ColumnDataSource,
    HoverTool,
    Legend,
    LegendItem,
)
from bokeh.models.annotations import BoxAnnotation
from bokeh.palettes import Category10
from bokeh.plotting import figure
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse

from .models import AttendanceViolin, LeagueManager

PLOT_HEIGHT = 400

# Helper functions

@login_required
def attendance_over_time_mean_json(
    request: HttpRequest,
) -> JsonResponse:
    """
    Return mean attendance per league per season data as JSON.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        JsonResponse: JSON response containing mean attendance data
        with fields: league_tier, season_start, and mean_attendance
    """
    logger = logging.getLogger(__name__)
    try:
        # Get data from the database using Django model manager
        mean_attendance_data = LeagueManager().get_mean_attendance_data()

        # Convert QuerySet to dict structure and convert Decimal to float
        # for JSON serialization
        data = {
            'league_tier': [],
            'season_start': [],
            'mean_attendance': []
        }
        for item in mean_attendance_data:
            # Skip rows with no mean attendance
            if item['mean_attendance'] is None:
                continue
            data['league_tier'].append(item['league_tier'])
            data['season_start'].append(int(item['season_start']))
            data['mean_attendance'].append(float(item['mean_attendance']))

        return JsonResponse({'data': data}, safe=False)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        error_line = (
            traceback.extract_tb(exc_tb)[-1].line
            if traceback.extract_tb(exc_tb) else "N/A"
        )
        error_message = (
            f"Error retrieving mean attendance data. "
            f"Exception occurred at line {line_number}: "
            f"{str(e)}. Line content: {error_line}"
        )
        logger.error(error_message)
        return JsonResponse(
            {'error': error_message},
            status=500,
            safe=False
        )

@login_required
def attendance_over_time_total_json(
    request: HttpRequest,
) -> JsonResponse:
    """
    Return total attendance per league per season data as JSON.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        JsonResponse: JSON response containing total attendance data
        with fields: league_tier, season_start, and total_attendance
    """
    logger = logging.getLogger(__name__)
    try:
        # Get data from the database using Django model manager
        total_attendance_data = LeagueManager().get_total_attendance_data()

        # Convert QuerySet to dict structure and convert Decimal to float
        # for JSON serialization
        data = {
            'league_tier': [],
            'season_start': [],
            'total_attendance': []
        }
        for item in total_attendance_data:
            # Skip rows with no total attendance
            if item['total_attendance'] is None:
                continue
            data['league_tier'].append(item['league_tier'])
            data['season_start'].append(int(item['season_start']))
            data['total_attendance'].append(float(item['total_attendance']))

        return JsonResponse({'data': data}, safe=False)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        error_line = (
            traceback.extract_tb(exc_tb)[-1].line
            if traceback.extract_tb(exc_tb) else "N/A"
        )
        error_message = (
            f"Error retrieving total attendance data. "
            f"Exception occurred at line {line_number}: "
            f"{str(e)}. Line content: {error_line}"
        )
        logger.error(error_message)
        return JsonResponse(
            {'error': error_message},
            status=500,
            safe=False
        )

@login_required
def attendance_over_time(
    request: HttpRequest,
) -> HttpResponse:
    """
    Display a Bokeh chart showing attendance trends over time from the
    Football database.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        HTTP response with attendance chart page (v2)
    """
    try:
        # Set default year for violin plot (hardcoded to 2023)
        violin_year = 2023
        # Get the available season range for the violin plot selector
        min_year, max_year = (
            AttendanceViolin.objects.get_attendance_violin_season_range()
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
        'league_tiers': json.dumps([1, 2, 3, 4, 5]),
        'league_tier_colors': json.dumps(
            ["#1f77b4", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
        ),
        'chart_div_id_total': 'chart_div_id_total',
        'chart_div_id_mean': 'chart_div_id_mean',
        'chart_div_id_violin': 'chart_div_id_violin',
        'title_total': (
            'Total season attendance by season start for each league tier'
        ),
        'title_mean': (
            'Mean attendance per match by season start for each league tier'
        ),
        'title_violin': 'Attendance violin plot',
        'x_axis_title_total': 'season_start',
        'x_axis_title_mean': 'season_start',
        'x_axis_title_violin': 'attendance',
        'y_axis_title_total': 'total_attendance',
        'y_axis_title_mean': 'mean_attendance',
        'y_axis_title_violin': 'probability_density',
        'callback_url_total': reverse(
            'trends:attendance_over_time_total_json'
        ),
        'callback_url_mean': reverse(
            'trends:attendance_over_time_mean_json'
        ),

        'callback_url_violin': reverse(
            'trends:attendance_violin_json'
        ),
        'show_wars': 'true',
        'violin_year': violin_year,
        'violin_min_year': min_year,
        'violin_max_year': max_year,
        'chart_controls': """
        The legend on the right is interactive. Click items to toggle.
        Use the toolbar to zoom and pan. Hover for season and value.
        """,
        'description': """
        The total and mean (per game) attendance figures tell the same
        story. <br/><br/>
        Attendance increased from the league start to about 1948 as the
        game became a professional sport and a mass spectator sport.
        <br/><br/>
        Unfortunately, hooliganism led to a decline in attendance and
        there were valid safety concerns for fans.
        There were some significant and tragicevents in the 1980s:
        the Bradford City stadium fire in 1985, the Heysel Stadium
        disaster in 1989, and the Hillsborough disaster in 1989.
        These events involved large scale loss of life. The English game
        had reached a nadir by the end of the 1980s.<br/><br/>
        Subsequently, clubs and the government worked to improve safety
        and the match-going experience. In more recent years, clubs have
        focused on creating a family-friendly atmosphere. The public
        rewarded these efforts with increased attendance.<br/><br/>
        The data clearly shows the COVID dip in 2020 when league games
        were played behind closed doors, so attendance was zero.
        <br/><br/>
        The attendance violin plots show the emergence of a
        league-within-a-league for the Premier League over the last few
        years. They also show attendance is not equally distributed
        across the leagues. The higher you go, the more people attend
        games.
        """.replace('\n', '').replace("<br/>", "\n"),
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
        # Restructure data from flat list to nested dict by league_tier
        # and convert Decimal types to float for JSON serialization.
        # Final structure:
        # {'1': {'attendance': [...], 'probability_density': [...]},
        #  '2': {'attendance': [...], 'probability_density': [...]},
        #  '3': {'attendance': [...], 'probability_density': [...]},
        #  '4': {'attendance': [...], 'probability_density': [...]},
        #  '5': {'attendance': [...], 'probability_density': [...]}}
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

@login_required
def discipline_over_time_fouls_json(
    request: HttpRequest,
) -> JsonResponse:
    """
    Return mean fouls per league per season data as JSON.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        JsonResponse: JSON response containing mean fouls data with fields:
        league_tier, season_start, and mean_fouls
    """
    logger = logging.getLogger(__name__)
    try:
        # Get data from the database using Django model manager
        foul_data = LeagueManager().get_foul_data()

        # Convert QuerySet to dict structure and convert Decimal to float
        # for JSON serialization
        data = {
            'league_tier': [],
            'season_start': [],
            'mean_fouls': []
        }
        for item in foul_data:
            # Filter out rows with missing values
            if item['mean_fouls'] is not None:
                data['league_tier'].append(item['league_tier'])
                data['season_start'].append(int(item['season_start']))
                data['mean_fouls'].append(float(item['mean_fouls']))

        return JsonResponse({'data': data}, safe=False)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        error_line = (
            traceback.extract_tb(exc_tb)[-1].line
            if traceback.extract_tb(exc_tb) else "N/A"
        )
        error_message = (
            f"Error retrieving mean fouls data. "
            f"Exception occurred at line {line_number}: {str(e)}. "
            f"Line content: {error_line}"
        )
        logger.error(error_message)
        return JsonResponse(
            {'error': error_message},
            status=500,
            safe=False
        )

@login_required
def discipline_over_time_red_cards_json(
    request: HttpRequest,
) -> JsonResponse:
    """
    Return mean red cards per league per season data as JSON.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        JsonResponse: JSON response containing mean red cards data with fields:
        league_tier, season_start, and mean_red_cards
    """
    logger = logging.getLogger(__name__)
    try:
        # Get data from the database using Django model manager
        red_card_data = LeagueManager().get_red_card_data()

        # Convert QuerySet to dict structure and convert Decimal to float
        # for JSON serialization
        data = {
            'league_tier': [],
            'season_start': [],
            'mean_red_cards': []
        }
        for item in red_card_data:
            # Filter out rows with missing values
            if item['mean_red_cards'] is not None:
                data['league_tier'].append(item['league_tier'])
                data['season_start'].append(int(item['season_start']))
                data['mean_red_cards'].append(float(item['mean_red_cards']))

        return JsonResponse({'data': data}, safe=False)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        error_line = (
            traceback.extract_tb(exc_tb)[-1].line
            if traceback.extract_tb(exc_tb) else "N/A"
        )
        error_message = (
            f"Error retrieving mean red cards data. "
            f"Exception occurred at line {line_number}: {str(e)}. "
            f"Line content: {error_line}"
        )
        logger.error(error_message)
        return JsonResponse(
            {'error': error_message},
            status=500,
            safe=False
        )

@login_required
def discipline_over_time(request: HttpRequest) -> HttpResponse:
    """
    Display a Bokeh chart showing discipline trends over time from the
    Football database.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        HTTP response with discipline chart page (v2)
    """
    context = {
        'title': 'Discipline Over Time',
        'league_tiers': json.dumps([1, 2, 3, 4, 5]),
        'league_tier_colors': json.dumps(
            ["#1f77b4", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
        ),
        'chart_div_id_red': 'chart_div_id_red',
        'chart_div_id_yellow': 'chart_div_id_yellow',
        'chart_div_id_foul': 'chart_div_id_foul',
        'title_red': (
            'Mean red cards/match by season start for each league tier'
        ),
        'title_yellow': (
            'Mean yellow cards/match by season start for each league tier'
        ),
        'title_foul': (
            'Mean fouls/match by season start for each league tier'
        ),
        'x_axis_title_red': 'season_start',
        'x_axis_title_yellow': 'season_start',
        'x_axis_title_foul': 'season_start',
        'y_axis_title_red': 'mean_red_cards',
        'y_axis_title_yellow': 'mean_yellow_cards',
        'y_axis_title_foul': 'mean_fouls',
        'callback_url_red': reverse(
            'trends:discipline_over_time_red_cards_json'
        ),
        'callback_url_yellow': reverse(
            'trends:discipline_over_time_yellow_cards_json'
        ),
        'callback_url_foul': reverse(
            'trends:discipline_over_time_fouls_json'
        ),
        'show_wars': 'false',
        'chart_controls': """
        There are three charts on this page, use the tabs to switch between
        them. The legend on the right is interactive. Click items to toggle.
        Use the toolbar to zoom and pan. Hover for season and value.
        """,
        'description': """
        I don't have a full data set for disciplinary data, here's all
        the data I've been able to find.<br/><br/>
        The red card data shows a steady decline over time, with the
        National League (tier 5) showiing the highest rate. The National
        League is the lowest tier and isn't usually even considered
        "league football". It's possible then that the players are less
        disciplined, so are awarded more red cards. Bear in mind, players
        awarded a red card are sent off, reducing their team to 10 men,
        a very significant disadvantage. Clubs are therefore incentived
        not to get red cards.<br/><br/>
        The yellow card data is more complex and shows an uptick over the
        last few years and a COVID dip. It's possible the COVID dip is
        due to then absence of fans in the stadiums.  The uptick could
        be due to more risk taking by players or players "downgrading"
        thjeir risk behavior from red cards to yellow cards. <br/><br/>
        The foul data has been more or less constant ove the last twenty
        years.
        """.replace('\n', '').replace("<br/>", "\n"),
    }
    return render(
        request=request,
        template_name='trends/discipline_chart.html',
        context=context,
    )

@login_required
def discipline_over_time_yellow_cards_json(
    request: HttpRequest,
) -> JsonResponse:
    """
    Return mean yellow cards per league per season data as JSON.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        JsonResponse: JSON response containing mean yellow cards data with
        fields: league_tier, season_start, and mean_yellow_cards
    """
    logger = logging.getLogger(__name__)
    try:
        # Get data from the database using Django model manager
        yellow_card_data = LeagueManager().get_yellow_card_data()

        # Convert QuerySet to dict structure and convert Decimal to float
        # for JSON serialization
        data = {
            'league_tier': [],
            'season_start': [],
            'mean_yellow_cards': []
        }
        for item in yellow_card_data:
            # Filter out rows with missing values
            if item['mean_yellow_cards'] is not None:
                data['league_tier'].append(item['league_tier'])
                data['season_start'].append(int(item['season_start']))
                data['mean_yellow_cards'].append(
                    float(item['mean_yellow_cards'])
                )

        return JsonResponse({'data': data}, safe=False)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        error_line = (
            traceback.extract_tb(exc_tb)[-1].line
            if traceback.extract_tb(exc_tb) else "N/A"
        )
        error_message = (
            f"Error retrieving mean yellow cards data. "
            f"Exception occurred at line {line_number}: {str(e)}. "
            f"Line content: {error_line}"
        )
        logger.error(error_message)
        return JsonResponse(
            {'error': error_message},
            status=500,
            safe=False
        )

@login_required
def draw_fraction_over_time_json(
    request: HttpRequest,
) -> JsonResponse:
    """
    Return draw fraction per league per season data as JSON.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        JsonResponse: JSON response containing draw fraction data with fields:
        league_tier, season_start, and draw_fraction
    """
    logger = logging.getLogger(__name__)
    try:
        # Get data from the database using Django model manager
        draw_fraction_data = LeagueManager().get_draw_fraction()

        # Convert QuerySet to dict structure and convert Decimal to float
        # for JSON serialization
        data = {
            'league_tier': [],
            'season_start': [],
            'draw_fraction': []
        }
        for item in draw_fraction_data:
            data['league_tier'].append(item['league_tier'])
            data['season_start'].append(int(item['season_start']))
            data['draw_fraction'].append(float(item['draw_fraction']))

        return JsonResponse({'data': data}, safe=False)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        error_line = (
            traceback.extract_tb(exc_tb)[-1].line
            if traceback.extract_tb(exc_tb) else "N/A"
        )
        error_message = (
            f"Error retrieving draw fraction data. "
            f"Exception occurred at line {line_number}: {str(e)}. "
            f"Line content: {error_line}"
        )
        logger.error(error_message)
        return JsonResponse(
            {'error': error_message},
            status=500,
            safe=False
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
        HTTP response with draw fraction chart page (v2)
    """
    context = {
        'chart_div_id': 'chart_div_id_1',
        'title': (
            'Draw fraction by season start for each league tier'
        ),
        'league_tiers': json.dumps([1, 2, 3, 4, 5]),
        'league_tier_colors': json.dumps(
            ["#1f77b4", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
        ),
        'x_axis_title': 'season_start',
        'y_axis_title': 'draw_fraction',
        'callback_url': reverse('trends:draw_fraction_over_time_json'),
        'show_wars': 'true',
        'chart_controls': """
        The legend on the right is interactive. Click items to toggle.
        Use the toolbar to zoom and pan. Hover to see season, league,
        and draw fraction values.
        """,
        'description': """
        This chart shows the fraction of matches ending in a draw by
        season start for each league tier. The light coral colored bands
        represent World Wars I and II. The league was officially
        suspended during the wars, though it did continue in a highly
        modified form.<br/><br/>
        The draw fraction starts of low (1888-1889) and increases
        steadily until about 1924. In 1925, there was a change to the
        offside rule, which might have decreased the draw fraction. The
        draw fraction increased substantially for the 1968-1969 season,
        which coincided with a rules change to allow the use of
        substitutions for any reason. Sinnce then, the draw fraction for
        most leagues has been on a slight decline. The exception is the
        Premier League, where the draw fraction has seen a marked decline
        since the early 2000s. This might be driven by increasing
        (financial and otherwise) inequalities in the league. We'll
        explore this in the inequality analysis.
        """.replace('\n', '').replace("<br/>", "\n"),
    }
    return render(
        request=request,
        template_name='trends/chart_detail.html',
        context=context,
    )

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
def goals_over_time_json(
    request: HttpRequest,
) -> JsonResponse:
    """
    Return mean goals per league per season data as JSON.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        JsonResponse: JSON response containing mean goals data with fields:
        league_tier, season_start, and mean_goals
    """
    logger = logging.getLogger(__name__)
    try:
        # Get data from the database using Django model manager
        goals_data = LeagueManager().get_mean_goals_per_league_per_season()

        # Convert QuerySet to dict structure and convert Decimal to float
        # for JSON serialization
        data = {'league_tier': [], 'season_start': [], 'mean_goals': []}
        for item in goals_data:
            data['league_tier'].append(item['league_tier'])
            data['season_start'].append(int(item['season_start']))
            data['mean_goals'].append(float(item['mean_goals']))

        return JsonResponse({'data': data}, safe=False)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        error_line = (
            traceback.extract_tb(exc_tb)[-1].line
            if traceback.extract_tb(exc_tb) else "N/A"
        )
        error_message = (
            f"Error retrieving mean goals data. "
            f"Exception occurred at line {line_number}: {str(e)}. "
            f"Line content: {error_line}"
        )
        logger.error(error_message)
        return JsonResponse(
            {'error': error_message},
            status=500,
            safe=False
        )

@login_required
def goals_over_time(request: HttpRequest) -> HttpResponse:
    """
    Display a Bokeh chart showing goals over time from the Football database.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        HTTP response with goals over time chart page (v2)
    """
    context = {
        'chart_div_id': 'chart_div_id_1',
        'title': (
            'Mean goals scored per match by season and league tier'
        ),
        'league_tiers': json.dumps([1, 2, 3, 4, 5]),
        'league_tier_colors': json.dumps(
            ["#1f77b4", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
        ),
        'x_axis_title': 'season_start',
        'y_axis_title': 'mean_goals',
        'callback_url': reverse('trends:goals_over_time_json'),
        'show_wars': 'true',
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
def home_advantage_over_time_hwf_json(
    request: HttpRequest,
) -> JsonResponse:
    """
    Return home goal advantage per league per season data as JSON.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        JsonResponse: JSON response containing mean goals data with fields:
        league_tier, season_start, and mean_goals
    """
    logger = logging.getLogger(__name__)
    try:
        # Get data from the database using Django model manager
        hwf_data = LeagueManager().get_home_win_fraction()

        # Convert QuerySet to dict structure and convert Decimal to float
        # for JSON serialization
        data = {
            'league_tier': [],
            'season_start': [],
            'home_win_fraction': []
        }
        for item in hwf_data:
            data['league_tier'].append(item['league_tier'])
            data['season_start'].append(int(item['season_start']))
            data['home_win_fraction'].append(
                float(item['home_win_fraction'])
            )

        return JsonResponse({'data': data}, safe=False)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        error_line = (
            traceback.extract_tb(exc_tb)[-1].line
            if traceback.extract_tb(exc_tb) else "N/A"
        )
        error_message = (
            f"Error retrieving home goal advantage data. "
            f"Exception occurred at line {line_number}: {str(e)}. "
            f"Line content: {error_line}"
        )
        logger.error(error_message)
        return JsonResponse(
            {'error': error_message},
            status=500,
            safe=False
        )

@login_required
def home_advantage_over_time_hwgd_json(
    request: HttpRequest,
) -> JsonResponse:
    """
    Return home goal advantage per league per season data as JSON.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        JsonResponse: JSON response containing mean goals data with fields:
        league_tier, season_start, and mean_goals
    """
    logger = logging.getLogger(__name__)
    try:
        # Get data from the database using Django model manager
        hwgd_data = LeagueManager().get_home_goal_advantage()

        # Convert QuerySet to dict structure and convert Decimal to float
        # for JSON serialization
        data = {
            'league_tier': [],
            'season_start': [],
            'home_goal_advantage': []
        }
        for item in hwgd_data:
            data['league_tier'].append(item['league_tier'])
            data['season_start'].append(int(item['season_start']))
            data['home_goal_advantage'].append(
                float(item['home_goal_advantage'])
            )

        return JsonResponse({'data': data}, safe=False)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        error_line = (
            traceback.extract_tb(exc_tb)[-1].line
            if traceback.extract_tb(exc_tb) else "N/A"
        )
        error_message = (
            f"Error retrieving home goal advantage data. "
            f"Exception occurred at line {line_number}: {str(e)}. "
            f"Line content: {error_line}"
        )
        logger.error(error_message)
        return JsonResponse(
            {'error': error_message},
            status=500,
            safe=False
        )

@login_required
def home_advantage_over_time(request: HttpRequest) -> HttpResponse:
    """
    Display a Bokeh chart showing home advantage trends over time from the
    Football database.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        HTTP response with home advantage chart page (v2)
    """
    context = {
        'league_tiers': json.dumps([1, 2, 3, 4, 5]),
        'league_tier_colors': json.dumps(
            ["#1f77b4", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
        ),
        'chart_div_id_hwf': 'chart_div_id_hwf',
        'chart_div_id_hwgd': 'chart_div_id_hwgd',
        'title_hwf': (
            'Home win fraction by season start for each league tier'
        ),
        'title_hwgd': (
            'Home goal advantage by season start for each league tier'
        ),
        'x_axis_title_hwf': 'season_start',
        'x_axis_title_hwgd': 'season_start',
        'y_axis_title_hwf': 'home_win_fraction',
        'y_axis_title_hwgd': 'home_goal_advantage',
        'callback_url_hwf': reverse(
            'trends:home_advantage_over_time_hwf_json'
        ),
        'callback_url_hwgd': reverse(
            'trends:home_advantage_over_time_hwgd_json'
        ),
        'show_wars': 'true',
        'chart_controls': """
        There are two charts on this page, use the tabs to switch between
        them. The legend on the right is interactive, by clicking on the
        legend items you can turn them on and off. To the right of the legend
        is a toolbar you can use to zoom in and out of the chart, move around
        the chart, etc. Lastly, by hovering over the data points you can see
        the league, season, and home win fraction for that data point.
        """,
        'description': """
        The chart on the tab "Home win fraction" shows the home win fraction
        by season start for each league tier. This is the fraction of all
        wins that were at home. If there were no home advantage, we would
        expect this fraction to be 0.5. <br/>
        As you can see, the win fraction has been declining steadily since
        the end of WWII, disappearing entirely for some leagues during COVID.
        The COVID effect suggests that spectators are part of the home club
        advantage. However, home advantage does not track the attendance
        charts, and the decline in home advantage has been roughly linear
        over the last fifty years whereas attenadance figures have not. I
        don't have a full explanation for home advantage. <br/><br/>

        The chart on the tab "Home win goals difference" shows the difference
        in goals scored by the home team and the away team by season start
        for each league tier. It quantifies home many goals home advantage
        is worth.  It's on a steady decline post WWII and may disappear
        entirely over the next few decades.
        """.replace('\n', '').replace("<br/>", "\n")
    }
    return render(
        request=request,
        template_name='trends/home_advantage_chart.html',
        context=context,
    )


@login_required
def inequality_win_fraction_sd_over_time_json(
    request: HttpRequest,
) -> JsonResponse:
    """
    Return win fraction standard deviation per league per season data as JSON.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        JsonResponse: JSON response containing win fraction standard deviation
        data with fields: league_tier, season_start, and win_fraction_sd
    """
    logger = logging.getLogger(__name__)
    try:
        # Get data from the database using Django model manager
        inequality_data = LeagueManager().get_win_fraction_sd_over_time()

        # Convert QuerySet to dict structure and convert Decimal to float
        # for JSON serialization
        data = {
            'league_tier': [],
            'season_start': [],
            'win_fraction_sd': []
        }
        for item in inequality_data:
            data['league_tier'].append(item['league_tier'])
            data['season_start'].append(int(item['season_start']))
            data['win_fraction_sd'].append(float(item['win_fraction_sd']))

        return JsonResponse({'data': data}, safe=False)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        line_number = exc_tb.tb_lineno
        error_line = (
            traceback.extract_tb(exc_tb)[-1].line
            if traceback.extract_tb(exc_tb) else "N/A"
        )
        error_message = (
            f"Error retrieving win fraction standard deviation data. "
            f"Exception occurred at line {line_number}: {str(e)}. "
            f"Line content: {error_line}"
        )
        logger.error(error_message)
        return JsonResponse(
            {'error': error_message},
            status=500,
            safe=False
        )

@login_required
def inequality_win_fraction_sd_over_time(
    request: HttpRequest,
) -> HttpResponse:
    """
    Display a Bokeh chart showing inequality (win fraction std dev) over time
    from the Football database.

    Only visible to logged in users.

    Args:
        request: HTTP request object

    Returns:
        HTTP response with inequality chart page (v2)
    """
    context = {
        'chart_div_id': 'chart_div_id_1',
        'title': (
            'Inequality - win fraction standard deviation by season start '
            'for each league tier'
        ),
        'league_tiers': json.dumps([1, 2, 3, 4, 5]),
        'league_tier_colors': json.dumps(
            ["#1f77b4", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
        ),
        'x_axis_title': 'season_start',
        'y_axis_title': 'win_fraction_sd',
        'callback_url': reverse(
            'trends:inequality_win_fraction_sd_over_time_json'
        ),
        'show_wars': 'true',
        'chart_controls': """
        The legend on the right is interactive. Click items to toggle.
        Use the toolbar to zoom and pan. Hover for details.
        """,
        'description': """
        The standard deviation of the win fraction measures the spread of
        win fractions across the clubs in a league for a season. A low
        win fraction standard deviation indicates the clubs are faily
        closely matched, a high standard deviation indicates the clubs are
        unequally matched. The trend in the win fraction standard dviation
        over time is a measure of the inequality in the league over time.
        <br/><br/>
        The data shows declining inquality in the earliest years of the
        league (1888-1889 onwards). This is as expected; the league was
        new and clubs were professionalizing. Notably the first tier became
        more equal with relegation to the second tier. <br/><br/>
        The top tier shows a marked increase in inequality after the
        introduction of the Premier League in the 1992-1993 season. A
        deeper analysis shows money in this league is concentrated to the
        top few clubs. <br/><br/>
        At the other end, tier 5, we can see an increase in win fraction
        standard deviation over the last few years. This league has also
        seen an influx of money to a few clubs, most famously Wrexham.
        """.replace('\n', '').replace("<br/>", "\n"),
    }
    return render(
        request=request,
        template_name='trends/chart_detail.html',
        context=context,
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
                    'Mean red cards, yellow cards, and fouls per match by '
                    'season and league tier'
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
