# The Relationship Between Disney Musicals' Soundtrack Popularity and Movie Performance (WIP)

A project aiming to relate the popularity of Disney movies' (musicals only) soundtracks on Spotify, with their rating/profit from IMDb. All data sourced by Spotify API calls (w/ requests library) and IMDb web scraping (w/ Selenium).

The repository is primarily split into `py funcs`, `ipynb funcs` and `report` which serve as follows. 

## `py funcs` and `ipynb funcs`

These two folders contain the methodology and code for attaining the data and are largely similar with the exception that the .ipynb files contain a lot of walking through the individual steps and reasoning along the way in markdown. The .py files are mostly just the final results and functions stemming from the work done in the .ipynb ones. Running either should return the same results (in terms of creating the relevant .csv files).

## `data`
As the files are not too large, I decided to upload them if you wanted to skip the data-fetching process. However, running files from either of the above folders should create the data folder and content automatically.

## `report`
Visualisations and findings are reported in .ipyb files in the `report` folder. This is where also where a lot of table joins are made in preparation for the report-writing.


## Tableau 
A link to interactive Tableau dashboards with insights can also be found here: [link](https://public.tableau.com/views/DisneyWIP/Dashboard2?:language=en-GB&:display_count=n&:origin=viz_share_link). This is slightly less comprehensive than the report (as it's just quick insights) but I decided to include them just for demonstration of Tableau competency.
