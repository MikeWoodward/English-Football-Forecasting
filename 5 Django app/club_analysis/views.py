"""
Views for the club analysis app.
"""
import json
import os
import re
from typing import Dict, List, Any, Optional

from bokeh.embed import components
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure
from django.db.models import Q, F, IntegerField
from django.db.models.functions import Substr, Cast
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from google import genai
# Import the specific APIError from the SDK
from google.genai.errors import APIError
from goals.models import (
    ClubHistory,
    ClubSeason,
    FootballMatch,
    League,
)
from pydantic import BaseModel


def club_analysis(request: HttpRequest):
    """
    Landing page for club analysis with dropdown menu.
    """
    return render(request, 'club_analysis/club_analysis.html')


def club_league_performance(request: HttpRequest):
    """
    Main view for club league performance page.
    Handles initial page load and club selection.
    """
    # Get all unique club names from club_history, sorted alphabetically
    clubs = (
        ClubHistory.objects
        .values_list('club_name', flat=True)
        .distinct()
        .order_by('club_name')
    )
    
    selected_club: Optional[str] = request.GET.get('club')
    
    context: Dict[str, Any] = {
        'clubs': clubs,
        'selected_club': selected_club,
    }
    
    if selected_club:
        # Get the modern_name for the selected club
        modern_name_record = (
            ClubHistory.objects
            .filter(club_name=selected_club)
            .first()
        )
        
        if modern_name_record:
            modern_name = modern_name_record.modern_name
            
            # Get all club names that share the same modern_name
            all_club_names = (
                ClubHistory.objects
                .filter(modern_name=modern_name)
                .values_list('club_name', flat=True)
                .distinct()
            )
            
            # Get club history data
            club_history_data = get_club_history_data(
                selected_club,
                modern_name
            )
            
            # Get league tier data for bar chart
            league_tier_data = get_league_tier_data(all_club_names)
            
            # Get match data grouped by season
            match_data_by_season = get_match_data_by_season(all_club_names)
            
            # Create bar chart
            chart_script, chart_div = create_league_tier_chart(
                league_tier_data
            )
            
            context.update({
                'modern_name': modern_name,
                'club_history_data': club_history_data,
                'league_tier_data': league_tier_data,
                'match_data_by_season': match_data_by_season,
                'chart_script': chart_script,
                'chart_div': chart_div,
            })
    
    return render(
        request,
        'club_analysis/club_league_performance.html',
        context
    )


def club_league_season_analysis(request: HttpRequest):
    """
    View for club league and season analysis page.
    """
    # Check if GOOGLE_API_KEY is defined
    has_api_key = bool(os.environ.get('GOOGLE_API_KEY'))
    
    # Handle AJAX request for seasons (only if API key is available)
    if request.method == 'GET' and request.GET.get('club'):
        if not has_api_key:
            return JsonResponse(
                {'error': 'API key not available'},
                status=500
            )
        club_name = request.GET.get('club')
        # Get all seasons for this club from club_season
        seasons = (
            ClubSeason.objects
            .filter(club_name=club_name)
            .select_related('league')
            .values_list('league__season', flat=True)
            .distinct()
            .order_by('league__season')
        )
        return JsonResponse({'seasons': list(seasons)})
    
    # Get all unique club names from club_history, sorted alphabetically
    # (only if API key is available)
    clubs = []
    if has_api_key:
        clubs = (
            ClubHistory.objects
            .values_list('club_name', flat=True)
            .distinct()
            .order_by('club_name')
        )
    
    context: Dict[str, Any] = {
        'has_api_key': has_api_key,
        'clubs': clubs,
    }
    
    return render(
        request,
        'club_analysis/club_league_season_analysis.html',
        context
    )


