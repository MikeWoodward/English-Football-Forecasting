# General comments

Gathering and consolidating English football data is fraught with difficulties:
* Data sources are partial and miss years/leagues/matches.
* Data sources contain errors, for example, incorrect match results.
* The data itself is problemtic, e.g. phoenix clubs, canceled matches, patchy attendance figures etc.

# Incorrect data

For this project, I've taken data from multiple sources. Where the fields contain the same data, I compare the values and flag any differences for resolution by hand.

# Structural issues

## Phoenix clubs

These are clubs that went bankrupt and then were revived. The rules are the team has to have a different name when it's "reborn". In practice, teams that have gone bankrupt and then were revived take on a new name and a few years later petition for their old name back.
	 - I considered phoenix clubs to be a continuation of the old club.

## Wimbledon

Wimbledon moved to to Milton Keynes in 2004 and changed their name to "Milton Keynes Dons". Fans in Wimbledon formed a new local team called "AFC Wimbledon". Both "Milton Keynes Dons" and "AFC Wimbledon" have played in the same league and played each other.
  - I considered pre-2004 Wimbledon, MK Dons, and AFC Wimbledon to be separate teams.

## Nicknames, abbreviations, and old names

Manchester United is sometimes known as MUFC, Man United, Man Utd, and various variants.
  -  I normalized the names using a name normalization table I created by hand.

Sheffield Wednesday was intially known as "The Wednesday". I call the team "Sheffield Wednesday" for itw s entire life.
 
## League names

English football since the early 1990s has had a convoluted history of renaming leagues. The league tiering remains the same, but the names of the tiers have changed. This is ultimately driven by money (e.g. naming rights).  
  -  I've used the tiering with the modern league names. This does yield some historical inconsistencies (there was no Premier League in 1890 for example), but it does keep the data set consistent.

## Canceled games

Some games were canceled but a score awarded and some games were played but the score didn't count. These kinds of fun and games happened around COVID. In a few odd cases teams refused to play, so the match was awarded against them without being played. In other cases, the match was played but the results canceled (e.g. [Dover Athletic](https://en.wikipedia.org/wiki/Dover_Athletic_F.C.)).
  - Where the game was not played but a score awarded, I ignored the match.
  - Where the game was played but the result later canceled, I included the match.

## Attendance figures patchy in the early days of the leagues

Some data sources are missing attendance figures for both historic and more modern matches. I filled in the gaps manually from a variety of sources, including individual club records. In only one case (an 1890 match) did I need to use an average figure. The attendance figures for some of the older games are plainly estimates; record keeping wasn't great at the end of the 19th century.

## Other changes

I removed Dover Athletic for the 2020-2021 season (complex story, but they only played part of the season).

I've used the "traditional" names for Phoenix clubs.

Gravesend & Northfleet changed their name to Ebbsfleet United in 2007, so I've used the modern name from the club formation in 1946.
