# Data sources for this project

## No (free) golden source

There's been a tremendous interest in modeling football data for some time now, so it's surprising how bad the free data sources are. 

* Many sources have incorrect data (date of match, goals scored) for historic matches (meaning, pre-WWII) and some even have incorrect match dates and results for matches since 2010.

* Many sources are incomplete, meaning they miss out matches and teams for some older seasons.

* Most sources exclude the National League (the fifth tier). This is still a professional league and matches can have attendances of several thousand. 

* Club names are inconsistently abbreviated or shortened.

* The same errors appear in multiple sources, suggesting a large amount of cutting-and-pasting. In other words, different sources are not always different.

## Quality checking methodology

I did two forms of quality checking: 

* Cross-checking sources against each other and manually checking the differences.
* Manually checking - meaning searching for the match on the internet. I considered some sources authoratative, e.g. old match programs, media reports, fan historic sites. Fortunately, I managed to find authoritative sources for every match.

## ENFA

This is the best data. I only found three errors in the entire data set: https://enfa.co.uk/. The data has been purchased by the English Football League and may be commercially available in late 2025.

## Football league web pages

This data looks very similar to the ENFA data set but it makes venue and attendance data freely available. https://www.englishfootballleaguetables.co.uk/

## Football club history

Clubs have merged, renamed themselves, gone bankrupt etc. etc. This site has helped me keep the naming straight: https://www.fchd.info/indexs.htm 

## Engsoccerdata

This is a set of data that James Curley has made available on GitHub: https://github.com/jalapic/engsoccerdata/tree/master/data-raw. It has fifth tier data. On the downside, I found a number of errors in the data.

## FBRef

This site is here: https://fbref.com/en/. Has data for the top four tiers. Has a number of date and result errors.

## Football-data

Located here: https://www.football-data.co.uk. This site has gambling data and red card, yellow card, and foul data. It includes the fifth tier.

## Football web pages

Located here: https://www.footballwebpages.co.uk. Limited data, but handily presented in CSV files. Data is incomplete, it misses matches and teams.

## todor66

Located here: http://todor66.com/football/England/. Limited time-scope, but includes the fifth tier.

## Transfermarkt

Located here: https://www.transfermarkt.com. Has match attendance figures etc. but suffers from correctness issues (results, dates), mostly for older matches, but some recentish issues too. It also has transfer values and hence estimates of the team values.

## World football

Located here: https://www.worldfootball.net. A mostly complete set of data but has the same date and score reliability issues.
