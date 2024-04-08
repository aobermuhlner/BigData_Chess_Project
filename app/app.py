from flask import Flask, render_template, request
import requests
import os

app = Flask(__name__)

# Folder name and other variables

GAME_STORAGE = './data/test'

# Check and create if necessary folder for games

os.makedirs(GAME_STORAGE, exist_ok=True)

# Get main page and take form which conatins lichess API instructions
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submitform', methods = ['POST'])
def submitform():
    if request.method == 'POST':
        # Get all Variables from form
        name = request.form['name']
        gameType = request.form.getlist('gameType')
        color = request.form['color']
        timeStart = request.form['timeStart']
        timeEnd = request.form['timeEnd']
        rated = request.form['rated']
        opponentName = request.form['opponentName']
        print(gameType, color, timeStart, timeEnd, rated, opponentName)
        games = lichessgames(name,  gameType, color, timeStart, timeEnd, rated, opponentName)
        pgn_file_path = os.path.join(GAME_STORAGE, f'{name}_games.pgn')
        with open(pgn_file_path, 'wb') as f:
            f.write(games.content)
        return f'Games have been downloaded and saved to {pgn_file_path}'
    # save pgn file as pgn with username and download date
    # return message of successfull download
    # add number of games loaded counter
    else:
        return 'try again'
# Get games from Lichess-API
    
def lichessgames(userName, gameType, color, timeStart, timeEnd, rated, opponentName):
    print('accesing liches now')
    # Ready for addtional parameters
    # add opening true to lichess api
    gamesRequest = requests.get(f'https://lichess.org/api/games/user/{userName}?opening=true')

    if gamesRequest.status_code == 200:
        # Games of player found
        print('have found all games in lichess')
        return gamesRequest
    else:
        # Request failed, return error message
        errorMessage = 'This failed, find another solution'
        return errorMessage


if __name__ == '__main__':
    app.run()
    