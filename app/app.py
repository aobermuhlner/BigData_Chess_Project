from flask import Flask, render_template, jsonify
import requests
import os
import requests
import concurrent.futures


from src.utils.lichess_api import download_games
from src.utils.apendraResults import gameResultsData, gameTypesData, dataElo
import src.utils.openings as openings

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

    return render_template('tab/other_analysis.html', 
                            gameResultsData=gameResultsData, 
                            gameTypesData=gameTypesData,
                            data=data)

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


    