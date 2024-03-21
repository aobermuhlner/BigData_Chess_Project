from flask import Flask, render_template, request
import requests
import os

app = Flask(__name__)


# Get main page and take form which conatins lichess API instructions
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submitform', methods = ['POST'])
def submitform():
    if request.method == 'POST':
        name = request.form['name']
        games = lichessgames(name)
        return games.text
    else:
        return 'try again'
# Get games from Lichess-API
    
def lichessgames(userName):
    print('accesing liches now')
    print(f'https://lichess.org/api/games/user/{userName}')
    gamesRequest = requests.get(f'https://lichess.org/api/games/user/{userName}')

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
    