"""
Views for the goals app.
"""
from typing import Dict, List, Any
from django.shortcuts import render
from django.http import HttpRequest, JsonResponse
from bokeh.models.mappers import LinearColorMapper
from datetime import date
from bokeh.embed import components
from bokeh.layouts import column, row
from bokeh.transform import transform
from bokeh.palettes import Viridis256
from bokeh.plotting import figure
from bokeh.models import (Band, ColumnDataSource, HoverTool)
import numpy as np
from goals.models import FootballMatch

PLOT_HEIGHT = 400

def bokeh_score_distribution_plots(data, league_tier, season_start):
    """
    Create Bokeh plots for score distribution analysis.
    """
    max_frequency = data['frequency'].max()
    max_home_goals = data['home_goals'].max()
    max_away_goals = data['away_goals'].max()
    color_mapper = LinearColorMapper(
        palette=Viridis256,
        low=0,
        high=max_frequency
    )
    plots = []
    for league_tier in data['league_tier'].unique():
        data_subset = data[data['league_tier'] == league_tier]
        source = ColumnDataSource(data_subset, name='score_distribution_data' + '_' =str(league_tier))
        plot = figure(
            title=f'Score Distribution for League Tier {league_tier} and season starting in {season_start}',
            x_axis_label='Home Goals',
            y_axis_label='Away Goals',
            name='score_distribution_plot' + '_' + str(league_tier),
        )
        plot.rect(
            x='home_goals',
            y='away_goals',
            width=1,
            height=1,
            source=source,
            fill_color=transform('frequency', color_mapper),
            line_color='white',
            line_width=1
        )
        # Configure axis properties for better visualization
        # Set tick marks to show integer values for goals
        plot.xaxis.ticker = list(range(max_home_goals + 1))
        plot.yaxis.ticker = list(range(max_away_goals + 1))
        # Remove grid lines for cleaner appearance
        plot.xgrid.visible = False
        plot.ygrid.visible = False
        # Set axis limits with small padding for better visual spacing
        plot.x_range.start = -0.5
        plot.x_range.end = max_home_goals + 0.5
        plot.y_range.start = -0.5
        plot.y_range.end = max_away_goals + 0.5

    plots = column(row(plots[0:2], sizing_mode="stretch_width"),
                   row(plots[2:4], sizing_mode="stretch_width"))
    script, div = components(plots)
    return script, div

def bokeh_goals_plots(data, x_axis, y_axes, league_tier, season_start):
    """
    Create Bokeh plots for goals analysis.
    """
    # Calculate height for each plot (divide total height by number
    # of tiers)
    height = int(PLOT_HEIGHT / len(y_axes))
    # Convert the data (a dict) to a ColumnDataSource.
    # Note we're filtering out r2 and p-values to make the value arrays
    # the same size.
    # Note: name is used in JavaScript callback to identify the source
    # of the data for the plot
    excluded_keys = (
        [a + '_r2' for a in y_axes] +
        [a + '_pvalue' for a in y_axes]
    )
    source = ColumnDataSource(
        data={
            key: value
            for key, value in data.items()
            if key not in excluded_keys
        },
        name='goals_data',
    )
    plots = []
    for y_axis in y_axes:
        # Replace underscores with spaces in axis labels for readability
        plot = figure(
            title=(
                f"{y_axis.replace('_', ' ')} vs "
                f"{x_axis.replace('_', ' ')} for league {league_tier} "
                f"and season starting in {season_start} "
                f"R-squared: {data[y_axis + '_r2']:.2f}, "
                f"p-value: {data[y_axis + '_pvalue']:.2f}"
            ),
            # Only show x-axis label on the last plot to avoid repetition
            x_axis_label=(
                x_axis.replace('_', ' ')
                if y_axis == y_axes[-1]
                else None
            ),
            # Replace underscores with spaces in y-axis label
            y_axis_label=y_axis.replace('_', ' '),
            # Add extra height to last plot to accommodate x-axis label
            height=height + 40 if y_axis == y_axes[-1] else height,
            sizing_mode="stretch_width",
            toolbar_location="right",
            # Note: name is used in JavaScript callback to identify the plot
            # for the y-axis when updating dynamically
            name=y_axis + '_plot',
        )
        # Hide x-axis on all plots except the last one
        plot.xaxis.visible = False if y_axis != y_axes[-1] else True
        # Scatter plot of clubs
        scatter = plot.scatter(
            x=x_axis,
            y=y_axis,
            source=source,
        )
        # Line fit
        plot.line(
            x=x_axis,
            y=y_axis + '_fit',
            source=source,
            line_width=2,
            color="blue",
        )
        # Upper and lower confidence intervals
        band = Band(
            base=x_axis,
            lower=y_axis + '_fit_lower',
            upper=y_axis + '_fit_upper',
            fill_alpha=0.05,
            fill_color="blue",
            line_color="blue",
            source=source,
        )
        plot.add_layout(band)
        hover_tips = (
            [("Club", "@club_name"),
             (x_axis.replace('_', ' '), f"@{x_axis}")] +
            [
                (y_axis.replace('_', ' '), f"@{y_axis}")
                for y_axis in y_axes
            ]
        )
        plot.add_tools(HoverTool(
            tooltips=hover_tips,
            renderers=[scatter]
        ))
        plots.append(plot)
    plots = column(plots, sizing_mode="stretch_width")
    script, div = components(plots)
    return script, div