def get_club_season_analysis(request: HttpRequest):
    """
    Handle AJAX request to get AI-powered analysis for a club's season.
    """
    # Check if GOOGLE_API_KEY is defined
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        return JsonResponse(
            {
                'error': (
                    'GOOGLE_API_KEY environment variable is not set'
                ),
                'html': ''
            },
            status=500
        )
    
    # Get club and season from request
    club = request.GET.get('club', '')
    season = request.GET.get('season', '')
    
    if not club or not season:
        return JsonResponse(
            {
                'error': 'Club and season are required',
                'html': ''
            },
            status=400
        )
    
    try:

        # This ensures the model returns a valid, predictable JSON object.
        # Using Pydantic BaseModel instead of TypedDict because
        # Google GenAI SDK requires a Pydantic model for response_schema
        class SoccerAnalysis(BaseModel):
            """Defines the required keys and value types for the JSON output."""
            Domestic_performance: str
            International_performance: str
            Team_notes: str
            Team_photos: str
            Notable_events: str

        # Build prompt
        prompt: str = (
            f'Using only soccer websites, give me an analysis of the '
            f'English soccer team {club}\'s season {season}. '
            'The analysis MUST be returned as a JSON object, strictly '
            'following the provided schema. '
            'The analysis should include: '
            '* Domestic league and cup performance. Include best and '
            'worst results. (HTML string). '
            '* International performance ("No international games played." '
            'if no games) (HTML string). '
            '* Team notes (best players, team and manager changes) '
            '(HTML string). '
            '* Team photos (if you can definitely find photos for this '
            'team for this season, include them as links. If not, say '
            'so.) '
            '* Any notable drama/scandals on or off the pitch '
            '(HTML string).'
        )

        # Initialize Google AI client
        client = genai.Client(api_key=api_key)

        # Configure the generation request
        config = genai.types.GenerateContentConfig(
            # CRITICAL: Specify JSON output format
            response_mime_type="application/json",
            # CRITICAL: Provide the TypedDict schema
            response_schema=SoccerAnalysis,
        )

        # Send prompt to Gemini API
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=config,
        )

    except APIError as e:
        # Handle API-specific errors (e.g., authentication, rate
        # limiting, invalid model)
        return JsonResponse(
            {
                'error': f'Google GenAI API Error occurred: {str(e)}',
                'html': ''
            },
            status=500
        )

    except Exception as e:
        # Handle any other errors
        error_msg = f'Error generating analysis: {str(e)}'
        return JsonResponse(
            {'error': error_msg, 'html': ''},
            status=500
        )


    try:
        # Parse the JSON response from the API
        response_text = response.text
        club_season = json.loads(response_text)

        # Create HTML string
        html_content = (
            f'<body>\n'
            f'    <hr>\n'
            f'    <h1>Club: {club} Season: {season}</h1>\n'
            f'    <h2>Domestic performance</h2>\n'
            f'    <p>{club_season["Domestic_performance"]}</p>\n'
            f'    <h2>International performance</h2>\n'
            f'    <p>{club_season["International_performance"]}</p>\n'
            f'    <h2>Team notes</h2>\n'
            f'    <p>{club_season["Team_notes"]}</p>\n'
            f'    <h2>Team photos</h2>\n'
            f'    <p>{club_season["Team_photos"]}</p>\n'
            f'    <h2>Notable events</h2>\n'
            f'    <p>{club_season["Notable_events"]}</p>\n'
            f'</body>\n'
        )

        return JsonResponse(
            {'error': None, 'html': html_content},
            status=200
        )

    except Exception as e:
        # Handle any other errors
        error_msg = f'Error generating analysis: {str(e)}'
        return JsonResponse(
            {'error': error_msg, 'html': ''},
            status=500
        )


def get_club_history_data(
    club_name: str,
    modern_name: str,
) -> List[Dict[str, Any]]:
    """
    Get club history data for the selected club.

    Returns:
        List of dictionaries with year, club_name, modern_name,
        nickname, event, wikipedia.
    """
    history_records = (
        ClubHistory.objects
        .filter(modern_name=modern_name)
        .order_by('year_changed')
    )
    
    return [
        {
            'year': record.year_changed,
            'club_name': record.club_name,
            'modern_name': record.modern_name,
            'nickname': record.nickname or '',
            'event': record.notes or '',
            'wikipedia': record.wikipedia or '',
        }
        for record in history_records
    ]


