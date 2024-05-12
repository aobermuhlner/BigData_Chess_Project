import chess
import pandas as pd
import json
from stockfish import Stockfish
import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import time


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
    moves_data = []

    # Adjusted to access attributes correctly from a namedtuple
    for san in game.moves[:move_number]:
        move = board.parse_san(san)
        board.push(move)

    fen = board.fen()
    row['fen'] = fen
    # Accessing headers as attributes
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


def analyze_games(chunk, max_move_number, stockfish_path, depth, skill_level):
    stockfish = initialize_stockfish(stockfish_path, depth, skill_level)
    evaluations_cache = load_evaluations_cache()

    all_game_analysis = []
    prev_evaluation = 0
    for game in chunk.itertuples(index=False):  # Make sure to set index=False if you don't want the index within the tuple
        game_analysis = []
        for move_number in range(1, max_move_number + 1):
            analysis_result, prev_evaluation = build_stored_game_analysis(game, move_number, prev_evaluation, stockfish, evaluations_cache)
            game_analysis.append(analysis_result)
        all_game_analysis.append(pd.DataFrame(game_analysis).set_index("move_number"))
    return all_game_analysis

def parallel_game_analysis(games, max_move_number, stockfish_path, depth, skill_level):
    worker= 1
    chunk_size = len(games) // worker  # Or determine dynamically based on the number of CPUs
    game_chunks = [games.iloc[i:i + chunk_size] for i in range(0, len(games), chunk_size)]
    args = [(chunk, max_move_number, stockfish_path, depth, skill_level) for chunk in game_chunks]

    results = []
    with ProcessPoolExecutor(max_workers=worker) as executor:
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

    max_move_number = 10
    n_games = 100  #len(games)
    skill_level = 10
    depth = 15

    games = load_game_data(file_name)
    games = games.iloc[:n_games]
 #   stockfish = initialize_stockfish(stockfish_path, depth, skill_level)
    start_time = time.time()
  #  games_analysis = analyze_games(games, n_games, max_move_number, stockfish, evaluations_cache)
    results = parallel_game_analysis(games, max_move_number,stockfish_path,depth, skill_level)

    duration = time.time() - start_time
    print(duration)
 #   print(results)
