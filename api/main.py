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
from flask import Flask, request, jsonify
import json
import functions as f


"""### Create Flask Application"""
app = Flask(__name__)


from constants import HEADERS, TEAM_NAMES_MAP
import utilities as u
"""## **1. IMPORTS, CONSTANTS AND FUNCTIONS**"""
# This is where all the imports, constants and functions will be stored for the project.


"""## **2. Data Extraction**

The data is extracted from the [Understat.com](https://understat.com/) website, which is a website containing statistics about the major footballing leagues in Europe.

### **2.1 Fetch Data from Understat**
"""

# 1. Get the understat league data
def get_understat_league_json_data(league_name, print_options=False):
  # la liga is la_liga in understat url
  if league_name =='laliga': 
    league_name = 'la_liga'
  # Make fetch request to website
  understat_res = requests.get(f"https://understat.com/league/{league_name}")

  # Check status code
  status_code = understat_res.status_code
  if status_code == 200:
    # Parse using beautiful soup
    soup = BeautifulSoup(understat_res.content, 'html.parser')

    # Get data from the script it's stored in
    scripts = soup.find_all('script')
    if print_options:
      print(f"There are {len(scripts)} scripts. \n" if understat_res.status_code == 200 else f'Wasn\'t able to scrape data, status code returned was {understat_res.status_code} \n')

    # The data is in the third script tag
    if print_options:
      print("The data is in the third script tag:")
      print(scripts[2], end='\n\n')

    # Convert the script into a string, and then convert that string into a json object
    strings = scripts[2].string
    if print_options:
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

"""### **2.2 Convert Data from String to JSON Object**

### **2.3 Enrich data with SofaScore team ids**
In order to make predictions about the resulting tables, we need access to the remaining fixtures. [Sofascore.com](https://www.sofascore.com/), a similar web service to to that of Understat, but offers a slightly easier format for collecting fixtures data.
"""

