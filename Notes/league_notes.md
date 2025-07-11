# Points

The clubs in the leagues are ranked by their number of points. At the end of each season, the top teams in the league are eligible for promotion to the next league up, and the bottom teams might be relegated to the league below. Bear in mind, money is not equally divided, so promotion can have a massive financial boost and relegation has a massive financial penalty.

Up until the 1981 season, match points were awarded as follows:
* Loss: 0 points
* Draw: 1 point
* Win: 2 points  

In England, from 1981 onward, the system changed:
* Loss: 0 points
* Draw: 1 point
* Win: 3 points  

The intention of awarding 3 points was to encourage teams to go for a win rather than settling for a draw.

(Obviously, there's no promotion from the top league, but the top teams in the league play in the UEFA Champions League, a European-level club competition. This can be extremely lucrative as this league is the most watched in the world. In other words, there's a financial benefit to being at the top of the top league.)

# The English football league structure

English football has undergone a number of organizational changes over the years, including a number of confusing name changes. However, the basic structure has stayed the same: a hierarchical set of leagues with promotion and relegation between them. From 1920-1958, the third tier was split into a northern and southern league, but in 1958, these were merged into a new national third and fourth tier (1958-1959 season onwards). For this project, I only considered national leagues.

At the time of writing (mid-2025), there are five national professional leagues. Below these leagues are semi-professional regional leagues. The top league (the EPL) takes the lion's share of the available money and the money falls off the lower down the league system you go.

The table below is a simplified version of the league structure over time. Over the years, some teams have "resigned" or been expelled from the league mid-season, this means the number of teams per league per season changes. 

| Tier    | League name | Number of clubs | 
| -------- | ------- | ------- |
| 1  | 1888-1992 First Division</br>1992-1993 FA Premier League </br>1993-2001 FA Carling Premiership.</br>2001-2004 FA  FA Barclaycard Premiership</br> 2004-2007 Barclays Premiership</br>2007-2016 Barclays Premier League</br>  2016- Premier League |  1888-1891 12</br> 1891-1892 14</br>1892-1898 16</br>1898-1904 18</br>1904-1915 20</br>1919-1939 22<br>1946-1987 22<br>1987-1988 21</br> 1988-1991 20</br>1991-1992 22</br>  1992-1995 22</br> 1995-onwards 20 | 
| 2 | 1892-1992 Football League Second Division</br>1992-2004 Football League First Division</br>2004-2016 Football League Championship<br>2016- EFL Championship | 1892-1893: 12 </br>1893-1898: 16 </br>1898-1905: 18 </br>1905-1915: 20 </br>1919-1987: 22 </br>1987-1988: 23 </br>1988-onwards 24 | 
| 3 | 1958-1992: Football League Third Division</br>1992-2004: Football League Second Division</br>2004-2015: Football League One</br>2016 - EFL League One| 1950-2019: 24 clubs</br>2019-2020: 23 clubs (Bury FC expelled)</br>2020-present: 24 clubs</br>| 
| 4 | 1958-1992: Football League Fourth Division</br>1992-2004: Football League Third Division</br>2004-2016: Football League Two</br>2016-: EFL League Two | 1958-1991: 24 clubs </br>1991-1992: 22 clubs </br>1992-onwards 24 clubs | 
| 5 | 1979-1984: Alliance Premier League</br>1984-1987: Gola League</br>1987-1997: Vauxhall Conference</br>1997-2002: Football Conference</br>2002-2006: Nationwide Conference</br>2006-2007: Conference National</br>2007-2011: Blue Square Premier</br>2011-2013: Blue Square Bet Premier</br>2013-2014: Skrill Premier</br>2014-2015: Vanarama Conference</br>2015-2024: Vanarama National League| 1979-2006 22</br>2006-2009 24</br>2009-2010 23</br>2010-onwards 24| 

# Oddities

In the 1919-1920 season, Leeds City were expelled from the second division mid-season and replaced by Port Vale. Port Vale "inherited" Leeds City's results. Because I'm training a model, I'm going to treat this as a league of 23 teams and treat Port Vale and Leeds City seprately. 

Matches were suspended during most of the First and Second World War. During the Second World War, matches were played, but with significant changes: players changed teams (or went off to war), and matches were limited to a 50 mile radius. The league proper wasn't resumed until 1946.

The 2019-2020 season was badly affected by COVID. Games were suspended for most of March 2020 and resumed behind closed doors. As a consequence, the season went on much longer than usual. The EPL and Championship (tiers 1 and 2) played out a full season, but League One and Two (tiers 3 and 4) ended their season early, which meant some games were not played. Promotion and relegation rules were a little diffeernt for this season.

A number of teams have gone bankrupt which is a breach of Football Association rules. In most cases, these teams have been resurrected under new names (so-called phoenix clubs), and again in most cases, these teams have reclaimed their old names after a few years. There have been mergers between teams, though this was largely restricted to the lower leagues.

The Football Association (FA) has penalized clubs for breach of its financial rules and several other issues. These penalties have been fines and/or points deductions. In a few cases (most notably, Dover Athletic), the FA has "canceled" match results, and in a few cases, the FA has awarded the match points to a club even though the match wasn't played.

# Notes

I removed Dover Athletic for the 2020-2021 season (complex story, but they only played part of the season).

I've used the "traditional" names for Phoenix clubs.

Gravesend & Northfleet changed their name to Ebbsfleet United in 2007, so I've used the modern name from the club formation in 1946.

On 2019-04-17, a match was scheduled to take place between Bolton Wanderers and Brentford. Unfortunately, the Bolton players hadn't been paid, so they refused to play. The match was called off. Although the match was originally going to be rescehduled, the Football Association (FA) awarded the match to Brentford 1-0 without it being played. I've chosen to keep the score in the data even though the match wasn't played. I've done this for simplicity.

Over the years, the FA has deducted points from teams for a range of issues, mostly involving financial issues. In my analysis, I've not included these point deductions because they reflect off-the-field issues.
