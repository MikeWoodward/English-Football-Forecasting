# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models, connection
from django.db.models import (
    Sum,
    Case,
    When,
    OuterRef,
    F,
    Min,
    Max,
    IntegerField,
)
from django.db.models.functions import Substr, Cast
from collections import defaultdict
from typing import Dict, List, Any
import numpy as np
import statsmodels.api as sm


class AttendanceViolin(models.Model):
    attendance = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    probability_density = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    league = models.ForeignKey('League', models.DO_NOTHING)
    attendance_league_id = models.CharField(primary_key=True, max_length=255)

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


class ClubSeasonManager(models.Manager):
    """
    Custom manager for ClubSeason model with methods to analyze
    market value data.
    """

    def get_season_min_max(self):
        """
        Return the minimum and maximum season for which there is
        club season data.

        Returns:
            Tuple of (min_season, max_season) where each value is a string
            representing the season (e.g., "2024-2025").
            Returns (None, None) if no club season data exists.
        """
        # Aggregate to find the minimum and maximum season values
        # across all club season records
        result = (
            self.aggregate(
                min_season=Min('league__season'),
                max_season=Max('league__season'),
            )
        )
        # Return tuple of min and max season values
        return result['min_season'], result['max_season']

    def get_club_money_season_min_max(self):
        """
        Return the minimum and maximum season for which there is a
        total_market_value.

        Returns:
            Tuple of (min_season, max_season) where each value is a string
            representing the season (e.g., "2024-2025").
            Returns (None, None) if no market value data exists.
        """
        # Filter for records with non-null total_market_value
        # then aggregate to find min and max season values
        result = (
            self.filter(total_market_value__isnull=False)
            .aggregate(
                min_season=Min('league__season'),
                max_season=Max('league__season'),
            )
        )

        # Return tuple of min and max season values
        return result['min_season'], result['max_season']

    def get_club_mean_age_season_min_max(self):
        """
        Return the minimum and maximum season for which there is a
        mean_age.

        Returns:
            Tuple of (min_season, max_season) where each value is a string
            representing the season (e.g., "2024-2025").
            Returns (None, None) if no mean age data exists.
        """
        # Filter for records with non-null mean_age
        # then aggregate to find min and max season values
        result = (
            self.filter(mean_age__isnull=False)
            .aggregate(
                min_season=Min('league__season'),
                max_season=Max('league__season'),
            )
        )

        # Return tuple of min and max season values
        return result['min_season'], result['max_season']

    def get_club_foreigner_count_season_min_max(self):
        """
        Return the minimum and maximum season for which there is a
        foreigner_count.

        Returns:
            Tuple of (min_season, max_season) where each value is a string
            representing the season (e.g., "2024-2025").
            Returns (None, None) if no foreigner count data exists.
        """
        # Filter for records with non-null foreigner_count
        # then aggregate to find min and max season values
        result = (
            self.filter(foreigner_count__isnull=False)
            .aggregate(
                min_season=Min('league__season'),
                max_season=Max('league__season'),
            )
        )

        # Return tuple of min and max season values
        return result['min_season'], result['max_season']


class ClubSeason(models.Model):
    league = models.ForeignKey('League', models.DO_NOTHING)
    club_name = models.CharField(max_length=255)
    club_league_id = models.CharField(primary_key=True, max_length=255)
    squad_size = models.IntegerField(blank=True, null=True)
    foreigner_count = models.IntegerField(blank=True, null=True)
    foreigner_fraction = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    mean_age = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)
    total_market_value = models.DecimalField(max_digits=65535, decimal_places=65535, blank=True, null=True)

    objects = ClubSeasonManager()

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


