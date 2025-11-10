# Overview
Create a Django application called EnglishFootballLeagueAnalysis. It consists of four applications:
* About - a page that describes the whole application.
* Trends - that shows trends over time using charts. 
* Goals - showing factors that influence goals. 
* Admin - manages users. 

## Model
Connect to the existing Postgres Football database. The credentials are: 
'host': os.environ['FOOTBALL_HOST'],
'port': int(os.environ['FOOTBALL_PORT']),
'database': "Football",
'user': os.environ['FOOTBALL_USER'],
'password': os.environ['FOOTBALL_PASSWORD']
The Trends and Goals apps will use tables from this database.

## Trends app
This will use Bokeh to display charts based on data from the database tables. 
Include all Bokeh libraries necessary in the Python and HTML files.
The app will allow the user to select from a menu of different charts. Clicking on their selection will take the user to a web page showing that chart with some explanatory text.
Create two URLs showing one dummy Bokeh chart each and some explanatory text. Make sure the dummy charts are in the dialog box.
The app is only visible to logged in users.
There will be explanatory text on each page of the app.

## Goals app
This will use Bokeh to display charts based on data from the database tables. 
Include all Bokeh libraries necessary in the Python and HTML files.
The app will allow the user to select from a menu of different charts. Clicking on their selection will take the user to a web page showing that chart with some explanatory text.
Create two URLs showing one dummy Bokeh chart each and some explanatory text. Make sure the dummy charts are in the dialog box.
There will be explanatory text on each page of the app.

## About app
This will show some explanatory text about the whole app and provide links to login as a user or as an admin. 

## Admin app
This will allow admins to add and delete users.
Only logged in admin users can access the Admin pages.

## User login and logout 
There will be a page that allows users to login. A logged in user will be able to edit their data, e.g. change password. Once the user is logged in, a logout button will appear on the top right of all pages.

## Appearance
All text to be at least 12pt.
All text to be black.
Lines or other graphical elements are to be shades of green.

Use bootstrap.js where appropriate.

Use crispy forms.

The applications will be accessible from a navigation bar on the top of every page. The logout button will be part of this navigation bar.

Every page will have a footer with a copyright statement.

## Users
Create an admin user: username: "Falcon1234", password: "birdbrain".
Create a user: username: "Footsmall", password: "roundball".
Store user and admin data in the Postgres database. Create whatever tables you need to store user and admin data.