def get_sofascore_df_data(league_name, print_options=False):
  # The ids for each league is required in the url for the league table
  leagues = {
      'epl' : {
          'country' : 'england',
          'league' : 'premier-league',
          'id': 17
      },
      'laliga' : {
          'country' : 'spain',
          'league': 'laliga',
          'id' : 8
      },
      'bundesliga' : {
          'country' : 'germany',
          'league' : 'bundesliga',
          'id' : 35
      },
      'serie_a' : {
          'country' : 'italy',
          'league': 'serie-a',
          'id': 23
      },
      'ligue_1' : {
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
  sofascore_df['team_name'] = sofascore_df['team_name'].replace(TEAM_NAMES_MAP[league_name])
  
  # Print Dataframe and return it 
  if print_options: 
     print(sofascore_df)
  return sofascore_df

"""## **3. Monte Carlo Simulation**"""
# This section of the project looks at how the league table is likely to end up based on each team's current run of form. Of course, like most models, there are a number of unforseeable factors which limit the accuracy of the predictions, such as player availability, changes in coaching staff, and player/team morale. Nonetheless the simulation does provide a good basis for estimating (ceteris paribus) what the league table might end up looking like, and provide motive for the remainder of the project.

"""### **3.1 Home vs. Away Stats**"""
# Teams perform differently at home vs playing at other stadiums, so the stats for home and away games will be divided into two dataframes to ensure that we capture this nuance.

def get_current_league_table_df_data(league_name):
  # Get understat and sofascore data with stats and ids
  understat_json = get_understat_league_json_data(league_name)
  sofascore_df = get_sofascore_df_data(league_name)
  
  home_league_table_data = []
  away_league_table_data =[]

  # The team_ids are the keys for each team's dictionary, construct a list of these ids
  TEAM_IDS = (team for team in understat_json)  

  # For each team do an accumulative value for matches, wins, draws, losses, etc.
  for id in TEAM_IDS:
    team_data = understat_json[id]
    # Get the home team_data
    home_team_data = {
        'team_id' : int(id),
        'team_name' : team_data['title'],
        'M': 0,
        'W': 0,
        'D' : 0,
        'L': 0,
        'G': 0,
        'GA': 0,
        'PTS': 0,
        'xG': 0,
        'xGA': 0,
        'xPTS': 0,
    }
    away_team_data = {
        'team_id' : int(id),
        'team_name' : team_data['title'],
        'M': 0,
        'W': 0,
        'D': 0,
        'L': 0,
        'G': 0,
        'GA': 0,
        'PTS': 0,
        'xG': 0,
        'xGA': 0,
        'xPTS': 0,
    }
    # if it's a home game add to the rolling average / sum for the home object for the team
    # For each team, get their home and away stats
    for game in team_data['history']:
      # If home game update home_team_stats
      if game['h_a'] == 'h':
        home_team_data['M'] += 1
        home_team_data['W'] += 1 if game['result'] == 'w' else 0
        home_team_data['D'] += 1 if game['result'] == 'd' else 0
        home_team_data['L'] += 1 if game['result'] == 'l' else 0
        home_team_data['G'] += game['scored']
        home_team_data['GA'] += game['missed']
        home_team_data['PTS'] += game['pts']
        home_team_data['xG'] += game['xG']
        home_team_data['xGA'] += game['xGA']
        home_team_data['xPTS'] += game['xpts']
      else:
        away_team_data['M'] += 1
        away_team_data['W'] += 1 if game['result'] == 'w' else 0
        away_team_data['D'] += 1 if game['result'] == 'd' else 0
        away_team_data['L'] += 1 if game['result'] == 'l' else 0
        away_team_data['G'] += game['scored']
        away_team_data['GA'] += game['missed']
        away_team_data['PTS'] += game['pts']
        away_team_data['xG'] += game['xG']
        away_team_data['xGA'] += game['xGA']
        away_team_data['xPTS'] += game['xpts']

    home_league_table_data.append(home_team_data)
    away_league_table_data.append(away_team_data)
    
  # Checking home and away league tables (passed)
  # h_df = pd.DataFrame(away_league_table_data)
  # a_df = pd.DataFrame(away_league_table_data)
  # print(h_df)

  columns = ['team_id', 'team_name','M', 'W','D','L', 'G', 'GA', 'PTS', 'xG', 'xGA', 'xPTS']
  home_df = pd.DataFrame(columns=columns, data=home_league_table_data).sort_values(by='team_name')
  away_df = pd.DataFrame(columns=columns, data=away_league_table_data).sort_values(by='team_name')

  # Add sofascore ids from previous table
  home_df = pd.merge(home_df, sofascore_df, on='team_name').sort_values(by='PTS', ascending=False)
  away_df = pd.merge(away_df, sofascore_df, on='team_name').sort_values(by='PTS', ascending=False)

  """### **3.2 Goals Per Game (GPG) Scored & Conceded**"""
  """This Monte Carlo simulation relies on heavily on the idea of how many goals a team is projected to score and condede. The first step towards those values is getting the average goals scored and conceded - **gpg (goals per game) scored and the gpg conceded.**"""

  # Add two columns to the df 'goals scored per game' and 'goals conceded per game'
  home_df['gpg scored'] = home_df['G']/home_df['M']
  home_df['gpg conceded'] = home_df['GA']/home_df['M']

  away_df['gpg scored'] = away_df['G']/away_df['M']
  away_df['gpg conceded'] = away_df['GA']/away_df['M']

  return home_df, away_df

def get_avg_gpg_dict(home_df, away_df):
  """### **3.3 League average GPG scored and conceded.**"""
  # Home teams
  # Add average goals per home team and goals per away team in the dfs and
  # then divide it by the number of teams in the league
  num_of_teams = len(home_df)
  home_avg_goals_per_game_scored = sum(home_df['gpg scored'])/num_of_teams
  home_avg_goals_per_game_scored

  # Away teams
  home_avg_goals_per_game_conceded = sum(home_df['gpg conceded'])/num_of_teams
  home_avg_goals_per_game_conceded

  away_avg_goals_per_game_scored = sum(away_df['gpg scored'])/num_of_teams
  away_avg_goals_per_game_scored

  # Add average goals per game conceded for
  away_avg_goals_per_game_conceded = sum(away_df['gpg conceded'])/num_of_teams
  away_avg_goals_per_game_conceded

  avg_gpg = {
      'total avg home gpg scored': home_avg_goals_per_game_scored,
      'total avg home gpg conceded': home_avg_goals_per_game_conceded,
      'total avg away gpg scored': away_avg_goals_per_game_scored,
      'total avg away gpg conceded': away_avg_goals_per_game_conceded
  }

  return avg_gpg

"""### **3.4 Functions for Monte Carlo Simulation**"""
# Along with the overall averages we also want to get the gpgs for each team
# This function allows us to get metrics for any given team from either the home_df or away_df
"""Some Utility functions"""
def find_team_metric(ha, team_name, metric, home_df, away_df):
  # NOTE: ha = home_or_away
  # If home pull the data from the home df
  if ha == 'home': return home_df[home_df['team_name'] == team_name][metric].iloc[0]
  # Otherwise pull the data from the away df
  else: return away_df[away_df['team_name'] == team_name][metric].iloc[0]

# Get all the remaining matchups for a given team
def get_fixtures(sofascore_id, print_options=False):
  fixtures_res = requests.get(f'https://api.sofascore.com/api/v1/team/{sofascore_id}/events/next/0', 
  headers=HEADERS)
  fixtures_data = fixtures_res.json()['events']
  # Only return dictionaries pertaining to Premier League games
  games_left = []
  for fixture in fixtures_data:
    # only return games for the appropiate league
    home_team = fixture['homeTeam']['name']
    away_team = fixture['awayTeam']['name']
    tournament = fixture['tournament']['name']
    # Store in data dict
    data = {
        'tournament': tournament,
        'home_team': home_team,
        'away_team': away_team,
    }
    # Append to games_list
    games_left.append(data)
    
  fixtures_df = pd.DataFrame(games_left)
  # Rename teams to match understat table
  # EPL
  list_of_fixtures = [tournament_dict['tournament']['name'] for tournament_dict in fixtures_data]
  if 'Premier League' in list_of_fixtures:
    fixtures_df = fixtures_df.replace(TEAM_NAMES_MAP['epl'])
    # Drop any rows that hold data about games outside of the Premier League
    fixtures_df = fixtures_df[fixtures_df['tournament'] == 'Premier League']
  elif 'Bundesliga' in list_of_fixtures:
    fixtures_df = fixtures_df.replace(TEAM_NAMES_MAP['bundesliga'])
    # Drop any rows that hold data about games outside of the Bundesliga
    fixtures_df = fixtures_df[fixtures_df['tournament'] == 'Bundesliga']
  elif  'Ligue 1' in list_of_fixtures:
    fixtures_df = fixtures_df.replace(TEAM_NAMES_MAP['ligue_1'])
    # Drop any rows that hold data about games outside of the Ligue 1
    fixtures_df = fixtures_df[fixtures_df['tournament'] == 'Ligue 1']
  elif 'LaLiga' in list_of_fixtures:
    fixtures_df = fixtures_df.replace(TEAM_NAMES_MAP['laliga'])
    # Drop any rows that hold data about games outside of the LaLiga
    fixtures_df = fixtures_df[fixtures_df['tournament'] == 'LaLiga']
  elif 'Serie A' in list_of_fixtures:
    fixtures_df = fixtures_df.replace(TEAM_NAMES_MAP['serie_a'])
    # Drop any rows that hold data about games outside of the Serie A
    fixtures_df = fixtures_df[fixtures_df['tournament'] == 'Serie A']
  # Return the list of the remaining games
  return fixtures_df.to_dict('records')

def who_wins(home_win, away_win, draw, HOME_TEAM, AWAY_TEAM):
  if home_win > away_win :
    if home_win > draw: return HOME_TEAM
    else: return 'DRAW'
  elif away_win > home_win:
    if away_win > draw: return AWAY_TEAM
    else: return 'DRAW'

def points_from_game(team_name, result):
  # result = the team who won, or if it's a draw then just 'DRAW'
  # If they won give them 3 points
  if result == team_name:
    return 3
  # If they drew give them 1 point
  elif result == 'DRAW':
    return 1
  # If they lost give them 0 points
  else:
    return 0
  
"""### **3.5 Monte Carlo Algorithm**"""
# MONTE CARLO SIMULATION FUNCTION

## STEP 1 | CHOOSE TEAMS & GET HOME AND AWAY PROJECTED GOALS
# You can put it in any two teams and see whose likely to win
def monte_carlo(home_team, away_team, avg_gpg, home_df, away_df, print_options=False):
  HOME_TEAM = home_team
  AWAY_TEAM = away_team

  attack_def_n_proj = {
      'projected_home_goals': find_team_metric('home', HOME_TEAM, 'gpg scored', home_df, away_df),
      'projected_away_goals': find_team_metric('away', AWAY_TEAM, 'gpg scored', home_df, away_df),

      'home_attack': find_team_metric('home', HOME_TEAM, 'gpg scored', home_df, away_df)/avg_gpg['total avg home gpg scored'],
      'away_defence': find_team_metric('away', AWAY_TEAM, 'gpg conceded', home_df, away_df)/avg_gpg['total avg home gpg scored'],

      'away_attack': find_team_metric('away', AWAY_TEAM, 'gpg scored', home_df, away_df)/avg_gpg['total avg away gpg scored'],
      'home_defence': find_team_metric('home', HOME_TEAM, 'gpg conceded', home_df, away_df)/avg_gpg['total avg away gpg scored'],
  }

  projected_goals = {
      'projected_home_goals': attack_def_n_proj['home_attack'] * attack_def_n_proj['away_defence'] * avg_gpg['total avg home gpg scored'],
      'projected_away_goals': attack_def_n_proj['away_attack'] * attack_def_n_proj['home_defence'] * avg_gpg['total avg away gpg scored'],
  }

  projected_goals['projected_total_goals'] = projected_goals['projected_home_goals'] + projected_goals['projected_away_goals']

  if print_options:
    print("Projected Goals: ", projected_goals, end='\n\n')

  ## STEP 2 | PROBABILITY OF EACH TEAM SCORING X NUM OF GOALS
  columns= ['teams'] + list(range(0, 9))  # home_team or away_team and the number of goals they might score
  prob_df_data=[]

  # For each team, get the probabiltiy of them scoring each number of goals using the poisson distribution
  for team in ['home_team', 'away_team']:
    # The rate (average) will change depending on the team in question
    if team == 'home_team':
      rate = projected_goals['projected_home_goals']
    else: rate = projected_goals['projected_away_goals']
    # Get the probability for each number of goals
    data = [u.poisson_distribution(rate, x) for x in range(0, 9)]
    # Create a list with the team 'home' or 'away' and the probability
    data = [team] + data
    if print_options:
      print(data)

    prob_df_data.append(data)

  # Print a new line to space out print statements
  if print_options:
    print()

  # Probability df
  prob_df = pd.DataFrame(columns=columns, data=prob_df_data)
  # Set the teams column as the index
  prob_df.set_index('teams', inplace=True, drop=True)

  if print_options:
    print("Probability home team scoring 0 goals, rounded to 2 d.p.: ", round(prob_df.iloc[0:1, 0].values[0], 2))

  ## STEP 3 | CONTINGENCY TABLE TO SHOW THE PROBABILITY OF EACH SCORELINE
  # Create DataFrames representing the range of values for each factor
  # away_goals = pd.DataFrame({'Away Goals': range(9)})
  # home_goals = pd.DataFrame({'Home Goals': range(9)})
  
  # This wasn't working because it created the cross tabulatio with the values being ints and i was trying to overwrite those values with floats
  # Construct a DataFrame with all possible combinations of away and home goals
  # where each row represents a different combination of away and home goals
  # df = pd.DataFrame([(away, home) for away in range(9) for home in range(9)],
  #                   columns=['Away Goals', 'Home Goals'])
  

  # # Compute the cross-tabulation
  # two_way_table = pd.crosstab(df['Away Goals'], df['Home Goals'])
  # print(two_way_table.values)
    
  # Construct a DataFrame with all possible combinations of away and home goals
  # where each row represents a different combination of away and home goals
  # !!!Note: Away goals are the rows and the Home goals are the columns
  # Initialize the cross-tabulation DataFrame with zeros
  two_way_table = pd.DataFrame(0.0, index=range(9), columns=range(9))

  # Fill in the values for each cell in the cross-tabulated df
  row_index=0 # away team score
  for row in two_way_table.values:
    col_index=0 # home team score
    for col in row:
      home_team_prob = float(prob_df.iloc[0:1, col_index].values[0])
      away_team_prob = float(prob_df.iloc[1:2, row_index].values[0])
     
      # Calculate the percentage without formatting it as a string yet
      percentage_value = home_team_prob * away_team_prob * 100

      # Assign the calculated percentage to the DataFrame and then format it as a string
      two_way_table.iloc[row_index, col_index] = percentage_value
      # two_way_table.iloc[row_index, col_index] =  '{:.2f}%'.format(home_team_prob * away_team_prob * 100)
      col_index+=1
    row_index+=1
  
  
  if print_options:
    print("Odds of home team goals (columns in df) vs away team goals (rows in df): \n")


  # Based on those probabilities find the sum of percentage chance that the team wil win, i.e. sum of probabilities
  home_win = 0
  away_win = 0
  draw = 0

  row_index=0 # away team score
  for row in two_way_table.values:
      col_index=0 # home team score
      for col in row:
        # If the home_team scores more
        if(col_index > row_index):
          home_win += float(two_way_table.iloc[row_index, col_index])
        # Else if the away team score more
        elif(row_index > col_index):
          away_win += float(two_way_table.iloc[row_index, col_index])
        # Else it's a draw
        else:
          draw += float(two_way_table.iloc[row_index, col_index])
        col_index+=1
      row_index+=1

  result = who_wins(home_win, away_win, draw, HOME_TEAM, AWAY_TEAM)


  # Create an list of objects that will check store the number of expected points per game.
  expected_points_for_this_game = {
      HOME_TEAM : points_from_game(HOME_TEAM, result),
      AWAY_TEAM : points_from_game(AWAY_TEAM, result)
  }

  # Return a dict with the expected number of points that will achieved by each team.
  return expected_points_for_this_game

# Pass in a team and get how many point we expect them to get by the end of the season
def end_of_season_xp(id, home_df, away_df, avg_gpg, print_options=False):

  # Get the sofascore id from the df to get the fixtures from sofascore
  sofascore_id = home_df[home_df['team_id'] == id]['sofascore_team_id'].iloc[0]

  if print_options:
    print("understat team_id:", id, " sofascore team_id: ", sofascore_id)

  remaining_games = get_fixtures(sofascore_id)

  # Get the team name from the df
  team = home_df[home_df['team_id'] == id]['team_name'].iloc[0]
  print(f"Getting the expected points for {team}")

  # Get their current number of points
  base = home_df[home_df['team_name'] == team]['PTS'].iloc[0] + away_df[away_df['team_name'] == team]['PTS'].iloc[0]
  if print_options:
    print("base pts: ", base)
  x_pts = 0
  for game in remaining_games:
    # Get the home and away team names from the game data
    home_team = game['home_team']
    away_team = game['away_team']
    if print_options:
      print(home_team, ", " ,away_team)
    print
    # Get the expected results
    results = monte_carlo(home_team, away_team, avg_gpg, home_df, away_df)
    if print_options:
      print(results)

    # Get the expected number of points from the results
    pts_from_game = results[team]
    x_pts += pts_from_game

  predicted_pts = base + x_pts
  # return the total num of expected points
  return predicted_pts

"""### **3.6 End of League Table Prediction**"""
# Simulate the remaining fixtures and print the resulting Premiere League Table.

def get_expected_df(home_df, away_df, avg_gpg):
  # Simulate the expected end of season PL table
  expected_data = []

  for _, row in home_df.iterrows():
    expected_data.append({
      'team_name' : row['team_name'],
      'PTS': end_of_season_xp(row['team_id'], home_df, away_df, avg_gpg)
    })

  # Create the expected premier league df, sort by points and reset the index and drop the old one
  expected_df = pd.DataFrame(columns=['team_name', 'PTS'], data=expected_data).sort_values(by='PTS', ascending=False).reset_index(drop=True)
  # Add one to all the values so that the index goes from 1 to 20, instead of 0 to 19
  expected_df.index +=1
  # Rename index to position
  expected_df.rename_axis('position', axis='index', inplace=True)

  return expected_df

# Current PL Table

def merge_home_n_away_df(expected_df, home_df, away_df): 
  df = home_df + away_df
  df['team_name'] = df['team_name'].apply(u.split_name_in_half)
  df.drop(columns=['team_id', 'xG', 'xGA', 'xPTS', 'sofascore_team_id', 'gpg scored', 'gpg conceded'], inplace=True)

  # Merge dfs to get predicted points and sort by current points
  # Merge the DataFrames
  merged_df = df.merge(expected_df, on='team_name', suffixes=('_current', '_prediction'))

  # Sort the merged DataFrame
  merged_df = merged_df.sort_values(by='PTS_prediction', ascending=False)

  # Reset the index
  merged_df.reset_index(drop=True, inplace=True)

  # Calculate Goal Difference
  merged_df['GD'] = merged_df['G'] - merged_df['GA']
  # Reorder columns
  merged_df['position'] = range(1, len(merged_df) + 1) 
  merged_df = merged_df[['position', 'team_name', 'M', 'D', 'L', 'G', 'GA', 'GD', 'PTS_current', 'PTS_prediction']]

  # Print df
  return merged_df


# # Main function to run everything sequentially
# def predict_main(league_name, print_options=False):
#   # Get current league table with sofascore team id and understat stats 
#   home_df, away_df = f.get_current_league_table_df_data(league_name)
#   # Get the average goals scored and conceded per game
#   avg_gpg_dict = f.get_avg_gpg_dict(home_df, away_df)
#   # Get the predicted points
#   expected_df = f.get_expected_df(home_df, away_df, avg_gpg_dict)
#   # Merge the predicted points with the current table
#   merged_df = f.merge_home_n_away_df(expected_df, home_df, away_df)

#   returned_json = {
#     'league': league_name, 
#     'number_of_teams': len(merged_df),
#     'predicted_table': merged_df.to_dict('records')
#   }

#   return returned_json


# App routes
@app.route("/")
def home():
  domain_name = "https://league-table-predictor-git-main-richardogujawa.vercel.app"
  return f"""
    <h1>Welcome to League Table Predictor API</h1>
    <p>The predictor predicts the outcome of the league based on the current form of the teams in each league.</p>
    <p>To get the data for a league please fetch data from the appropriate endpoint below:</p>
    <ul>
      <li>Bundesliga => <a href="https://{domain_name}/league/bundesliga">https://{domain_name}/league/bundesliga</a></li>
      <li>English Premier League => <a href="https://{domain_name}/league/epl">https://{domain_name}/league/epl</a></li>
      <li>LaLiga => <a href="https://{domain_name}/league/laliga">https://{domain_name}/league/laliga</a></li>
      <li>Ligue 1 => <a href="https://{domain_name}/league/ligue_1">https://{domain_name}/league/ligue_1</a></li>
      <li>Serie A=> <a href="https://{domain_name}/league/serie-a">https://{domain_name}/league/serie_a</a></li>
    </ul>
  """

# @app.route("/league/<league_name>")
# def predict(league_name):
#   predicted_table_as_str = predict_main(league_name, True)
#   return json.dumps(predicted_table_as_str)


# --- Code should be above this line---
# Run server
# if __name__ == "__main__": 
#    app.run(debug=True)

# Production server
# More on it here: 
# https://stackoverflow.com/questions/51025893/flask-at-first-run-do-not-use-the-development-server-in-a-production-environmen
# if __name__ == "__main__":
#     from waitress import serve
#     serve(app, host="0.0.0.0", port=8080)