class FootballMatchManager(models.Manager):
    """
    Custom manager for FootballMatch model with methods to analyze
    goals in relation to financial data.
    """

    def get_goals_by_money(
        self,
        *,
        season_start,
        league_tier,
    ):
        """
        Return goals as a function of money for a given season start.

        This method aggregates total goals scored by each club and their
        market value for matches in leagues starting on the specified date.

        Args:
            season_start: Date object or integer representing the season
                start year. If integer, represents the year (e.g., 2021).
            league_tier: Integer representing the league tier (1-4).

        Returns:
            list: List of dictionaries with club_name, league_id,
            total_goals, and total_market_value fields, ordered by
            total_market_value. Only includes clubs with market values.
        """

        # Handle both date objects and integer years
        # If season_start is an integer, treat it as a year
        if isinstance(season_start, int):
            start_year = season_start
        else:
            # If it's a date object, extract the year
            start_year = season_start.year

        # Convert season_start to season string format (e.g., "2024-2025")
        season = (
            str(start_year) + '-' + str(start_year + 1)
        )

        # Use parameterized query to prevent SQL injection
        # This query aggregates goals for each club by combining home and away
        # matches, then joins with club_season to get market values
        sql = """
        select 
            subby.league_id,
            subby.club_name, 
            sum(for_goals) as for_goals, 
            sum(against_goals) as against_goals,
            sum(for_goals) - sum(against_goals) as net_goals,
            club_season.total_market_value
        from
            (
                -- Subquery 1: Aggregate goals when club is home team
                select
                    league.league_id,
                    home_club as club_name, 
                    sum(home_goals) as for_goals, 
                    sum(away_goals) as against_goals
                from 
                    football_match
                join
                    league
                on
                    league.league_id = football_match.league_id
                where
                    league_tier = %s and season = %s
                group by
                    league.league_id,
                    home_club
                union all
                -- Subquery 2: Aggregate goals when club is away team
                select
                    league.league_id,
                    away_club as club_name, 
                    sum(away_goals) as for_goals, 
                    sum(home_goals) as against_goals
                from 
                    football_match
                join
                    league
                on
                    league.league_id = football_match.league_id
                where
                    league_tier = %s and season = %s
                group by
                    league.league_id,
                    away_club
            ) as subby
        join
            club_season
        on
            club_season.league_id = subby.league_id and
            club_season.club_name = subby.club_name
        where
            club_season.total_market_value is not null
        group by
            subby.league_id,
            subby.club_name,
            club_season.total_market_value
        order by
            club_season.total_market_value
        """

        with connection.cursor() as cursor:
            cursor.execute(
                sql,
                [league_tier, season, league_tier, season],
            )
            columns = [col[0] for col in cursor.description]
            result = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

        json_data: Dict[str, List[Any]] = {
            'club_name': [
                row['club_name'] for row in result
            ],
            'for_goals': [
                int(row['for_goals']) if row['for_goals'] else 0
                for row in result
            ],
            'against_goals': [
                int(row['against_goals'])
                if row['against_goals'] else 0
                for row in result
            ],
            'net_goals': [
                int(row['net_goals']) if row['net_goals'] else 0
                for row in result
            ],
            'total_market_value': [
                float(row['total_market_value'])
                if row['total_market_value'] else None
                for row in result
            ],
        }

        # Perform linear regression analysis for each goal type
        # Get predictions with 95% confidence intervals
        # Convert lists to numpy arrays and filter out None values
        market_values = np.array(json_data['total_market_value'])
        # Create boolean mask to identify valid (non-NaN) market values
        valid_mask = ~np.isnan(market_values)
        
        # Add constant term (intercept) for linear regression
        # OLS requires X to include a column of ones for the intercept
        X_const = sm.add_constant(market_values[valid_mask])
        
        # Perform regression for each goal type (for, against, net)
        for y_axis in ['for_goals', 'against_goals', 'net_goals']:
            # Get y values and filter to match valid market values
            # Only use data points where market value is not null
            y_values = np.array(json_data[y_axis])[valid_mask]
            
            # Create Ordinary Least Squares (OLS) linear regression model
            model = sm.OLS(y_values, X_const)
            # Fit the model to the data
            results = model.fit()
            
            # Get predictions with 95% confidence intervals
            # alpha=0.05 means 95% confidence interval
            predictions = (
                results
                .get_prediction(X_const)
                .summary_frame(alpha=0.05)
            )
            
            # Initialize arrays with NaN for all data points
            # This ensures arrays match the original data length
            fit_array = np.full(len(json_data[y_axis]), np.nan)
            fit_lower_array = np.full(len(json_data[y_axis]), np.nan)
            fit_upper_array = np.full(len(json_data[y_axis]), np.nan)
            
            # Fill in predictions only for valid data points
            # Invalid points remain NaN
            fit_array[valid_mask] = predictions['mean']
            fit_lower_array[valid_mask] = predictions['mean_ci_lower']
            fit_upper_array[valid_mask] = predictions['mean_ci_upper']
            
            # Convert numpy arrays back to Python lists for JSON serialization
            json_data[y_axis + '_fit'] = fit_array.tolist()
            json_data[y_axis + '_fit_lower'] = fit_lower_array.tolist()
            json_data[y_axis + '_fit_upper'] = fit_upper_array.tolist()

            # Add quality of fit metrics
            # R-squared: proportion of variance explained (0-1, higher is better)
            # p-value: statistical significance of the relationship
            json_data[y_axis + '_r2'] = results.rsquared
            # pvalues[1] is the p-value for the slope (not intercept)
            json_data[y_axis + '_pvalue'] = results.pvalues[1]
        return json_data

    def get_goals_by_tenure(
        self,
        *,
        season_start,
        league_tier,
    ):
        """
        Return goals as a function of tenure for a given season start.

        This method aggregates total goals scored by each club and their
        tenure for matches in leagues starting on the specified date.

        Args:
            season_start: Date object or integer representing the season
                start year. If integer, represents the year (e.g., 2021).
            league_tier: Integer representing the league tier (1-4).

        Returns:
            list: List of dictionaries with club_name, league_id,
            total_goals, and total_market_value fields, ordered by
            total_market_value. Only includes clubs with market values.
        """

        # Handle both date objects and integer years
        # If season_start is an integer, treat it as a year
        if isinstance(season_start, int):
            start_year = season_start
        else:
            # If it's a date object, extract the year
            start_year = season_start.year

        # Convert season_start to season string format (e.g., "2024-2025")
        season = (
            str(start_year) + '-' + str(start_year + 1)
        )

        # WARNING: This query uses f-strings instead of parameterized queries
        # This is a security risk (SQL injection vulnerability)
        # The complex nested tenure calculation makes parameterization difficult
        # TODO: Refactor to use parameterized queries
        # This query calculates tenure (consecutive seasons in league) using
        # a complex window function approach that handles gaps in seasons
        sql = f"""
                SELECT subby.club_name
                    ,SUM(for_goals) AS for_goals
                    ,SUM(against_goals) AS against_goals
                    ,SUM(for_goals) - SUM(against_goals) AS net_goals
                    ,seasons_in_league AS tenure
                FROM (
                    -- Aggregate goals when club is home team
                    SELECT league.league_id
                        ,home_club AS club_name
                        ,SUM(home_goals) AS for_goals
                        ,SUM(away_goals) AS against_goals
                    FROM football_match
                    JOIN league ON league.league_id = football_match.league_id
                    WHERE league_tier = {league_tier}
                        AND season = '{season}'
                    GROUP BY league.league_id
                        ,home_club
                    
                    UNION ALL
                    
                    -- Aggregate goals when club is away team
                    SELECT league.league_id
                        ,away_club AS club_name
                        ,SUM(away_goals) AS for_goals
                        ,SUM(home_goals) AS against_goals
                    FROM football_match
                    JOIN league ON league.league_id = football_match.league_id
                    WHERE league_tier = {league_tier}
                        AND season = '{season}'
                    GROUP BY league.league_id
                        ,away_club
                    ) AS subby
                JOIN (
                    -- Calculate tenure: count of consecutive seasons in league
                    -- This uses window functions to identify gaps in seasons
                    SELECT club_name
                        ,Count(season_start) AS seasons_in_league
                    FROM (
                        -- Calculate cumulative guard to identify continuous runs
                        SELECT club_name
                            ,season_start
                            ,guard
                            ,SUM(guard) OVER (
                                PARTITION BY club_name ORDER BY season_start DESC
                                ) AS cum_guard
                        FROM (
                            -- Fix guard values for special cases (WWI, WWII)
                            SELECT club_name
                                ,season_start
                                ,CASE 
                                    WHEN season_start = 1914
                                        AND guard = - 4
                                        THEN - 1
                                    WHEN season_start = 1938
                                        THEN guard + 7
                                    ELSE guard
                                    END AS guard
                            FROM (
                                -- Calculate guard: difference between consecutive
                                -- seasons (1 = consecutive, >1 = gap)
                                SELECT club_name
                                    ,season_start
                                    ,season_start + 1 - Lag(season_start, 1, 
                                        season_start + 1) OVER (
                                        PARTITION BY club_name ORDER BY club_name
                                            ,season_start DESC
                                        ) AS guard
                                FROM (
                                    -- Extract season start year from season string
                                    SELECT club_season.club_name AS club_name
                                        ,league_tier
                                        ,Substring(season, 1, 4)::INT AS 
                                        season_start
                                    FROM club_season
                                    JOIN league ON league.league_id = club_season
                                        .league_id
                                    JOIN (
                                        -- Filter to clubs in the target season/tier
                                        SELECT club_name
                                        FROM club_season
                                        JOIN league ON league.league_id = 
                                            club_season.league_id
                                        WHERE league_tier = {league_tier}
                                            AND season = '{season}'
                                        ) AS clubs ON clubs.club_name = 
                                        club_season.club_name
                                    WHERE league_tier = {league_tier}
                                    ORDER BY club_name
                                        ,season DESC
                                    ) AS clubs
                                ) AS guard
                            ) AS guard_fixed
                        )
                    -- Only count seasons in the current continuous run (cum_guard=0)
                    WHERE cum_guard = 0
                    GROUP BY club_name
                    ) AS tenure ON tenure.club_name = subby.club_name
                GROUP BY subby.club_name
                    ,seasons_in_league
                order by
                    tenure
        """

        # Execute SQL query (note: parameters are not used due to f-string)
        # This is a security risk that should be fixed
        with connection.cursor() as cursor:
            cursor.execute(
                sql,
                [league_tier, season, league_tier, season],
            )
            # Convert query results to list of dictionaries
            columns = [col[0] for col in cursor.description]
            result = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

        # Transform query results into JSON-friendly format
        # Each key contains a list of values, one per club
        json_data: Dict[str, List[Any]] = {
            'club_name': [
                row['club_name'] for row in result
            ],
            'for_goals': [
                int(row['for_goals']) if row['for_goals'] else 0
                for row in result
            ],
            'against_goals': [
                int(row['against_goals'])
                if row['against_goals'] else 0
                for row in result
            ],
            'net_goals': [
                int(row['net_goals']) if row['net_goals'] else 0
                for row in result
            ],
            'tenure': [
                int(row['tenure']) if row['tenure'] else 0
                for row in result
            ],
        }

        # Perform linear regression analysis for each goal type
        # Get predictions with 95% confidence intervals
        # Convert lists to numpy arrays and filter out None values
        tenure = np.array(json_data['tenure'])
        # Create boolean mask to identify valid (non-NaN) tenure values
        valid_mask = ~np.isnan(tenure)
        
        # Add constant term (intercept) for linear regression
        X_const = sm.add_constant(tenure[valid_mask])
        
        for y_axis in ['for_goals', 'against_goals', 'net_goals']:
            # Get y values and filter to match valid tenure values
            y_values = np.array(json_data[y_axis])[valid_mask]
            
            # Create OLS model with constant term
            model = sm.OLS(y_values, X_const)
            results = model.fit()
            
            # Get predictions with 95% confidence intervals
            predictions = (
                results
                .get_prediction(X_const)
                .summary_frame(alpha=0.05)
            )
            
            # Initialize arrays with NaN for all data points
            fit_array = np.full(len(json_data[y_axis]), np.nan)
            fit_lower_array = np.full(len(json_data[y_axis]), np.nan)
            fit_upper_array = np.full(len(json_data[y_axis]), np.nan)
            
            # Fill in predictions only for valid data points
            fit_array[valid_mask] = predictions['mean']
            fit_lower_array[valid_mask] = predictions['mean_ci_lower']
            fit_upper_array[valid_mask] = predictions['mean_ci_upper']
            
            # Convert back to lists
            json_data[y_axis + '_fit'] = fit_array.tolist()
            json_data[y_axis + '_fit_lower'] = fit_lower_array.tolist()
            json_data[y_axis + '_fit_upper'] = fit_upper_array.tolist()

            # Add quality of fit metrics
            json_data[y_axis + '_r2'] = results.rsquared
            json_data[y_axis + '_pvalue'] = results.pvalues[1]
        return json_data

    def get_goals_by_mean_age(
        self,
        *,
        season_start,
        league_tier,
    ):
        """
        Return goals as a function of mean age for a given season start.

        This method aggregates total goals scored by each club and their
        mean age for matches in leagues starting on the specified date.

        Args:
            season_start: Date object or integer representing the season
                start year. If integer, represents the year (e.g., 2021).
            league_tier: Integer representing the league tier (1-4).

        Returns:
            list: List of dictionaries with club_name, league_id,
            total_goals, and mean_age fields, ordered by
            mean_age. Only includes clubs with mean age values.
        """

        # Handle both date objects and integer years
        # If season_start is an integer, treat it as a year
        if isinstance(season_start, int):
            start_year = season_start
        else:
            # If it's a date object, extract the year
            start_year = season_start.year

        # Convert season_start to season string format (e.g., "2024-2025")
        season = (
            str(start_year) + '-' + str(start_year + 1)
        )

        # Use parameterized query to prevent SQL injection
        sql = """
        select 
            subby.league_id,
            subby.club_name, 
            sum(for_goals) as for_goals, 
            sum(against_goals) as against_goals,
            sum(for_goals) - sum(against_goals) as net_goals,
            club_season.mean_age
        from
            (
                select
                    league.league_id,
                    home_club as club_name, 
                    sum(home_goals) as for_goals, 
                    sum(away_goals) as against_goals
                from 
                    football_match
                join
                    league
                on
                    league.league_id = football_match.league_id
                where
                    league_tier = %s and season = %s
                group by
                    league.league_id,
                    home_club
                union all
                select
                    league.league_id,
                    away_club as club_name, 
                    sum(away_goals) as for_goals, 
                    sum(home_goals) as against_goals
                from 
                    football_match
                join
                    league
                on
                    league.league_id = football_match.league_id
                where
                    league_tier = %s and season = %s
                group by
                    league.league_id,
                    away_club
            ) as subby
        join
            club_season
        on
            club_season.league_id = subby.league_id and
            club_season.club_name = subby.club_name
        where
            club_season.mean_age is not null
        group by
            subby.league_id,
            subby.club_name,
            club_season.mean_age
        order by
            club_season.mean_age
        """

        with connection.cursor() as cursor:
            cursor.execute(
                sql,
                [league_tier, season, league_tier, season],
            )
            columns = [col[0] for col in cursor.description]
            # Convert query results to list of dictionaries
            result = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

        # Transform query results into JSON-friendly format
        # Each key contains a list of values, one per club
        json_data: Dict[str, List[Any]] = {
            'club_name': [
                row['club_name'] for row in result
            ],
            'for_goals': [
                int(row['for_goals']) if row['for_goals'] else 0
                for row in result
            ],
            'against_goals': [
                int(row['against_goals'])
                if row['against_goals'] else 0
                for row in result
            ],
            'net_goals': [
                int(row['net_goals']) if row['net_goals'] else 0
                for row in result
            ],
            'mean_age': [
                float(row['mean_age'])
                if row['mean_age'] else None
                for row in result
            ],
        }

        # Perform linear regression analysis for each goal type
        # Get predictions with 95% confidence intervals
        # Convert lists to numpy arrays and filter out None values
        mean_ages = np.array(json_data['mean_age'])
        # Create boolean mask to identify valid (non-NaN) mean age values
        valid_mask = ~np.isnan(mean_ages)
        
        # Add constant term (intercept) for linear regression
        X_const = sm.add_constant(mean_ages[valid_mask])
        
        for y_axis in ['for_goals', 'against_goals', 'net_goals']:
            # Get y values and filter to match valid mean ages
            # Only use data points where mean age is not null
            y_values = np.array(json_data[y_axis])[valid_mask]
            
            # Create OLS model with constant term
            model = sm.OLS(y_values, X_const)
            results = model.fit()
            
            # Get predictions with 95% confidence intervals
            predictions = (
                results
                .get_prediction(X_const)
                .summary_frame(alpha=0.05)
            )
            
            # Initialize arrays with NaN for all data points
            fit_array = np.full(len(json_data[y_axis]), np.nan)
            fit_lower_array = np.full(len(json_data[y_axis]), np.nan)
            fit_upper_array = np.full(len(json_data[y_axis]), np.nan)
            
            # Fill in predictions only for valid data points
            fit_array[valid_mask] = predictions['mean']
            fit_lower_array[valid_mask] = predictions['mean_ci_lower']
            fit_upper_array[valid_mask] = predictions['mean_ci_upper']
            
            # Convert back to lists
            json_data[y_axis + '_fit'] = fit_array.tolist()
            json_data[y_axis + '_fit_lower'] = fit_lower_array.tolist()
            json_data[y_axis + '_fit_upper'] = fit_upper_array.tolist()

            # Add quality of fit metrics
            json_data[y_axis + '_r2'] = results.rsquared
            json_data[y_axis + '_pvalue'] = results.pvalues[1]
        return json_data

    def get_goals_by_foreigner_count(
        self,
        *,
        season_start,
        league_tier,
    ):
        """
        Return goals as a function of foreigner count for a given season start.

        This method aggregates total goals scored by each club and their
        foreigner count for matches in leagues starting on the specified date.

        Args:
            season_start: Date object or integer representing the season
                start year. If integer, represents the year (e.g., 2021).
            league_tier: Integer representing the league tier (1-4).

        Returns:
            list: List of dictionaries with club_name, league_id,
            total_goals, and foreigner_count fields, ordered by
            foreigner_count. Only includes clubs with foreigner count values.
        """

        # Handle both date objects and integer years
        # If season_start is an integer, treat it as a year
        if isinstance(season_start, int):
            start_year = season_start
        else:
            # If it's a date object, extract the year
            start_year = season_start.year

        # Convert season_start to season string format (e.g., "2024-2025")
        season = (
            str(start_year) + '-' + str(start_year + 1)
        )

        # Use parameterized query to prevent SQL injection
        sql = """
        select 
            subby.league_id,
            subby.club_name, 
            sum(for_goals) as for_goals, 
            sum(against_goals) as against_goals,
            sum(for_goals) - sum(against_goals) as net_goals,
            club_season.foreigner_count
        from
            (
                select
                    league.league_id,
                    home_club as club_name, 
                    sum(home_goals) as for_goals, 
                    sum(away_goals) as against_goals
                from 
                    football_match
                join
                    league
                on
                    league.league_id = football_match.league_id
                where
                    league_tier = %s and season = %s
                group by
                    league.league_id,
                    home_club
                union all
                select
                    league.league_id,
                    away_club as club_name, 
                    sum(away_goals) as for_goals, 
                    sum(home_goals) as against_goals
                from 
                    football_match
                join
                    league
                on
                    league.league_id = football_match.league_id
                where
                    league_tier = %s and season = %s
                group by
                    league.league_id,
                    away_club
            ) as subby
        join
            club_season
        on
            club_season.league_id = subby.league_id and
            club_season.club_name = subby.club_name
        where
            club_season.foreigner_count is not null
        group by
            subby.league_id,
            subby.club_name,
            club_season.foreigner_count
        order by
            club_season.foreigner_count
        """

        with connection.cursor() as cursor:
            cursor.execute(
                sql,
                [league_tier, season, league_tier, season],
            )
            columns = [col[0] for col in cursor.description]
            # Convert query results to list of dictionaries
            result = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

        # Transform query results into JSON-friendly format
        # Each key contains a list of values, one per club
        json_data: Dict[str, List[Any]] = {
            'club_name': [
                row['club_name'] for row in result
            ],
            'for_goals': [
                int(row['for_goals']) if row['for_goals'] else 0
                for row in result
            ],
            'against_goals': [
                int(row['against_goals'])
                if row['against_goals'] else 0
                for row in result
            ],
            'net_goals': [
                int(row['net_goals']) if row['net_goals'] else 0
                for row in result
            ],
            'foreigner_count': [
                int(row['foreigner_count'])
                if row['foreigner_count'] else None
                for row in result
            ],
        }

        # Perform linear regression analysis for each goal type
        # Get predictions with 95% confidence intervals
        # Convert lists to numpy arrays and filter out None values
        foreigner_counts = np.array(json_data['foreigner_count'])
        # Create boolean mask to identify valid (non-NaN) foreigner counts
        valid_mask = ~np.isnan(foreigner_counts)
        
        # Add constant term (intercept) for linear regression
        X_const = sm.add_constant(foreigner_counts[valid_mask])
        
        for y_axis in ['for_goals', 'against_goals', 'net_goals']:
            # Get y values and filter to match valid foreigner counts
            # Only use data points where foreigner count is not null
            y_values = np.array(json_data[y_axis])[valid_mask]
            
            # Create OLS model with constant term
            model = sm.OLS(y_values, X_const)
            results = model.fit()
            
            # Get predictions with 95% confidence intervals
            predictions = (
                results
                .get_prediction(X_const)
                .summary_frame(alpha=0.05)
            )
            
            # Initialize arrays with NaN for all data points
            fit_array = np.full(len(json_data[y_axis]), np.nan)
            fit_lower_array = np.full(len(json_data[y_axis]), np.nan)
            fit_upper_array = np.full(len(json_data[y_axis]), np.nan)
            
            # Fill in predictions only for valid data points
            fit_array[valid_mask] = predictions['mean']
            fit_lower_array[valid_mask] = predictions['mean_ci_lower']
            fit_upper_array[valid_mask] = predictions['mean_ci_upper']
            
            # Convert back to lists
            json_data[y_axis + '_fit'] = fit_array.tolist()
            json_data[y_axis + '_fit_lower'] = fit_lower_array.tolist()
            json_data[y_axis + '_fit_upper'] = fit_upper_array.tolist()

            # Add quality of fit metrics
            json_data[y_axis + '_r2'] = results.rsquared
            json_data[y_axis + '_pvalue'] = results.pvalues[1]
        return json_data

    def get_score_distribution(
        self,
        *,
        season_start: int,
    ):
        """
        Return the distribution of scores for a given season start.

        Args:
            season_start: Date object or integer representing the season
                start year. If integer, represents the year (e.g., 2021).

        Returns:
            Dictionary with score distribution data.
        """
        # Convert season_start to season string format (e.g., "2024-2025")
        season = (
            str(season_start) + '-' + str(season_start + 1)
        )

        # Use parameterized query to prevent SQL injection
        # This query calculates the frequency of each score combination
        # (e.g., "2-1", "0-0") across all matches in the season
        sql = """
        select
            league_tier,
            split_part(score, '-', 1) as home_goals,
            split_part(score, '-', 2) as away_goals,
            frequency
        from
            (
            -- Calculate frequency: count of each score / total matches in league
            select 
                league_tier,
                score,
                count(score)/league_size_matches::float as frequency
            from
                (
                -- Create score strings by concatenating home and away goals
                select
                    league_tier,
                    league_size_matches,
                    home_goals || '-' || away_goals as score
                from
                    football_match
                join
                    league
                on 
                    league.league_id = football_match.league_id
                where
                    season = %s
                ) as score
            group by
                league_size_matches,
                score.league_tier,
                score
            )
        """
        # Execute SQL query with parameterized season value
        with connection.cursor() as cursor:
            cursor.execute(sql, [season])
            # Convert query results to list of dictionaries
            columns = [col[0] for col in cursor.description]
            result = [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]
        # Transform query results into JSON-friendly format
        # Each key contains a list of values, one per score combination
        json_data: Dict[str, List[Any]] = {
            'league_tier': [
                int(row['league_tier']) if row['league_tier'] else 0
                for row in result
            ],
            'home_goals': [
                int(row['home_goals']) if row['home_goals'] else 0
                for row in result
            ],
            'away_goals': [
                int(row['away_goals']) if row['away_goals'] else 0
                for row in result
            ],
            'frequency': [
                float(row['frequency']) if row['frequency'] else 0
                for row in result
            ],
        }
        return json_data

class FootballMatch(models.Model):
    match_id = models.CharField(primary_key=True, max_length=255)
    league = models.ForeignKey('League', models.DO_NOTHING)
    match_date = models.DateField()
    match_time = models.CharField(max_length=255, blank=True, null=True)
    match_day_of_week = models.CharField(max_length=255)
    attendance = models.IntegerField(blank=True, null=True)
    home_club = models.CharField(max_length=255)
    home_goals = models.IntegerField()
    home_fouls = models.IntegerField(blank=True, null=True)
    home_yellow_cards = models.IntegerField(blank=True, null=True)
    home_red_cards = models.IntegerField(blank=True, null=True)
    away_club = models.CharField(max_length=255)
    away_goals = models.IntegerField()
    away_fouls = models.IntegerField(blank=True, null=True)
    away_yellow_cards = models.IntegerField(blank=True, null=True)
    away_red_cards = models.IntegerField(blank=True, null=True)

    objects = FootballMatchManager()

    class Meta:
        managed = False
        db_table = 'football_match'


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

    class Meta:
        managed = False
        db_table = 'league'
