from flask import Flask, render_template, jsonify, request
import traceback
from src.utils.lichess_api import download_and_measure_games_multithreaded
from src.utils.apendraResults import gameResultsData, gameTypesData, dataElo
import src.utils.openings as openings
from src.utils.accuracyGraph import load_and_aggregate_data
from datetime import date

app = Flask(__name__)

@app.route('/')
def getGames():
    return render_template('tab/get_games.html', today=date.today().isoformat())

@app.route('/analyzed')
def analysis():
    return render_template('tab/analyzed_games.html')

@app.route('/otherAnalysis')
def otherAnalysis():
    data = openings.process_openings()
    _, unique_combinations = load_and_aggregate_data()
    combinations = unique_combinations.to_dict(orient='records')
    return render_template('tab/other_analysis.html', 
                            gameResultsData=gameResultsData, 
                            gameTypesData=gameTypesData,
                            data=data,
                            combinations=combinations)

@app.route('/get_elo_data')
def get_elo_data():
    data = dataElo
    return jsonify(data)

@app.route('/getGamesFromForm', methods=['GET'])
def get_games():
    try:
        # Extract parameters from request
        username = request.args.get('username')
        since = request.args.get('since')
        until = request.args.get('until')
        color = request.args.get('color')
        rated = request.args.get('rated')
        game_types = request.args.getlist('game_type')

        # Call the function to download and measure games
        response_data = download_and_measure_games_multithreaded(username, since, until, color, rated, game_types)
        return jsonify(response_data)
    except Exception as e:
        # Log the exception and return an error message
        traceback.print_exc()
        return jsonify({'error': 'Failed to fetch games', 'details': str(e)}), 500

@app.route('/get_accuracy_data', methods=['POST'])
def get_accuracy_data():
    data = request.get_json()
    opening_name = data.get('opening_name')
    player_color = data.get('player_color')
    
    avg_accuracy_per_move, _ = load_and_aggregate_data()

    if player_color == 'White':
        filtered_data = avg_accuracy_per_move[
            (avg_accuracy_per_move['opening_name'] == opening_name) &
            (avg_accuracy_per_move['player_color'] == player_color) &
            (avg_accuracy_per_move['move_number'] % 2 == 1)
        ]
    else:
        filtered_data = avg_accuracy_per_move[
            (avg_accuracy_per_move['opening_name'] == opening_name) &
            (avg_accuracy_per_move['player_color'] == player_color) &
            (avg_accuracy_per_move['move_number'] % 2 == 0)
        ]

    result = {
        'move_number': filtered_data['move_number'].tolist(),
        'accuracy': filtered_data['accuracy'].tolist()
    }
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)


    