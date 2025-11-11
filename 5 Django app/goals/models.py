# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete`
#     set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to
#     create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values
# or field names.
from django.db import models


class AttendanceViolin(models.Model):
    attendance = models.DecimalField(
        max_digits=65535, decimal_places=65535, blank=True, null=True)
    probability_density = models.DecimalField(
        max_digits=65535, decimal_places=65535, blank=True, null=True)
    league_tier = models.IntegerField(blank=True, null=True)
    season_start = models.IntegerField(blank=True, null=True)
    league_id = models.CharField(max_length=255, blank=True, null=True)

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


class ClubMatch(models.Model):
    match_id = models.CharField(max_length=255)
    club_name = models.CharField(max_length=255)
    goals = models.IntegerField()
    red_cards = models.IntegerField(blank=True, null=True)
    yellow_cards = models.IntegerField(blank=True, null=True)
    fouls = models.IntegerField(blank=True, null=True)
    is_home = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'club_match'


class ClubSeason(models.Model):
    league_id = models.CharField(max_length=255)
    club_name = models.CharField(max_length=255)
    squad_size = models.IntegerField(blank=True, null=True)
    foreigner_count = models.IntegerField(blank=True, null=True)
    foreigner_fraction = models.DecimalField(
        max_digits=65535, decimal_places=65535, blank=True, null=True)
    mean_age = models.DecimalField(
        max_digits=65535, decimal_places=65535, blank=True, null=True)
    total_market_value = models.DecimalField(
        max_digits=65535, decimal_places=65535, blank=True, null=True)

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
    content_type = models.ForeignKey(
        'DjangoContentType', models.DO_NOTHING, blank=True, null=True)
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
    league_id = models.CharField(max_length=255)
    match_date = models.DateField()
    attendance = models.IntegerField()

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
