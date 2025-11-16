"""
Views for the club analysis app.
"""
from typing import Dict, List, Any, Optional
from django.shortcuts import render
from django.http import HttpRequest, JsonResponse
from django.db.models import Q, F, IntegerField
from django.db.models.functions import Substr, Cast
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool
from goals.models import (
    ClubHistory,
    ClubSeason,
    League,
    FootballMatch,
)


def club_analysis(request: HttpRequest):
    """
    Main view for club analysis page.
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
            club_history_data = get_club_history_data(selected_club, modern_name)
            
            # Get league tier data for bar chart
            league_tier_data = get_league_tier_data(all_club_names)
            
            # Get match data grouped by season
            match_data_by_season = get_match_data_by_season(all_club_names)
            
            # Create bar chart
            chart_script, chart_div = create_league_tier_chart(league_tier_data)
            
            context.update({
                'modern_name': modern_name,
                'club_history_data': club_history_data,
                'league_tier_data': league_tier_data,
                'match_data_by_season': match_data_by_season,
                'chart_script': chart_script,
                'chart_div': chart_div,
            })
    
    return render(request, 'club_analysis/club_analysis.html', context)


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
        Dictionary where keys are seasons and values are lists of match dicts.
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
