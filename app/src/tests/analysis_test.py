import chess
import pandas as pd
from stockfish import Stockfish
import time
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from queue import Queue


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

def build_stored_game_analysis_no_index(game, move_number, prev_evaluation, stockfish):
    row = {}
    row['move_number'] = move_number
    board = chess.Board()

    for san in game.moves[:move_number]:
        move = board.parse_san(san)
        board.push(move)

    fen = board.fen()
    row['fen'] = fen
    row['url'] = getattr(game.headers, "_tag_roster", {}).get("Site", "") + f"#{move_number}"

    # Always calculate evaluation directly from Stockfish
    stockfish.set_fen_position(fen)
    evaluation = stockfish.get_evaluation()
    evaluation_value = evaluation['value']

    row['evaluation'] = evaluation_value
    row['evaluation_change'] = evaluation_value - prev_evaluation
    row['accuracy'] = get_accuracy(row['evaluation_change'])
    row['invalid'] = bool(board.is_checkmate()) or bool(board.can_claim_draw())

    return row, evaluation_value


def analyze_games(chunk, max_move_number, stockfish_path, depth, skill_level):
    start_time = time.time()  # Record start time for this chunk
    stockfish = initialize_stockfish(stockfish_path, depth, skill_level)
    evaluations_cache = load_evaluations_cache()

    all_game_analysis = []
    prev_evaluation = 0
    for game in chunk.itertuples(index=False):
        game_analysis = []
        for move_number in range(1, max_move_number + 1):
            analysis_result, prev_evaluation = build_stored_game_analysis(game, move_number, prev_evaluation, stockfish, evaluations_cache)
            game_analysis.append(analysis_result)
        all_game_analysis.append(pd.DataFrame(game_analysis).set_index("move_number"))

    end_time = time.time()  # Record end time for this chunk
    # Include the timing data with the results
    return {"analysis": all_game_analysis, "start_time": start_time, "end_time": end_time, "duration": end_time - start_time}


def parallel_game_analysis(games, max_move_number, stockfish_path, depth, skill_level, workers=3):
    total_games = len(games)
    chunk_size = total_games // workers
    remainder = total_games % workers

    # Creating chunks with adjusted sizes for better balance
    game_chunks = []
    start = 0
    for i in range(workers):
        end = start + chunk_size + (1 if i < remainder else 0)  # Add one more to some chunks to balance the remainder
        game_chunks.append(games.iloc[start:end])
        start = end

    args = [(chunk, max_move_number, stockfish_path, depth, skill_level) for chunk in game_chunks]

    timing_results = []
    results = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(analyze_games, *arg): i for i, arg in enumerate(args)}
        for future in as_completed(futures):
            core_result = future.result()
            results.extend(core_result["analysis"])
            chunk_memory_kb = game_chunks[futures[future]].memory_usage(deep=True).sum() / 1024
            timing_results.append({
                "core_id": futures[future],
                "chunk_size": len(game_chunks[futures[future]]),
                "memory_kb": chunk_memory_kb,
                "duration": core_result["duration"]
            })

    # Convert timing results to DataFrame
    timing_df = pd.DataFrame(timing_results)
    return results, timing_df



if __name__ == "__main__":
    file_name = "apendra_games"
    stockfish_path = "C:/Users/aober/Documents/Data_Science_Studium/4Semester/BigData/stockfish/stockfish-windows-x86-64-avx2.exe"
    max_move_number = 10
    n_games = 200  # Specify the number of games to analyze
    skill_level = 10
    depth = 15
    workers = 8

    games = load_game_data(file_name)
    games = games.iloc[:n_games]  # Limit the number of games if necessary

    start_time = time.time()
    results, timing_df = parallel_game_analysis(games, max_move_number, stockfish_path, depth, skill_level, workers)
    print("Analysis completed. Timing DataFrame:")
    print(timing_df)
    print(time.time() - start_time)