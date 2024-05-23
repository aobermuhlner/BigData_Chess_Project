import chess
import pandas as pd
import json
from stockfish import Stockfish
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import numpy as np
from sklearn.linear_model import LogisticRegression
import joblib

def load_game_data(file_name):
    games = pd.read_csv(f"../../../data/processed/{file_name}.csv")
    games['moves'] = games['moves'].apply(lambda x: eval(x))
    games['headers'] = games['headers'].apply(lambda x: eval(x))
    return games

def load_evaluations_cache():
    file_path = "../../../data/indexed_positions/final_processed_index.json"
    with open(file_path, 'r') as file:
        cache = json.load(file)
    return cache

def initialize_stockfish(path, depth, skill_level):
    stockfish = Stockfish(path)
    stockfish.set_depth(depth)
    stockfish.set_skill_level(skill_level)
    return stockfish

def load_logistic_regression_model():
    model_path = "../../../models/opening_classifier/opening_middlegame_classifier.pkl"
    with open(model_path, 'rb') as model_file:
        model = joblib.load(model_path)
    return model


def fen_to_input(fen):
    board = chess.Board(fen)
    input_matrix = np.zeros((8, 8, 12), dtype=int)

    piece_to_plane = {
        'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
        'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11
    }

    for rank in range(8):
        for file in range(8):
            piece = board.piece_at(chess.square(file, 7 - rank))
            if piece:
                plane = piece_to_plane[piece.symbol()]
                input_matrix[rank, file, plane] = 1

    additional_planes = np.zeros((8, 8, 5), dtype=int)

    if board.has_kingside_castling_rights(chess.WHITE):
        additional_planes[:, :, 0] = 1
    if board.has_queenside_castling_rights(chess.WHITE):
        additional_planes[:, :, 1] = 1
    if board.has_kingside_castling_rights(chess.BLACK):
        additional_planes[:, :, 2] = 1
    if board.has_queenside_castling_rights(chess.BLACK):
        additional_planes[:, :, 3] = 1

    if board.ep_square:
        ep_rank = chess.square_rank(board.ep_square)
        ep_file = chess.square_file(board.ep_square)
        additional_planes[7 - ep_rank, ep_file, 4] = 1

    side_to_move_plane = np.ones((8, 8, 1), dtype=int) if board.turn == chess.WHITE else np.zeros((8, 8, 1), dtype=int)

    input_tensor = np.concatenate((input_matrix, additional_planes, side_to_move_plane), axis=2)

    return input_tensor

def get_accuracy(evaluation_change):
    if abs(evaluation_change) <= 25:
        return 100
    elif abs(evaluation_change) <= 50:
        return 75
    elif abs(evaluation_change) <= 75:
        return 50
    elif abs(evaluation_change) <= 100:
        return 25
    else:
        return 0

def build_stored_game_analysis(game, move_number, prev_evaluation, stockfish, evaluations_cache):
    row = {}
    row['move_number'] = move_number
    board = chess.Board()

    for san in game.moves[:move_number]:
        move = board.parse_san(san)
        board.push(move)

    fen = board.fen()
    row['fen'] = fen
    row['url'] = getattr(game.headers, "_tag_roster", {}).get("Site", "") + f"#{move_number}"

    if fen in evaluations_cache:
        evaluation_value = evaluations_cache[fen]
    else:
        stockfish.set_fen_position(fen)
        evaluation = stockfish.get_evaluation()
        evaluation_value = evaluation['value']

    row['evaluation'] = evaluation_value
    row['evaluation_change'] = evaluation_value - prev_evaluation
    row['accuracy'] = get_accuracy(row['evaluation_change'])
    row['invalid'] = bool(board.is_checkmate()) or bool(board.can_claim_draw())

    return row, evaluation_value

def analyze_games(chunk, stockfish_path, depth, skill_level):
    stockfish = initialize_stockfish(stockfish_path, depth, skill_level)
    evaluations_cache = load_evaluations_cache()
    logistic_model = load_logistic_regression_model()

    all_game_analysis = []
    for game in chunk.itertuples(index=False):  # Make sure to set index=False if you don't want the index within the tuple
        game_analysis = []
        prev_evaluation = 0
        move_number = 1
        middle_game_reached = False

        while move_number <= len(game.moves):
            analysis_result, prev_evaluation = build_stored_game_analysis(game, move_number, prev_evaluation, stockfish, evaluations_cache)
            game_analysis.append(analysis_result)

            # Convert FEN to input tensor for logistic regression model
            input_tensor = fen_to_input(analysis_result['fen'])
            # Aggregate the input_tensor into a 1D array of 6 features as required by the model
            num_pieces = np.sum(input_tensor[:, :, :12])
            castling_rights = np.sum(input_tensor[:, :, 12:16], axis=(0, 1))
            side_to_move = np.sum(input_tensor[:, :, 16])

            model_input = np.concatenate(([num_pieces], castling_rights, [side_to_move]))

            classification = logistic_model.predict([model_input])[0]


            if classification == 0:  # If classified as middle game
                middle_game_reached = True
                for extra_move in range(1, 5):  # Evaluate 4 more moves
                    if move_number + extra_move <= len(game.moves):
                        extra_move_number = move_number + extra_move
                        extra_analysis_result, prev_evaluation = build_stored_game_analysis(game, extra_move_number, prev_evaluation, stockfish, evaluations_cache)
                        game_analysis.append(extra_analysis_result)
                break  # Stop the loop after evaluating the extra moves

            move_number += 1

        all_game_analysis.append(pd.DataFrame(game_analysis).set_index("move_number"))
    return all_game_analysis

import matplotlib.pyplot as plt

def parallel_game_analysis(games, stockfish_path, depth, skill_level, workers):
    chunk_size = len(games) // workers  # Or determine dynamically based on the number of CPUs
    game_chunks = [games.iloc[i:i + chunk_size] for i in range(0, len(games), chunk_size)]
    args = [(chunk, stockfish_path, depth, skill_level) for chunk in game_chunks]

    results = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(analyze_games, *arg) for arg in args]
        for future in as_completed(futures):
            results.extend(future.result())
    return results

def save_results_to_json(results, file_path):
    with open(file_path, 'w') as file:
        json.dump(results, file, indent=4)

if __name__ == "__main__":
    file_name = "apendra_games"
    stockfish_path = "C:/Users/aober/Documents/Data_Science_Studium/4Semester/BigData/stockfish/stockfish-windows-x86-64-avx2.exe"

    n_games = 19  # len(games)
    skill_level = 1
    depth = 1

    games = load_game_data(file_name)
    games = games.iloc[:n_games]
    start_time = time.time()

    results = parallel_game_analysis(games, stockfish_path, depth, skill_level, 4)
    print(results)
   # json.dump(results, indent=4)

