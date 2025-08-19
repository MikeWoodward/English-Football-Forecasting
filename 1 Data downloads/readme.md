# Data sources

On another page (https://github.com/MikeWoodward/English-Football-Forecasting/blob/main/Notes/data_sources.md), I've talked about data sources and the problems of getting good quality data. In this folder, I've stored the code for the data sources I've used.

* ENFA. This is the highest quality source. It's the top four tiers only, with no attendance data. It stops at the 2023-2024 season.
* EnglishFootballLeagueTables. Attendance data and results for the top four leagues. It's created by hand (!) so there are errors and inconsistencies in the HTML.
* FBREf. More restricted data set but good for filling in the gaps.
* Football-data. More restricted data set but good for filling in the gaps.
* Todor. Nice set of data for the National League but missing some recent results and missing attendance data.
* TransferMarkt-values. Club values, foreign players, etc. This data set only goes back to the early 2000s.
* The DataSourceCleanUp folder contains utilities used to check and clean up data.

The Python files in each folder are numbered in order of execution, so run file 1_ followed by file 2_ etc. The Python files are broken down into steps:

* Download. This is often scraping different web pages and can be a time costly process. For some sources, it can take several days to downlaod all the data.
* Process. Consolidates any downloaded data.
* Cleanse. Cleans data ready for use in teh Data Preparation step.

The exact steps and numbering will depend on the data sources.

# Batch processing

I've consolidated the processing and cleaning steps into a batch file called process.sh. 

The data download steps are too time-intenive for batch file processing to make sense.