def goals_dashboard(request):
    """
    Display the goals dashboard with chart selection menu.

    Shows factors that influence goals.
    """
    context = {
        'title': 'Goal Analysis',
        'charts': [
            {
                'name': 'Money and goals',
                'url': 'goals:money_and_goals',
                'description': (
                    'See how club value affects goals scored.'
                )
            },
            {
                'name': 'Tenure and goals',
                'url': 'goals:tenure_and_goals',
                'description': (
                    'See how tenure in a league affects goals scored.'
                )
            },
            {
                'name': 'Mean age and goals',
                'url': 'goals:mean_age_and_goals',
                'description': (
                    'See how club mean age affects goals scored.'
                )
            },
            {
                'name': 'Foreigner count and goals',
                'url': 'goals:foreigner_count_and_goals',
                'description': (
                    'See how foreigner count affects goals scored.'
                )
            },
            {
                'name': 'Score distribution',
                'url': 'goals:score_distribution',
                'description': (
                    'See the distribution of scores for a given league tier and season.'
                )
            }
        ]
    }
    return render(request, 'goals/dashboard.html', context)


def money_and_goals(request):
    """
    Display a chart showing how team value affects goals scored.

    Args:
        request: HTTP request object

    Returns:
        HTTP response with money and goals chart page
    """
    # TODO: Implement money and goals analysis
    season_start: int = 2024
    league_tier: int = 1
    json_data = FootballMatch.objects.get_goals_by_money(
        season_start=season_start,
        league_tier=league_tier,
    )

    script, div = bokeh_goals_plots(
        data=json_data,
        x_axis='total_market_value',
        y_axes=['for_goals', 'against_goals', 'net_goals'],
        league_tier=1,
        season_start=2024,
    )
    context = {
        'title': 'Money and Goals',
        'script': script,
        'div': div,
        'callback': 'money_goals_json',
        'x_field': 'total_market_value',
        'chart_controls': (
            """
            The legend on the right is interactive. Click items to toggle.
            Use the toolbar to zoom and pan. Hover over points for details. <br/><br/>
            The year slider allows you to select the season start year. The
            league tier radio buttons allow you to select the league tier.
            """.replace('\n', '').replace("<br/>", "\n")
        ),
        'min_year': 2010,
        'max_year': 2024,
        'current_year': season_start,
        'description': """
        This chart shows the relationship between the tenure of clubs in a league and the 
        number of goals scored, conceded, and net goals. Tenure means the number of contguous seasons
        a club has been in a league. <br/><br/>
        The r-squared values show that although tenure is factor for goals 
        scored, it's not the only factor.The p-values show that the relationship is mostly statistically 
        significant. <br/><br/>
        """.replace('\n', '').replace("<br/>", "\n")
    }
    return render(request, 'goals/chart_detail.html', context)


def money_goals_json(
    request: HttpRequest,
    *,
    league_tier: int,
    season_start: int,
) -> JsonResponse:
    """
    Return JSON data structure for money and goals analysis. Note we do NOT 
    convert the season_start to a date object.

    Args:
        request: HTTP request object
        league_tier: Integer representing league tier
        season_start: Integer representing season start year

    Returns:
        JSON response with goals and market value data for clubs.
    """
    try:
        json_data: Dict[str, List[Any]] = (
            FootballMatch.objects.get_goals_by_money(
                season_start=season_start,
                league_tier=league_tier,
            )
        )

        return JsonResponse(json_data)

    except ValueError as e:
        return JsonResponse(
            {'error': f'Invalid parameter: {str(e)}'},
            status=400,
        )
    except Exception as e:
        return JsonResponse(
            {'error': f'Server error: {str(e)}'},
            status=500,
        )


