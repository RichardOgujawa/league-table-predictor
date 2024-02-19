from flask import Flask, request, jsonify
import json
import functions as f


"""### Create Flask Application"""
app = Flask(__name__)

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