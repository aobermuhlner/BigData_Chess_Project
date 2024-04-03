import chess
import pandas as pd
import numpy as np
import json
from stockfish import Stockfish
import tqdm


def load_game_data(file_name):
    games = pd.read_csv(f"../../../testData/{file_name}.csv")
    games['moves'] = games['moves'].apply(lambda x: eval(x))
    games['headers'] = games['headers'].apply(lambda x: eval(x))
    return games



def initialize_stockfish(path, depth, skill_level):
    stockfish = Stockfish(path)
    stockfish.set_depth(depth)
    stockfish.set_skill_level(skill_level)
    return stockfish



def get_accuracy(evaluation_change):
    # Function to calculate accuracy based on evaluation_change
    return get_accuracy(evaluation_change)


def build_stored_game_analysis(game, move_number, stockfish):
    row = {'move_number': move_number, 'taken': []}
    board = chess.Board()
    for san in game['moves'][:move_number]:
        parsed_san = board.parse_san(san)
        taken = board.piece_at(parsed_san.to_square)
        if taken:
            row['taken'].append(taken.__str__())
        board.push_san(san)
    row['invalid'] = bool(board.promoted) or bool(board.outcome())
    stockfish.set_fen_position(board.fen())
    evaluation = stockfish.get_evaluation()
    row['evaluation'] = evaluation['value']
    row['evaluation_change'] = evaluation['value'] - (row['evaluation'] if move_number > 1 else 0)
    row['accuracy'] = get_accuracy(row['evaluation_change'])
    row['taken_score'] = sum([piece_scores.get(p, 0) for p in row['taken']]) * 100
    row['fen'] = board.fen()
    row['url'] = game['headers'].get("_tag_roster", {}).get("Site", "") + f"#{move_number}"
    row['last_move'] = san if 'san' in locals() else None
    return row, evaluation['value']



def analyze_games(games, n_games, max_move_number, stockfish):
    all_game_analysis = []
    for i in tqdm.tqdm(range(min(n_games, len(games)))):
        game = games.iloc[i]
        game_analysis = []
        prev_evaluation = 0
        for move_number in range(1, max_move_number + 1):
            analysis_result, prev_evaluation = build_stored_game_analysis(game, move_number, prev_evaluation, stockfish)
            game_analysis.append(analysis_result)
        all_game_analysis.append(pd.DataFrame(game_analysis).set_index("move_number"))
    return all_game_analysis



def save_data(games, games_analysis, file_name):
    games.to_json(f"../../../testData/{file_name}.json", orient='records', lines=True)
    games_analysis_dict = [df.to_dict(orient='records') for df in games_analysis]
    with open(f"../../testData/{file_name}_analysis.json", "w") as file:
        json.dump(games_analysis_dict, file)


    games_analysis_dict = [df.to_dict(orient='records') for df in games_analysis]
    with open("../../../testData/games_analysis.json", "w") as file:
        json.dump(games_analysis_dict, file)


if __name__ == "__main__":
    file_name = "apendra_games"
    n_games = 1000
    max_move_number = 10
    stockfish_path = "C:/Users/aober/Documents/Data_Science_Studium/4Semester/BigData/stockfish/stockfish-windows-x86-64-avx2.exe"
    depth = 15
    skill_level = 15

    games = load_game_data(file_name)
    stockfish = initialize_stockfish(stockfish_path, depth, skill_level)
    games_analysis = analyze_games(games, n_games, max_move_number, stockfish)
    save_data(games[0:n_games], games_analysis, file_name)
