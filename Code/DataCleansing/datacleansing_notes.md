# Data Cleansing comments

There are 

* How to cope with "phoenix clubs". These are clubs that went bankrupt and then were revived. The rules are the team has to have a different name. In practice, teams that have gone bankrupt and then were revived take on a new name and a few years later petition for the old name back.

I didn't use AI for this. Where there were very similar club names, I resolved the issue by hand.

* How to cope with Wimbledon. Wimbledon moved to to Milton Keynes in 2004 and changed their name to "Milton Keynes Dons". Fans in Wimbledon formed a new local team called "AFC Wimbledon". Both "Milton Keynes Dons" and "AFC Wimbledon" have played in the same league and played each other.

I didn't use AI for this, I resolved the issue by hand.

* Nicknames, abbreviations, and truncations.  Manchester United is sometimes known as MUFC, Man United, Man Utd, and various variants.

Because I know the team names and abbreviations, I resolved the issue by hand. As a trial, I asked Cursor to give me alternative names for the 1880's club, "The Wednesday". It couldn't process the query.

* The league names have changed over the years but the tiering hasn't.

I used the modern league names and kept the 
