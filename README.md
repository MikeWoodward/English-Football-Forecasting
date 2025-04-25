# Python-EPL-forecasting
Project to forecast EPL results. This is a work in progress.

This work is based on an earlier project I did in R. I had several goals here:
1. Use the project as a demo vehicle for using Cursor on a large machine learning project.
2. Add new data to the model.
3. More in-depth investigation of neural nets.

## Data Cleansing Challenges

This data set is a very difficult one to cleanse automatically. There are several oddities, for example:

* How to cope with "phoenix clubs". These are clubs that went bankrupt and then were revived. The rules are the team has to have a different name. In practice, teams that have gone bankrupt and then were revived take on a new name and a few years later petition for the old name back.
  * I considered phoenix clubs to be a continuation of the old club.

* How to cope with Wimbledon. Wimbledon moved to Milton Keynes in 2004 and changed their name to "Milton Keynes Dons". Fans in Wimbledon formed a new local team called "AFC Wimbledon". Both "Milton Keynes Dons" and "AFC Wimbledon" have played in the same league and played each other.
  * I considered pre-2004 Wimbledon, MK Dons, and AFC Wimbledon to be separate teams.

* Nicknames, abbreviations, and truncations. Manchester United is sometimes known as MUFC, Man United, Man Utd, and various variants.
  * I normalized the names using a name normalization table I created by hand.

* The league names have changed over the years, but the tiering hasn't.
  * I've used the tiering with the modern league names. This does yield some historical inconsistencies (there was no Premier League in 1890 for example), but it does keep the data set consistent.
