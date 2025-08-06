# Data sources

On another page (https://github.com/MikeWoodward/English-Football-Forecasting/blob/main/Notes/data_sources.md), I've talked about data sources and the problems of getting good quality data. In this folder, I've stored the code for the data sources I've used.

* ENFA. This is the highest quality source. It's the top four tiers only, with no attendance data. It stops at the 2023-2024 season.
* EnglishFootballLeagueTables. Attendance data and results for the top four leagues. It's created by hand (!) so there are errors and inconsistencies in the HTML.
* FBREf. More restricted data set but good for filling in the gaps.
* Football-data. More restricted data set but good for filling in the gaps.
* Todor. Nice set of data for the National League but missing some recent results and missing attendance data.
* TransferMarkt-vales. Club values, foreign players, etc. This data set only goes back to the early 2000s.
* The DataSourceCleanUp folder contains utilities used to check and clean up data.
