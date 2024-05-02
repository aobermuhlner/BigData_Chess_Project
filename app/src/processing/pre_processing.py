import chess.pgn
import pandas as pd
import numpy as np
import tqdm
import ftfy

pd.options.display.max_columns = 999

file_name = "apendra_games"
player_name = "Apendra"
NUM_GAMES = 1800

def read_pgn_create_dataframe(file_name, num_games, player_name):
    rows = []
    with open(f'../../testData/lichess_db_standard_rated_2013-04/{file_name}.pgn') as pgn:
        for _ in tqdm.tqdm(range(num_games)):
            row = {}
            game = chess.pgn.read_game(pgn)
            if game is None:
                break
            row['headers'] = game.headers.__dict__
            row['moves'] = [x.uci() for x in game.mainline_moves()]
            rows.append(row)
    games = pd.DataFrame(rows)
    return games

def process_games_data(games, player_name):
    games['lichess_id'] = games['headers'].apply(lambda x: x.get("_tag_roster", {}).get("Site", ""))
    games['white_elo'] = games['headers'].apply(lambda x: safe_convert_to_int(x.get("_others", {}).get("WhiteElo", "").split("-")[0]))
    games['black_elo'] = games['headers'].apply(lambda x: safe_convert_to_int(x.get("_others", {}).get("BlackElo", "").split("-")[0]))
    games['ECO'] = games['headers'].apply(lambda x: x.get("_others", {}).get("ECO"))
    games['opening_name'] = games['headers'].apply(lambda x: x.get("_others", {}).get("Opening", ""))
    games['event'] = games['headers'].apply(lambda x: x.get("_tag_roster", {}).get("Event", ""))
    games['player_color'] = games['headers'].apply(lambda x: find_player_color(x, player_name))
    games['score'] = games.apply(lambda x: player_score(x['headers'], x['player_color']), axis=1)
    games['opening_name'] = games['opening_name'].apply(ftfy.fix_encoding)
    games = games[games['ECO'] != '?']
    return games

def safe_convert_to_int(value):
    try:
        return int(value)
    except ValueError:
        return None  # or you can use np.nan or a placeholder like -1

def find_player_color(header, player_name):
    if header.get("_tag_roster", {}).get("White", "") == player_name:
        return 'White'
    elif header.get("_tag_roster", {}).get("Black", "") == player_name:
        return 'Black'
    return 'Unknown'

def player_score(header, player_color):
    result = header.get('_tag_roster', {}).get('Result', '')
    if result == "1/2-1/2":
        return 0.5  # Draw
    elif result == "1-0" and player_color == 'White':
        return 1.0  # White win
    elif result == "0-1" and player_color == 'Black':
        return 1.0  # Black win
    return 0.0  # Loss or unknown result

def save_to_csv(games, file_name):
    games.to_csv(f"../../testData/{file_name}.csv", index=False)

def load_from_csv(file_name):
    return pd.read_csv(f"../../testData/{file_name}.csv")





if __name__ == "__main__":
    # Define the parameters
    file_name = "apendra_games"
    player_name = "Apendra"
    NUM_GAMES = 1800  # From https://database.nikonoel.fr/

    # Step 1: Read PGN files and create a DataFrame
    games = read_pgn_create_dataframe(file_name, NUM_GAMES, player_name)

    # Step 2: Process and clean the data
    games_processed = process_games_data(games, player_name)

    # Step 3: Save the processed data to CSV
    save_to_csv(games_processed, file_name)

    # Optional: Load the data back from CSV (demonstrating the load function)
    games_loaded = load_from_csv(file_name)

    # Now, games_loaded contains the processed game data ready for further analysis or use
    print(games_loaded.head())

