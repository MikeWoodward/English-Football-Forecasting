from django.db import models
from django.db.models import (
    Avg,
    Sum,
    F,
    ExpressionWrapper,
    DecimalField,
    FloatField,
    Case,
    When,
    IntegerField,
    Count,
    Q,
    OuterRef,
    Subquery,
    StdDev,
)
from django.db.models.functions import Cast, Substr


class AttendanceViolinManager(models.Manager):
    """
    Custom manager for AttendanceViolin model with methods to calculate
    statistics.
    """

    def get_attendance_violin_data(
        self,
        *,
        season_start: int,
    ):
        """
        Return attendance violin data per league for a specific season.

        Args:
            season_start: Season start year to filter data (e.g., 2023)

        Returns:
            QuerySet: Annotated queryset with league_tier, attendance,
            and probability_density fields.
        """
        season_selector = str(season_start) + '-' + str(season_start + 1)
        return (
            self.get_queryset()
            .select_related('league')
            .filter(league__season=season_selector)
            .annotate(
                league_tier=F('league__league_tier'),
            )
            .values(
                'league_tier',
                'attendance',
                'probability_density',
            )
        )

    def get_attendance_violin_season_range(self) -> tuple[int, int]:
        """
        Return the minimum and maximum season start values.

        Based on the attendance violin data, extracts the first four
        characters of the season field to determine season start years.

        Returns:
            tuple[int, int]: Tuple containing (min_season_start,
            max_season_start)
        """
        # Get all unique season values from attendance_violin
        # Extract first 4 characters (season start year)
        queryset = (
            self.get_queryset()
            .select_related('league')
            .values_list('league__season', flat=True)
            .distinct()
        )
        # Extract season start years (first 4 characters)
        season_starts = [
            int(season[:4]) for season in queryset if season
        ]
        min_season = min(season_starts)
        max_season = max(season_starts)
        return (min_season, max_season)


class AttendanceViolin(models.Model):
    attendance = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    probability_density = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    league = models.ForeignKey('League', models.DO_NOTHING)
    attendance_league_id = models.CharField(primary_key=True, max_length=255)

    objects = AttendanceViolinManager()

    class Meta:
        managed = False
        db_table = 'attendance_violin'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class ClubHistory(models.Model):
    club_name_year_changed_id = models.CharField(primary_key=True, max_length=255)
    club_name = models.CharField(max_length=255)
    nickname = models.CharField(max_length=255, blank=True, null=True)
    modern_name = models.CharField(max_length=255)
    year_changed = models.IntegerField()
    date_changed = models.DateField(blank=True, null=True)
    notes = models.CharField(max_length=255, blank=True, null=True)
    wikipedia = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'club_history'

class ClubSeason(models.Model):
    league = models.ForeignKey('League', models.DO_NOTHING)
    club_name = models.CharField(max_length=255)
    club_league_id = models.CharField(primary_key=True, max_length=255)
    squad_size = models.IntegerField(blank=True, null=True)
    foreigner_count = models.IntegerField(blank=True, null=True)
    foreigner_fraction = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    mean_age = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    total_market_value = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'club_season'


class CustomUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    is_admin = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'custom_user'


class CustomUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    customuser = models.ForeignKey(CustomUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'custom_user_groups'
        unique_together = (('customuser', 'group'),)


class CustomUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    customuser = models.ForeignKey(CustomUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'custom_user_user_permissions'
        unique_together = (('customuser', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(CustomUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class FootballMatch(models.Model):
    match_id = models.CharField(primary_key=True, max_length=255)
    league = models.ForeignKey('League', models.DO_NOTHING)
    match_date = models.DateField()
    match_time = models.TimeField(blank=True, null=True)
    match_day_of_week = models.CharField(max_length=255)
    attendance = models.IntegerField()
    home_club = models.CharField(max_length=255)
    home_goals = models.IntegerField(blank=True, null=True)
    home_fouls = models.IntegerField(blank=True, null=True)
    home_yellow_cards = models.IntegerField(blank=True, null=True)
    home_red_cards = models.IntegerField(blank=True, null=True)
    away_club = models.CharField(max_length=255)
    away_goals = models.IntegerField(blank=True, null=True)
    away_fouls = models.IntegerField(blank=True, null=True)
    away_yellow_cards = models.IntegerField(blank=True, null=True)
    away_red_cards = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'football_match'


class LeagueManager(models.Manager):
    """
    Custom manager for League model with methods to calculate statistics.
    """

    def get_mean_goals_per_league_per_season(self):
        """
        Return mean number of goals scored per league per season.

        Returns:
            QuerySet: Annotated queryset with league_tier, season,
            season_start, and mean_goals fields.
        """
        # Use FootballMatch directly which has home_goals and away_goals
        # Total goals per match = home_goals + away_goals
        return (
            FootballMatch.objects
            .select_related('league')
            .values(
                'league__league_tier',
                'league__season',
            )
            .annotate(
                total_goals=Sum(
                    ExpressionWrapper(
                        F('home_goals') + F('away_goals'),
                        output_field=IntegerField(),
                    ),
                ),
                match_count=F('league__league_size_matches'),
            )
            .annotate(
                league_tier=F('league__league_tier'),
                season_start=Substr('league__season', 1, 4),
                mean_goals=ExpressionWrapper(
                    Cast(F('total_goals'), FloatField()) / 
                    Cast(F('match_count'), FloatField()),
                    output_field=FloatField(),
                ),
            )
            .values(
                'league_tier',
                'season_start',
                'mean_goals',
            )
        )

    def get_home_win_fraction(self):
        """
        Return home win fraction per league per season.

        Home win fraction is the fraction of all wins that were home
        wins. If there were no home advantage, we would expect this
        fraction to be 0.5.

        Returns:
            QuerySet: Annotated queryset with league_tier, season_start,
            and home_win_fraction fields.
        """
        # Use FootballMatch directly which has home_goals and away_goals
        # fields. Use conditional aggregation to count wins directly
        return (
            FootballMatch.objects
            .select_related('league')
            .values(
                'league__league_tier',
                'league__season',
            )
            .annotate(
                home_wins=Sum(
                    Case(
                        When(
                            home_goals__gt=F('away_goals'),
                            then=1,
                        ),
                        default=0,
                        output_field=IntegerField(),
                    ),
                ),
                total_wins=Sum(
                    Case(
                        When(
                            home_goals__gt=F('away_goals'),
                            then=1,
                        ),
                        When(
                            away_goals__gt=F('home_goals'),
                            then=1,
                        ),
                        default=0,
                        output_field=IntegerField(),
                    ),
                ),
            )
            .annotate(
                league_tier=F('league__league_tier'),
                season_start=Substr('league__season', 1, 4),
                home_win_fraction=ExpressionWrapper(
                    Cast(F('home_wins'), FloatField()) / 
                    Cast(F('total_wins'), FloatField()),
                    output_field=FloatField(),
                ),
            )
            .values(
                'league_tier',
                'season_start',
                'home_win_fraction',
            )
        )

    def get_home_goal_advantage(self):
        """
        Return home goal advantage per league per season.

        Home goal advantage is the mean difference in goals scored
        by the home team and the away team. It quantifies how many
        goals home advantage is worth.

        Returns:
            QuerySet: Annotated queryset with league_tier, season_start,
            and home_goal_advantage fields.
        """
        # Use FootballMatch directly which has home_goals and away_goals
        # Calculate mean goal advantage per league/season
        return (
            FootballMatch.objects
            .select_related('league')
            .values(
                'league__league_tier',
                'league__season',
            )
            .annotate(
                league_tier=F('league__league_tier'),
                season_start=Substr('league__season', 1, 4),
                home_goal_advantage=Avg(
                    ExpressionWrapper(
                        F('home_goals') - F('away_goals'),
                        output_field=IntegerField(),
                    ),
                    output_field=FloatField(),
                ),
            )
            .values(
                'league_tier',
                'season_start',
                'home_goal_advantage',
            )
        )

    def get_draw_fraction(self):
        """
        Return draw fraction per league per season.

        Draw fraction is the fraction of all matches in a season that
        end in a draw (home_goals == away_goals).

        Returns:
            QuerySet: Annotated queryset with league_tier, season_start,
            and draw_fraction fields.
        """
        # Use FootballMatch directly which has home_goals and away_goals
        # Use conditional aggregation to count draws directly
        return (
            FootballMatch.objects
            .select_related('league')
            .values(
                'league__league_tier',
                'league__season',
            )
            .annotate(
                draws=Sum(
                    Case(
                        When(
                            home_goals=F('away_goals'),
                            then=1,
                        ),
                        default=0,
                        output_field=IntegerField(),
                    ),
                ),
                match_count=Count('match_id'),
            )
            .annotate(
                league_tier=F('league__league_tier'),
                season_start=Substr('league__season', 1, 4),
                draw_fraction=ExpressionWrapper(
                    Cast(F('draws'), FloatField()) / 
                    Cast(F('match_count'), FloatField()),
                    output_field=FloatField(),
                ),
            )
            .values(
                'league_tier',
                'season_start',
                'draw_fraction',
            )
        )
    def get_red_card_data(self):
        """
        Return red card data per league per season.

        Red card data is the number of red cards per match.

        Returns:
            QuerySet: Annotated queryset with league_tier, season_start,
            and red_cards_per_match fields.
        """
        # Use FootballMatch directly which has home_red_cards and away_red_cards
        # Sum total red cards and divide by match count
        return (
            FootballMatch.objects
            .select_related('league')
            .values(
                'league__league_tier',
                'league__season',
            )
            .annotate(
                total_red_cards=Sum(
                    ExpressionWrapper(
                        F('home_red_cards') + F('away_red_cards'),
                        output_field=IntegerField(),
                    ),
                ),
                match_count=Count('match_id'),
            )
            .annotate(
                league_tier=F('league__league_tier'),
                season_start=Substr('league__season', 1, 4),
                mean_red_cards=ExpressionWrapper(
                    Cast(F('total_red_cards'), FloatField()) / 
                    Cast(F('match_count'), FloatField()),
                    output_field=FloatField(),
                ),
            )
            .values(
                'league_tier',
                'season_start',
                'mean_red_cards',
            )
        )

    def get_yellow_card_data(self):
        """
        Return yellow card data per league per season.

        Yellow card data is the number of yellow cards per match.

        Returns:
            QuerySet: Annotated queryset with league_tier, season_start,
            and yellow_cards_per_match fields.
        """
        # Use FootballMatch directly which has home_yellow_cards and 
        # away_yellow_cards. Sum total yellow cards and divide by match count
        return (
            FootballMatch.objects
            .select_related('league')
            .values(
                'league__league_tier',
                'league__season',
            )
            .annotate(
                total_yellow_cards=Sum(
                    ExpressionWrapper(
                        F('home_yellow_cards') + F('away_yellow_cards'),
                        output_field=IntegerField(),
                    ),
                ),
                match_count=Count('match_id'),
            )
            .annotate(
                league_tier=F('league__league_tier'),
                season_start=Substr('league__season', 1, 4),
                mean_yellow_cards=ExpressionWrapper(
                    Cast(F('total_yellow_cards'), FloatField()) / 
                    Cast(F('match_count'), FloatField()),
                    output_field=FloatField(),
                ),
            )
            .values(
                'league_tier',
                'season_start',
                'mean_yellow_cards',
            )
        )

    def get_foul_data(self):
        """
        Return foul data per league per season.

        Foul data is the number of fouls per match.

        Returns:
            QuerySet: Annotated queryset with league_tier, season_start,
            and fouls_per_match fields.
        """
        # Use FootballMatch directly which has home_fouls and away_fouls.
        # Sum total fouls and divide by match count
        return (
            FootballMatch.objects
            .select_related('league')
            .values(
                'league__league_tier',
                'league__season',
            )
            .annotate(
                total_fouls=Sum(
                    ExpressionWrapper(
                        F('home_fouls') + F('away_fouls'),
                        output_field=IntegerField(),
                    ),
                ),
                match_count=Count('match_id'),
            )
            .annotate(
                league_tier=F('league__league_tier'),
                season_start=Substr('league__season', 1, 4),
                mean_fouls=ExpressionWrapper(
                    Cast(F('total_fouls'), FloatField()) / 
                    Cast(F('match_count'), FloatField()),
                    output_field=FloatField(),
                ),
            )
            .values(
                'league_tier',
                'season_start',
                'mean_fouls',
            )
        )

    def get_total_attendance_data(self):
        """
        Return attendance data per league per season.

        Attendance data is the total attendance per league per season.

        Returns:
            QuerySet: Annotated queryset with league_tier, season_start,
            and total_attendance fields.
        """
        # Use FootballMatch directly which has attendance field.
        # Sum total attendance per league per season
        return (
            FootballMatch.objects
            .select_related('league')
            .values(
                'league__league_tier',
                'league__season',
            )
            .annotate(
                total_attendance=Sum('attendance'),
            )
            .annotate(
                league_tier=F('league__league_tier'),
                season_start=Substr('league__season', 1, 4),
            )
            .values(
                'league_tier',
                'season_start',
                'total_attendance',
            )
        )

    def get_mean_attendance_data(self):
        """
        Return mean attendance data per league per season.

        Mean attendance data is the mean attendance per match.

        Returns:
            QuerySet: Annotated queryset with league_tier, season_start,
            and mean_attendance fields.
        """
        # Use FootballMatch directly which has attendance field.
        # Sum total attendance and divide by match count
        return (
            FootballMatch.objects
            .select_related('league')
            .values(
                'league__league_tier',
                'league__season',
            )
            .annotate(
                total_attendance=Sum('attendance'),
                match_count=Count('match_id'),
            )
            .annotate(
                league_tier=F('league__league_tier'),
                season_start=Substr('league__season', 1, 4),
                mean_attendance=ExpressionWrapper(
                    Cast(F('total_attendance'), FloatField()) / 
                    Cast(F('match_count'), FloatField()),
                    output_field=FloatField(),
                ),
            )
            .values(
                'league_tier',
                'season_start',
                'mean_attendance',
            )
        )

    def get_win_fraction_sd_over_time(self):
        """
        Return win fraction standard deviation data per league per season.

        Win fraction standard deviation data is the standard deviation of
        the win fraction across all teams in each league and season.

        First calculates win fraction for each team in each league/season:
        - Home wins: when team is home_club and home_goals > away_goals
        - Away wins: when team is away_club and away_goals > home_goals
        - Total games: when team is home_club OR away_club
        - Win fraction: (home_wins + away_wins) / total_games

        Then calculates the standard deviation of these win fractions
        grouped by league and season.

        Returns:
            QuerySet: Annotated queryset with league_tier, season_start,
            and win_fraction_sd fields.
        """
        # Use raw SQL to calculate win fractions per club per league/season,
        # then calculate standard deviation. This avoids aggregating
        # aggregations by using CTEs.
        from django.db import connection

        sql = """
            WITH club_matches AS (
                -- Home matches for each club
                SELECT 
                    l.league_tier,
                    l.season,
                    fm.home_club AS club_name,
                    CASE WHEN fm.home_goals > fm.away_goals THEN 1 
                         ELSE 0 END AS is_win,
                    1 AS is_game
                FROM football_match fm
                JOIN league l ON fm.league_id = l.league_id
                WHERE fm.home_goals IS NOT NULL 
                  AND fm.away_goals IS NOT NULL
                
                UNION ALL
                
                -- Away matches for each club
                SELECT 
                    l.league_tier,
                    l.season,
                    fm.away_club AS club_name,
                    CASE WHEN fm.away_goals > fm.home_goals THEN 1 
                         ELSE 0 END AS is_win,
                    1 AS is_game
                FROM football_match fm
                JOIN league l ON fm.league_id = l.league_id
                WHERE fm.home_goals IS NOT NULL 
                  AND fm.away_goals IS NOT NULL
            ),
            club_win_fractions AS (
                -- Calculate win fraction for each club per league/season
                SELECT
                    league_tier,
                    season,
                    club_name,
                    CAST(SUM(is_win) AS FLOAT) / 
                    CAST(SUM(is_game) AS FLOAT) AS win_fraction
                FROM club_matches
                GROUP BY league_tier, season, club_name
            )
            -- Calculate standard deviation of win fractions per league/season
            SELECT
                league_tier,
                SUBSTR(season, 1, 4) AS season_start,
                STDDEV(win_fraction) AS win_fraction_sd
            FROM club_win_fractions
            GROUP BY league_tier, season
        """

        # Execute the query and return results as a list of dictionaries
        # matching the pattern of other functions
        with connection.cursor() as cursor:
            cursor.execute(sql)
            columns = [col[0] for col in cursor.description]
            results = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

        # Return a QuerySet-like structure that matches the interface
        # of other functions
        class WinFractionSDQuerySet:
            """
            Simple QuerySet-like wrapper for win fraction std dev results.
            """
            def __init__(self, results):
                self._results = results

            def __iter__(self):
                return iter(self._results)

            def __getitem__(self, key):
                return self._results[key]

            def __len__(self):
                return len(self._results)

            def values(self, *fields):
                # Already in dict format, just filter fields if needed
                if not fields:
                    return self
                return WinFractionSDQuerySet([
                    {k: v for k, v in item.items() if k in fields}
                    for item in self._results
                ])

        return WinFractionSDQuerySet(results)

 


class League(models.Model):
    league_id = models.CharField(primary_key=True, max_length=255)
    season = models.CharField(max_length=255)
    league_tier = models.IntegerField()
    league_name = models.CharField(max_length=255)
    season_start = models.DateField()
    season_end = models.DateField()
    league_size_matches = models.IntegerField()
    league_size_clubs = models.IntegerField()
    league_notes = models.TextField(blank=True, null=True)

    objects = LeagueManager()

    class Meta:
        managed = False
        db_table = 'league'