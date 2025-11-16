Create new app called 'Club Analysis'. For now, it will consist of a single page called "club analysis". 

* When the user first goes to the club analysis page, they will see a message to select a club and a dropdown box listing all the clubs. The club names will come from the database table club_history and will be the field "club_name". The clubs will be in alphabetical order.

* Once the user selects a club, these actions will occur:

    * A message will appear saying something like "You have selected the club X", where X is the club name. Z will appear in bold.
    * A table will appear showing data from the database table club_history. The table will have these columns: year (corresponding to year_changed), club name, modern name (corresponding to modern_name), nickname, event (corresponging to note), wikipedia link (corresponding to wikipedia). The table will be sorted by increasing year.
    * A bar chart. The bar chart will show league tier on the y axis and season start on the x axis. Season start is int(season[0:4]). The data is a bit more complex, so pay attention to the next sentences. Look up the modern_name using the club_name. Get all names the club has had (all club_names matching modern_name). Join the table league to club_season, look up all the club_names and get the corresponding league_tiers and seasons.  Return the following data: club_name, season_start, league_tier. Sort the data by season_start. 
    * Tables of all matches played by the club. There will be one table per season. The tables will have the following columns: Season, Match Date, League Tier, Home Club, Away Club, Home Goals, Away Goals. Above each table will be a heading saying "Matches for club X for season Y", where X is the club_name and Y is the season. Here's how to get the data, pay attention because this is difficult. Get all names the club has been known by (see previous instruction). Join the table football_match to the table league. Fom this combined table, select all matches where club_names match the home club and the away club. Sort the data by season and match date.

Under League Tier over time, have the following HTML: paragraph. "Football was suspended during World War I and World War II".

The bar chart of "League Tier Over Time" is to use light green bars and have the same color line.

Add clubs_analysis to the menu bar and the Quick Access box on the landing page.

If the user selects another club from the drop down box, redraw the web page.

Use the Django ORM where possible and avoid the use of SQL queries. Avoid aggegating aggregations.