def tenure_and_goals(request):
    """
    Display a chart showing how team tenure affects goals scored.

    Args:
        request: HTTP request object

    Returns:
        HTTP response with tenure and goals chart page
    """
    season_start: int = 2024
    league_tier: int = 1
    json_data = FootballMatch.objects.get_goals_by_tenure(
        season_start=season_start,
        league_tier=league_tier,
    )

    script, div = bokeh_goals_plots(
        data=json_data,
        x_axis='tenure',
        y_axes=['for_goals', 'against_goals', 'net_goals'],
        league_tier=1,
        season_start=2024,
    )
    context = {
        'title': 'Tenure and Goals',
        'script': script,
        'div': div,
        'callback': 'tenure_goals_json',
        'x_field': 'tenure',
        'chart_controls': (
            """
            The legend on the right is interactive. Click items to toggle.
            Use the toolbar to zoom and pan. Hover over points for details. <br/><br/>
            The year slider allows you to select the season start year. The
            league tier radio buttons allow you to select the league tier.
            """.replace('\n', '').replace("<br/>", "\n")
        ),
        'min_year': 2010,
        'max_year': 2024,
        'current_year': season_start,
        'description': """
        This chart shows the relationship between the total market value of clubs at the start of a 
        season and the number of goals scored, conceded, and net goals in the top four tiers of the 
        English football league. <br/><br/>
        The r-squared values show that although money is an important factor for goals scored, it's 
        not the only factor. The p-values show that the relationship is mostly tatistically 
        significant. <br/><br/>
        The r-squared values are higher for the Premier League (tier 1) and higher for more recent 
        seasons. It's well-known that more money is coming into the game, and we can clearly see the
        effect of money inequality in terms of goals scored.
        """.replace('\n', '').replace("<br/>", "\n")
    }
    return render(request, 'goals/chart_detail.html', context)


def tenure_goals_json(
    request: HttpRequest,
    *,
    league_tier: int,
    season_start: int,
) -> JsonResponse:
    """
    Return JSON data structure for tenure and goals analysis. Note we do NOT 
    convert the season_start to a date object.

    Args:
        request: HTTP request object
        league_tier: Integer representing league tier
        season_start: Integer representing season start year

    Returns:
        JSON response with goals and market value data for clubs.
    """
    try:
        json_data: Dict[str, List[Any]] = (
            FootballMatch.objects.get_goals_by_tenure(
                season_start=season_start,
                league_tier=league_tier,
            )
        )

        return JsonResponse(json_data)

    except ValueError as e:
        return JsonResponse(
            {'error': f'Invalid parameter: {str(e)}'},
            status=400,
        )
    except Exception as e:
        return JsonResponse(
            {'error': f'Server error: {str(e)}'},
            status=500,
        )


def mean_age_and_goals(request):
    """
    Display a chart showing how team mean age affects goals scored.

    Args:
        request: HTTP request object

    Returns:
        HTTP response with mean age and goals chart page
    """
    # TODO: Implement mean age and goals analysis
    season_start: int = 2024
    league_tier: int = 1
    json_data = FootballMatch.objects.get_goals_by_mean_age(
        season_start=season_start,
        league_tier=league_tier,
    )

    script, div = bokeh_goals_plots(
        data=json_data,
        x_axis='mean_age',
        y_axes=['for_goals', 'against_goals', 'net_goals'],
        league_tier=1,
        season_start=2024,
    )
    context = {
        'title': 'Mean Age and Goals',
        'script': script,
        'div': div,
        'callback': 'mean_age_goals_json',
        'x_field': 'mean_age',
        'chart_controls': (
            """
            The legend on the right is interactive. Click items to toggle.
            Use the toolbar to zoom and pan. Hover over points for details. <br/><br/>
            The year slider allows you to select the season start year. The
            league tier radio buttons allow you to select the league tier.
            """.replace('\n', '').replace("<br/>", "\n")
        ),
        'min_year': 2010,
        'max_year': 2024,
        'current_year': season_start,
        'description': """
        This chart shows the relationship between the mean age of clubs at the start of a 
        season and the number of goals scored, conceded, and net goals in the top four tiers of the 
        English football league. <br/><br/>
        The the curve slope and the r-squared values show club mean age only has a slight, if any, 
        effect on goals scored. The p-values show that the relationship is mostly statistically 
        insignificant. <br/><br/>
        """.replace('\n', '').replace("<br/>", "\n")
    }
    return render(request, 'goals/chart_detail.html', context)


def mean_age_goals_json(
    request: HttpRequest,
    *,
    league_tier: int,
    season_start: int,
) -> JsonResponse:
    """
    Return JSON data structure for mean age and goals analysis. Note we do NOT 
    convert the season_start to a date object.

    Args:
        request: HTTP request object
        league_tier: Integer representing league tier
        season_start: Integer representing season start year

    Returns:
        JSON response with goals and mean age data for clubs.
    """
    try:
        json_data: Dict[str, List[Any]] = (
            FootballMatch.objects.get_goals_by_mean_age(
                season_start=season_start,
                league_tier=league_tier,
            )
        )

        return JsonResponse(json_data)

    except ValueError as e:
        return JsonResponse(
            {'error': f'Invalid parameter: {str(e)}'},
            status=400,
        )
    except Exception as e:
        return JsonResponse(
            {'error': f'Server error: {str(e)}'},
            status=500,
        )


