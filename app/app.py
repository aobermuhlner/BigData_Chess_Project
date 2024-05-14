from flask import Flask, render_template, jsonify
import requests
import os
import requests
import concurrent.futures

from src.utils.lichess_api import download_games
from src.utils.apendraResults import gameResultsData, gameTypesData, dataElo
from src.utils.openings import most_played_white, highest_accuracy_white, lowest_accuracy_white, most_played_black, highest_accuracy_black, lowest_accuracy_black, most_played_variations_white, highest_accuracy_variations_white, lowest_accuracy_variations_white, most_played_variations_black, highest_accuracy_variations_black, lowest_accuracy_variations_black

app = Flask(__name__)

@app.route('/')
def getGames():
    return render_template('tab/get_games.html')

@app.route('/analyzed')
def analysis():
    return render_template('tab/analyzed_games.html')

@app.route('/otherAnalysis')
def otherAnalysis():
    return render_template('tab/other_analysis.html', 
                            gameResultsData=gameResultsData, 
                            gameTypesData=gameTypesData,
                            most_played_white=most_played_white,
                            highest_accuracy_white=highest_accuracy_white,
                            lowest_accuracy_white=lowest_accuracy_white,
                            most_played_black=most_played_black,
                            highest_accuracy_black=highest_accuracy_black,
                            lowest_accuracy_black=lowest_accuracy_black,
                            most_played_variations_white=most_played_variations_white,
                            highest_accuracy_variations_white=highest_accuracy_variations_white,
                            lowest_accuracy_variations_white=lowest_accuracy_variations_white,
                            most_played_variations_black=most_played_variations_black,
                            highest_accuracy_variations_black=highest_accuracy_variations_black,
                            lowest_accuracy_variations_black=lowest_accuracy_variations_black)

@app.route('/get_elo_data')
def get_elo_data():
    data = dataElo
    return jsonify(data)

@app.route('/getGamesFromForm', methods=['GET'])
def getLichesApi():
    result = download_games()
    return result 

if __name__ == '__main__':
    app.run(debug=True)


    