"""
Admin configuration for the goals app.
"""
from django.contrib.admin import ModelAdmin
from .models import FootballMatch, League, ClubSeason

# Import admin_site with error handling
try:
    from admin_app.admin import admin_site
except ImportError:
    # Fallback to default admin if custom admin fails to import
    from django.contrib import admin
    admin_site = admin.site


class FootballMatchAdmin(ModelAdmin):
    """Admin interface for FootballMatch model."""
    list_display = (
        'match_id',
        'match_date',
        'home_club',
        'away_club',
        'home_goals',
        'away_goals',
        'attendance',
    )
    list_filter = (
        'match_date',
        'league',
    )
    search_fields = (
        'home_club',
        'away_club',
        'match_id',
    )
    readonly_fields = ('match_id',)
    date_hierarchy = 'match_date'
    ordering = ('-match_date',)


class LeagueAdmin(ModelAdmin):
    """Admin interface for League model."""
    list_display = (
        'league_id',
        'league_name',
        'season',
        'league_tier',
        'season_start',
        'season_end',
        'league_size_clubs',
    )
    list_filter = (
        'league_tier',
        'season',
    )
    search_fields = (
        'league_name',
        'league_id',
        'season',
    )
    readonly_fields = ('league_id',)
    ordering = ('-season_start', 'league_tier',)


class ClubSeasonAdmin(ModelAdmin):
    """Admin interface for ClubSeason model."""
    list_display = (
        'club_league_id',
        'club_name',
        'league',
        'squad_size',
        'mean_age',
        'foreigner_count',
        'total_market_value',
    )
    list_filter = (
        'league',
    )
    search_fields = (
        'club_name',
        'club_league_id',
    )
    readonly_fields = ('club_league_id',)
    ordering = ('club_name',)


# Register models after classes are defined
admin_site.register(FootballMatch, FootballMatchAdmin)
admin_site.register(League, LeagueAdmin)
admin_site.register(ClubSeason, ClubSeasonAdmin)