def get_league_tier_data(
    all_club_names: List[str],
) -> List[Dict[str, Any]]:
    """
    Get league tier data for bar chart.

    Returns:
        List of dictionaries with club_name, season_start, league_tier.
    """
    # Join club_season with league to get season and league_tier
    club_seasons = (
        ClubSeason.objects
        .filter(club_name__in=all_club_names)
        .select_related('league')
        .values(
            'club_name',
            'league__season',
            'league__league_tier',
        )
        .order_by('league__season')
    )
    
    result = []
    for cs in club_seasons:
        season = cs['league__season']
        # Extract season start year: int(season[0:4])
        season_start = int(season[:4])
        result.append({
            'club_name': cs['club_name'],
            'season_start': season_start,
            'league_tier': cs['league__league_tier'],
        })
    
    return result


def get_match_data_by_season(
    all_club_names: List[str],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get match data grouped by season.

    Returns:
        Dictionary where keys are seasons and values are lists of
        match dicts.
    """
    # Get all matches where the club is either home or away
    matches = (
        FootballMatch.objects
        .filter(
            Q(home_club__in=all_club_names) |
            Q(away_club__in=all_club_names)
        )
        .select_related('league')
        .values(
            'league__season',
            'league__league_tier',
            'home_club',
            'away_club',
            'home_goals',
            'away_goals',
            'match_date',
        )
        .order_by('league__season', 'match_date')
    )
    
    # Group by season
    matches_by_season: Dict[str, List[Dict[str, Any]]] = {}
    
    for match in matches:
        season = match['league__season']
        if season not in matches_by_season:
            matches_by_season[season] = []
        
        matches_by_season[season].append({
            'season': season,
            'league_tier': match['league__league_tier'],
            'home_club': match['home_club'],
            'away_club': match['away_club'],
            'home_goals': match['home_goals'],
            'away_goals': match['away_goals'],
            'match_date': match['match_date'],
        })
    
    # Sort each season's matches by match_date
    for season in matches_by_season:
        matches_by_season[season].sort(key=lambda x: x['match_date'])
    
    return matches_by_season


def create_league_tier_chart(
    league_tier_data: List[Dict[str, Any]],
) -> tuple:
    """
    Create a bar chart showing league tier vs season start.

    Returns:
        Tuple of (script, div) for Bokeh chart embedding.
    """
    if not league_tier_data:
        # Return empty chart if no data
        plot = figure(
            title='League Tier Over Time',
            x_axis_label='Season Start',
            y_axis_label='League Tier',
            height=400,
            sizing_mode="stretch_width",
        )
        plot.y_range.flipped = True
        script, div = components(plot)
        return script, div
    
    # Sort data by season_start to ensure proper ordering
    sorted_data = sorted(league_tier_data, key=lambda x: x['season_start'])
    
    # Prepare data for chart
    season_starts = [d['season_start'] for d in sorted_data]
    league_tiers = [d['league_tier'] for d in sorted_data]
    
    source = ColumnDataSource({
        'season_start': season_starts,
        'league_tier': league_tiers,
    })
    
    plot = figure(
        title='League Tier Over Time',
        x_axis_label='Season Start',
        y_axis_label='League Tier',
        height=400,
        sizing_mode="stretch_width",
        toolbar_location=None,
    )
    
    # Reverse y-axis so league 1 is at the top
    plot.y_range.flipped = True
    
    # Create bar chart
    plot.vbar(
        x='season_start',
        top='league_tier',
        width=0.8,
        source=source,
        fill_color='lightgreen',
        line_color='lightgreen',
    )
    
    # Add hover tool
    hover = HoverTool(
        tooltips=[
            ('Season Start', '@season_start'),
            ('League Tier', '@league_tier'),
        ]
    )
    plot.add_tools(hover)
    
    # Set y-axis to show integer tiers
    if league_tiers:
        max_tier = max(league_tiers)
        plot.yaxis.ticker = list(range(1, max_tier + 2))
    
    script, div = components(plot)
    return script, div