def foreigner_count_and_goals(request):
    """
    Display a chart showing how team foreigner count affects goals scored.

    Args:
        request: HTTP request object

    Returns:
        HTTP response with foreigner count and goals chart page
    """
    # TODO: Implement foreigner count and goals analysis
    season_start: int = 2024
    league_tier: int = 1
    json_data = FootballMatch.objects.get_goals_by_foreigner_count(
        season_start=season_start,
        league_tier=league_tier,
    )

    script, div = bokeh_goals_plots(
        data=json_data,
        x_axis='foreigner_count',
        y_axes=['for_goals', 'against_goals', 'net_goals'],
        league_tier=1,
        season_start=2024,
    )
    context = {
        'title': 'Foreigner Count and Goals',
        'script': script,
        'div': div,
        'callback': 'foreigner_count_goals_json',
        'x_field': 'foreigner_count',
        'chart_controls': (
            """
            The legend on the right is interactive. Click items to toggle.
            Use the toolbar to zoom and pan. Hover over points for details. <br/><br/>
            The year slider allows you to select the season start year. The
            league tier radio buttons allow you to select the league tier.
            """.replace('\n', '').replace("<br/>", "\n")
        ),
        'min_year': 2010,
        'max_year': 2024,
        'current_year': season_start,
        'description': """
        This chart shows the relationship between the foreigner count of clubs at the start of a 
        season and the number of goals scored, conceded, and net goals in the top four tiers of the 
        English football league. <br/><br/>
        The slope and the r-squared values show that foreigner count is mostly not a factor.
        The p-values show that the relationship is mostly statistically 
        insignificant. <br/><br/>
        """.replace('\n', '').replace("<br/>", "\n")
    }
    return render(request, 'goals/chart_detail.html', context)


def foreigner_count_goals_json(
    request: HttpRequest,
    *,
    league_tier: int,
    season_start: int,
) -> JsonResponse:
    """
    Return JSON data structure for foreigner count and goals analysis. Note we do NOT 
    convert the season_start to a date object.

    Args:
        request: HTTP request object
        league_tier: Integer representing league tier
        season_start: Integer representing season start year

    Returns:
        JSON response with goals and foreigner count data for clubs.
    """
    try:
        json_data: Dict[str, List[Any]] = (
            FootballMatch.objects.get_goals_by_foreigner_count(
                season_start=season_start,
                league_tier=league_tier,
            )
        )

        return JsonResponse(json_data)

    except ValueError as e:
        return JsonResponse(
            {'error': f'Invalid parameter: {str(e)}'},
            status=400,
        )
    except Exception as e:
        return JsonResponse(
            {'error': f'Server error: {str(e)}'},
            status=500,
        )

def score_distribution(request):
    """
    Display a chart showing the distribution of scores for a given league tier and season.

    Args:
        request: HTTP request object

    Returns:
        HTTP response with score distribution chart page
    """
    season_start: int = 2024
    json_data = FootballMatch.objects.get_score_distribution(
        season_start=season_start,
    )
    script, div = bokeh_score_distribution_plots(
        data=json_data,
    )
    context = {
        'title': 'Score Distribution',
        'script': script,
        'div': div,
        'callback': 'score_distribution_json',
        'x_field': 'home_goals',
        'y_field': 'frequency',
        'chart_controls': (
            """
            The legend on the right is interactive. Click items to toggle.
            Use the toolbar to zoom and pan. Hover over points for details. <br/><br/>
            The year slider allows you to select the season start year. The
            league tier radio buttons allow you to select the league tier.
            """.replace('\n', '').replace("<br/>", "\n")
        ),
        'min_year': 2010,
        'max_year': 2024,
        'current_year': season_start,
        'description': """
        This chart shows the distribution of scores for a given league tier and season.
        The x-axis shows the number of home goals and the y-axis shows the frequency of that score.
        The frequency is the number of times a score occurred divided by the total number of matches.
        """.replace('\n', '').replace("<br/>", "\n")
    }
    return render(request, 'goals/chart_score_distribution.html', context)

def score_distribution_json(request, *, season_start:int):
    """
    Display a chart showing the distribution of scores for a given league tier and season.

    Args:
        request: HTTP request object

    Returns:
        HTTP response with score distribution chart page
    """
    json_data = FootballMatch.objects.get_score_distribution(
        season_start=season_start
    )
    return JsonResponse(json_data)