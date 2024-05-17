from flask import Flask, render_template, jsonify, request

from src.utils.lichess_api import download_games
from src.utils.apendraResults import gameResultsData, gameTypesData, dataElo
import src.utils.openings as openings
from src.utils.accuracyGraph import load_and_aggregate_data

app = Flask(__name__)

@app.route('/')
def getGames():
    return render_template('tab/get_games.html')

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
def getLichesApi():
    result = download_games()
    return result 

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


    