
"""## **1. IMPORTS, CONSTANTS AND FUNCTIONS**"""
# This is where all the imports, constants and functions will be stored for the project.

"""### **1.1 Imports**"""

import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import re
from time import sleep
from datetime import datetime, date
from tqdm import tqdm_notebook
import math
import random
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm
from matplotlib.colors import Normalize
# from sqlalchemy import create_engine
# from sqlalchemy import text
# import sqlite3
from flask import Flask, request, jsonify


"""### Create Flask Application"""
app = Flask(__name__)

"""### **1.2 Constants**"""


USER_AGENT = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
}

HEADERS = {
    'authority': 'api.sofascore.com',
    'accept': '*/*',
    'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    'cache-control': 'max-age=0',
    'if-none-match': 'W/"0839132050"',
    'origin': 'https://www.sofascore.com',
    'referer': 'https://www.sofascore.com/',
    'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'If-Modified-Since' : 'Tue, 13 Feb 2024 00:00:00 GMT'
}

# Brighton's team_id is 30, Sheffield United's team_id is 15
TEAM_NAMES_AND_IDS = (('Brighton And Hove Albion', 30), ('Sheffield United', 15))

engine = create_engine('sqlite:///fall_from_grace.db')

"""### **1.3 Utility Functions**"""

"""# UTILITY FUNCTIONS"""
# Convert to lowercase
def string_to_slug(text):
    slug = text.lower()
    # Replace spaces with hyphens
    slug = slug.replace(' ', '-')
    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    return slug

# Convert slug into title case
def slug_to_string(slug_text):
    # Split the slug text by '-'
    words = slug_text.split('-')

    # Capitalize each word and join them with a space
    title_case_text = ' '.join(word.capitalize() for word in words)

    return title_case_text

# Unix timestamp conversion
def unix_time_to_date(timestamp):
  # Convert Unix timestamp to datetime object
  dt_object = datetime.fromtimestamp(timestamp)

  # Format the datetime object as a string
  formatted_date = dt_object.strftime("%d-%b-%Y")

  return formatted_date

# Using poisson distribution to calculate probability fo home team and away team scoring x number of goals
def factorial(x):
  # When we get to x = 1 or 0, just return one as the thing to be multiplied by the other numbers
  if x == 0 or x == 1:
        return 1
  # Else return the multiplication of x and x-1
  return x * factorial(x - 1)

# Poisson Distribution Formula for likelihood of a team scoring x number of goals
def poisson_distribution(rate, x):
  E = 2.718
  return (rate ** x) * (E ** -rate)/ factorial(x)

# Convert strings into param strings, i.e. instead of 'Moises Caicedo', you'd have 'moises+caicedo'
def str_param(str):
  return '+'.join(str.split(' ')).lower()

"""## **2. Data Extraction**

The data is extracted from the [Understat.com](https://understat.com/) website, which is a website containing statistics about the major footballing leagues in Europe.

### **2.1 Fetch Data from Understat**
"""

# Get the understat league data
def get_understat_league_data(league_name, print_options=False):
  leagues = {
      'EPL' : 'EPL',
      'La Liga' : 'La_liga',
      'Bundesliga' : 'Bundesliga',
      'Serie A' : 'Serie_A',
      'Ligue 1' : 'Ligue_1'
  }

  # Make fetch request to website
  understat_res = requests.get(f"https://understat.com/league/{leagues[league_name]}/2023")

  # Check status code
  status_code = understat_res.status_code
  if status_code == 200:
    # Parse using beautiful soup
    soup = BeautifulSoup(understat_res.content, 'html.parser')

    # Get data from the script it's stored in
    scripts = soup.find_all('script')
    print(f"There are {len(scripts)} scripts. \n" if understat_res.status_code == 200 else f'Wasn\'t able to scrape data, status code returned was {understat_res.status_code} \n')

    # The data is in the third script tag
    print("The data is in the third script tag:")
    print(scripts[2], end='\n\n')

    # Convert the script into a string, and then convert that string into a json object
    strings = scripts[2].string
    print("Data as a string: \n" + strings.strip(), end='\n\n')

    # Remove unneccessary symbols so we only have JSON data
    #ind_start is the index to start the slice from, ind_end is the index we want to end the slice before
    ind_start = strings.index("('") + 2
    ind_end = strings.index("')")

    json_data = strings[ind_start:ind_end]
    json_data = json_data.encode('utf8').decode('unicode_escape')

    understat_data = json.loads(json_data)

    # Print data and return it
    if print_options:
      print("JSON Object: \n",  understat_data)
    return(understat_data)
  else:
    print('Error occured with status code:', status_code)

