"""
Views for the goals app.
"""
from django.shortcuts import render
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
import numpy as np


def goals_dashboard(request):
    """
    Display the goals dashboard with chart selection menu.

    Shows factors that influence goals.
    """
    context = {
        'title': 'Goal Analysis',
        'charts': [
            {
                'name': 'Goal Timing Analysis',
                'url': 'goals:goal_timing',
                'description': 'Analyze when goals are most likely to be scored'
            },
            {
                'name': 'Player Impact',
                'url': 'goals:player_impact',
                'description': 'Examine individual player contributions to goals'
            }
        ]
    }
    return render(request, 'goals/dashboard.html', context)


def goal_timing(request):
    """
    Display a dummy Bokeh chart showing goal timing analysis.

    Shows factors that influence when goals are scored.
    """
    # Create dummy data for demonstration
    time_intervals = ['0-15', '15-30', '30-45', '45-60', '60-75', '75-90']
    goals_scored = [45, 52, 68, 55, 78, 89]
    home_goals = [28, 32, 42, 33, 45, 52]
    away_goals = [17, 20, 26, 22, 33, 37]

    # Create Bokeh figure
    plot = figure(
        title="Goal Timing Analysis - When Goals Are Scored",
        x_axis_label="Time Interval (minutes)",
        y_axis_label="Number of Goals",
        width=800,
        height=500,
        toolbar_location="right",
        x_range=time_intervals
    )

    # Create data source
    source = ColumnDataSource(data=dict(
        intervals=time_intervals,
        total=goals_scored,
        home=home_goals,
        away=away_goals
    ))

    # Add bar chart
    plot.vbar(x='intervals', top='total', width=0.6, color="#2E8B57",
              alpha=0.8, source=source, legend_label="Total Goals")

    # Add line for home goals
    plot.line(time_intervals, home_goals, line_width=3, color="#90EE90",
              line_dash="solid", legend_label="Home Goals")

    # Add line for away goals
    plot.line(time_intervals, away_goals, line_width=3, color="#98FB98",
              line_dash="dashed", legend_label="Away Goals")

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Time", "@intervals"),
        ("Total Goals", "@total"),
        ("Home Goals", "@home"),
        ("Away Goals", "@away")
    ])
    plot.add_tools(hover)

    # Style the plot
    plot.legend.location = "top_left"
    plot.legend.click_policy = "hide"
    plot.xaxis.major_label_orientation = 0

    # Embed the plot
    script, div = components(plot)

    context = {
        'title': 'Goal Timing Analysis',
        'script': script,
        'div': div,
        'description': """
        This analysis reveals the temporal patterns of goal scoring in the 
        English Premier League. The data shows clear trends in when goals 
        are most likely to be scored during a match.
        
        Key findings:
        - Goals increase significantly in the final 15 minutes (75-90 min)
        - The first half shows a gradual increase in goal frequency
        - Home teams consistently score more goals than away teams
        - The 30-45 minute period shows the highest first-half goal rate
        - Late goals (75-90 min) are the most common, likely due to:
          * Fatigue affecting defensive concentration
          * Teams pushing for equalizers or winners
          * Substitutions changing the game dynamics
        """
    }
    return render(request, 'goals/chart_detail.html', context)


def player_impact(request):
    """
    Display a dummy Bokeh chart showing player impact on goals.

    Shows factors that influence individual player contributions.
    """
    # Create dummy data for demonstration
    players = ['Haaland', 'Kane', 'Salah', 'Rashford', 'Odegaard',
               'De Bruyne', 'Saka', 'Toney', 'Wilson', 'Mitrovic']
    goals = [36, 30, 19, 17, 15, 7, 14, 20, 18, 14]
    assists = [5, 3, 12, 5, 8, 16, 11, 4, 1, 2]
    minutes = [2853, 3080, 2610, 2400, 2800, 2200, 2500, 2700, 2000, 1800]

    # Calculate goals per 90 minutes
    goals_per_90 = [g * 90 / m for g, m in zip(goals, minutes)]

    # Create Bokeh figure
    plot = figure(
        title="Player Impact on Goals - Goals vs Assists",
        x_axis_label="Goals",
        y_axis_label="Assists",
        width=800,
        height=500,
        toolbar_location="right"
    )

    # Create data source
    source = ColumnDataSource(data=dict(
        x=goals,
        y=assists,
        players=players,
        goals_per_90=goals_per_90,
        minutes=minutes
    ))

    # Add scatter plot with size based on goals per 90
    plot.scatter('x', 'y', size=[g*3 for g in goals_per_90],
                 color="#2E8B57", alpha=0.7, source=source)

    # Add player labels
    from bokeh.models import LabelSet
    labels = LabelSet(x='x', y='y', text='players', source=source,
                      text_font_size='8pt', text_color='black',
                      x_offset=5, y_offset=5)
    plot.add_layout(labels)

    # Add hover tool
    hover = HoverTool(tooltips=[
        ("Player", "@players"),
        ("Goals", "@x"),
        ("Assists", "@y"),
        ("Goals per 90 min", "@goals_per_90{0.2f}"),
        ("Minutes Played", "@minutes")
    ])
    plot.add_tools(hover)

    # Style the plot
    plot.xaxis.axis_line_color = "#2E8B57"
    plot.yaxis.axis_line_color = "#2E8B57"
    plot.xaxis.major_tick_line_color = "#2E8B57"
    plot.yaxis.major_tick_line_color = "#2E8B57"

    # Embed the plot
    script, div = components(plot)

    context = {
        'title': 'Player Impact Analysis',
        'script': script,
        'div': div,
        'description': """
        This scatter plot analyzes individual player contributions to goals, 
        plotting goals scored against assists provided. The size of each 
        point represents the player's goals per 90 minutes ratio.
        
        Key insights:
        - Players in the top-right quadrant are the most complete attackers
        - Large points indicate high efficiency (goals per 90 minutes)
        - Pure strikers cluster in the top-left (high goals, low assists)
        - Creative midfielders cluster in the bottom-right (low goals, high assists)
        - The most valuable players balance both goals and assists
        
        Factors influencing player impact:
        - Playing position and role in the team
        - Minutes played and fitness levels
        - Team tactics and formation
        - Opposition strength and game context
        - Individual skill and form
        """
    }
    return render(request, 'goals/chart_detail.html', context)
