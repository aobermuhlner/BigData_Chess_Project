from flask import Flask, render_template, request
import requests
import os
import requests
import concurrent.futures

from src.utils.lichess_api import download_games
from src.utils.otherAnalysis import analyze_game_results, analyze_game_types

app = Flask(__name__)


@app.route('/')
def showMainpage():
    render_template('dashboard.html')

@app.route('/getGames')
def getGames():
    return render_template('tabs/get_games.html')

@app.route('/otherAnalysis')
def otherAnalysis():
    render_template('tabs/other_analysis.html')

@app.route('/getGamesFromForm', methods=['GET'])
def getLichesApi():
    result = download_games()
    return result 

@app.route('/api/game-results')
def game_results_api():
    games = load_json_data('path_to_your_game_data.json')
    result_counts = analyze_game_results(games)
    return jsonify({'labels': list(result_counts.keys()), 'values': list(result_counts.values())})

@app.route('/api/game-types')
def game_types_api():
    games = load_json_data('path_to_your_game_data.json')
    type_counts = analyze_game_types(games)
    return jsonify({'labels': list(type_counts.keys()), 'values': list(type_counts.values())})

@app.route('/api/elo-rating/<player_name>')
def elo_rating_api(player_name):
    games = load_json_data('path_to_your_game_data.json')
    dates, elos = analyze_elo_development(games, player_name)
    return jsonify({'labels': list(dates), 'values': list(elos)})

if __name__ == '__main__':
    app.run(debug=True)


    