# get_understat_league_data('EPL')

"""### **2.2 Convert Data from String to JSON Object**

### **2.3 Enrich data with SofaScore team ids**
In order to make predictions about the resulting tables, we need access to the remaining fixtures. [Sofascore.com](https://www.sofascore.com/), a similar web service to to that of Understat, but offers a slightly easier format for collecting fixtures data.
"""

def get_sofascore_data(league_name, print_options=False):
  # The ids for each league is required in the url for the league table
  leagues = {
      'EPL' : {
          'country' : 'england',
          'league' : 'premier-league',
          'id': 17
      },
      'La Liga' : {
          'country' : 'spain',
          'league': 'laliga',
          'id' : 8
      },
      'Bundesliga' : {
          'country' : 'germany',
          'league' : 'bundesliga',
          'id' : 35
      },
      'Serie A' : {
          'country' : 'italy',
          'league': 'serie-a',
          'id': 23
      },
      'Ligue 1' : {
          'country' : 'france',
          'league': 'ligue-1',
          'id' : 34
      }
  }

  # Params necessary for initial web scrape
  country_name, league, league_id = leagues[league_name]['country'], leagues[league_name]['league'], leagues[league_name]['id']

  # Get the season id from the script, so that we can access the api
  get_script_url = f"https://www.sofascore.com/tournament/football/{country_name}/{league}/{league_id}"

  # Get the ids for each team from sofascore so we can fetch their remaining fixtures from sofascore later
  sofascore_res = requests.get(get_script_url, headers=HEADERS)
  sofascore_soup = BeautifulSoup(sofascore_res.content, 'html.parser')
  # Scripts
  text_with_season_id = sofascore_soup.find('script', {'id' : '__NEXT_DATA__'}).text
  json_with_season_id = json.loads(text_with_season_id)
  # season_id = json_with_season_id['props']['seasons'][0]['id']
  season_id = json_with_season_id['props']['pageProps']['seasons'][0]['id']

  # Get all the teams from the returned JSON object
  api_url = f"https://api.sofascore.com/api/v1/unique-tournament/{league_id}/season/{season_id}/standings/total"
  api_res = requests.get(api_url, headers=HEADERS)
  sofascore_data = api_res.json()['standings'][0]['rows']

  # # Create a dataframe with all the teams
  sofascore_df = pd.DataFrame(columns=['team', 'sofascore_team_id', 'team_name'], data=sofascore_data).sort_values(by='team_name')

  # Update the sofascore team id and team name so that it includes the appropriate data instead of NaN
  sofascore_df['sofascore_team_id'] = sofascore_df['team'].apply(lambda x : x['id'])
  sofascore_df['team_name'] = sofascore_df['team'].apply(lambda x : x['name'])

  # Drop the team column as it's no longer needed
  sofascore_df.drop(columns=['team'], inplace=True)

  # Update some team names coming from Sofascore to match the ones that came from Understat
  # This includes all the possible teams that could play in each league
  team_names_map = {
      # This list is not exhaustive and may need to be updated
      'EPL' : {
        'Brighton & Hove Albion' : 'Brighton',
        'Luton Town' : 'Luton',
        'Tottenham Hotspur' : 'Tottenham',
        'West Ham United' : 'West Ham',
        'Wolves' : 'Wolverhampton Wanderers',
        'Leeds United' : 'Leeds',
        'Leicester City': 'Leicester',
        'Norwich City'  : 'Norwich',
        'Cardiff City'  : 'Cardiff',
        'Huddersfield Town'  : 'Huddersfield',
        'Swansea City'  : 'Swansea',
        'Stoke City'  : 'Stoke',
        'Hull City' : 'Hull',
        "Parma" : "Parma Calcio 1913"
      },
      'Bundesliga': {
          "Bayer 04 Leverkusen" : "Bayern Leverkusen",
          "RB Leipzig" : "RasenBallsport Leipzig",
          "SV Werder Bremen" : "Werder Bremen",
          "SC Freiburg" : "Freiburg",
          "TSG Hoffenheim" : "Hoffenheim",
          "VfL Wolfsburg" : "Wolfsburg",
          "VfL Bochum 1848" : "Bochum",
          "1. FC Heidenheim" : "FC Heidenheim",
          "1. FSV Mainz 05" : "Mainz 05",
          "1. FC Köln": "FC Cologne",
          "1. FC Union Berlin": "Union Berlin",
          "FC Augsburg": "Augsburg",
          "FC Bayern München": "Bayern Munich",
          "FC Ingolstadt 04": "Ingolstadt",
          "Borussia M'gladbach": "Borussia M.Gladbach",
          "Hertha BSC": "Hertha Berlin",
          "FC Schalke 04" : "Schalke 04",
          "SpVgg Greuther Fürth": "Greuther Fuerth",
          "SC Paderborn 07": "Paderborn",
          "Fortuna Düsseldorf" : "Fortuna Duesseldorf",
          "1. FC Nürnberg": "Nuernberg",
          "Darmstadt 98": "Darmstadt",
      },
      'Serie A': {
        "Milan" : 'AC Milan',
        "Hellas Verona" : "Verona",
        "SPAL" : "SPAL 2013",
        "ChievoVerona": "Chievo"
      },
      'La Liga': {
          '' : ''
      },
      'Ligue 1': {
          'Paris Saint-Germain' : 'Paris Saint Germain',
          'AS Monaco': 'Monaco',
          'Saint-Étienne' : 'Saint-Etienne',
          'RC Strasbourg' : 'Strasbourg',
          'Stade de Reims' : 'Reims',
          'Olympique Lyonnais': 'Lyon',


      },
      }
  sofascore_df['team_name'] = sofascore_df['team_name'].replace(team_names_map[league_name])
  
  # Print Dataframe and return it 
  if print_options: 
     print(sofascore_df)
  return sofascore_df

get_sofascore_data('Bundesliga', True)

# Test
@app.route("/")
def home():
  return json.dumps({
        'Brighton & Hove Albion' : 'Brighton',
        'Luton Town' : 'Luton',
        'Tottenham Hotspur' : 'Tottenham',
        'West Ham United' : 'West Ham',
        'Wolves' : 'Wolverhampton Wanderers',
        'Leeds United' : 'Leeds',
        'Leicester City': 'Leicester',
        'Norwich City'  : 'Norwich',
        'Cardiff City'  : 'Cardiff',
        'Huddersfield Town'  : 'Huddersfield',
        'Swansea City'  : 'Swansea',
        'Stoke City'  : 'Stoke',
        'Hull City' : 'Hull',
        "Parma" : "Parma Calcio 1913"
      })


#--- Code should be above this line---
# # Run server
# if __name__ == "__main__": 
#    app.run(debug=True)

# Production server
# More on it here: 
# https://stackoverflow.com/questions/51025893/flask-at-first-run-do-not-use-the-development-server-in-a-production-environmen
# if __name__ == "__main__":
#     from waitress import serve
#     serve(app, host="0.0.0.0", port=8080)