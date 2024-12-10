import chess
import pandas as pd
import json
from stockfish import Stockfish
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import numpy as np
import joblib
import matplotlib.pyplot as plt

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
 #   row['url'] = getattr(game.headers, "_tag_roster", {}).get("Site", "") + f"#{move_number}"

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
    for game in chunk.itertuples(index=False):
        game_analysis = []
        prev_evaluation = 0
        move_number = 1

        while move_number <= len(game.moves):
            analysis_result, prev_evaluation = build_stored_game_analysis(game, move_number, prev_evaluation, stockfish, evaluations_cache)
            analysis_result['move_number'] = move_number
            analysis_result['game_stage'] = 'opening'  # Default to opening

            input_tensor = fen_to_input(analysis_result['fen'])
            num_pieces = np.sum(input_tensor[:, :, :12])
            castling_rights = np.sum(input_tensor[:, :, 12:16], axis=(0, 1))
            side_to_move = np.sum(input_tensor[:, :, 16])
            model_input = np.concatenate(([num_pieces], castling_rights, [side_to_move]))

            classification = logistic_model.predict([model_input])[0]
            if classification == 0:
                analysis_result['game_stage'] = 'middle_game'
                # Optionally break if this is your desired logic
            game_analysis.append(analysis_result)
            move_number += 1

        # Ensure that a DataFrame is created even if no moves are analyzed
        if not game_analysis:
            game_analysis.append({'move_number': None, 'game_stage': 'N/A'})
        df = pd.DataFrame(game_analysis)
        df.set_index('move_number', inplace=True)
        all_game_analysis.append(df)

    return all_game_analysis



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

def get_analyzed_games(games):
    # Internal parameters change stockfish path to yours and worker to your core amount
    n_games = len(games)
    skill_level = 15
    depth = 15
    num_threads = 8  # Number of threads for parallel processing
    stockfish_path = "C:/Users/aober/Documents/Data_Science_Studium/4Semester/BigData/stockfish/stockfish-windows-x86-64-avx2.exe"

    games = games[:n_games]
    games.loc[:, 'moves'] = games['moves'].apply(lambda x: x.split() if isinstance(x, str) else x)

    results = parallel_game_analysis(games, stockfish_path, depth, skill_level, num_threads)
    return results



def plot_transition_distribution(all_game_analysis):
    # Extracting the move number for each game where the stage changes to middle game
    transition_moves = []
    for game_df in all_game_analysis:
        if 'game_stage' in game_df.columns:
            middle_game_start = game_df[game_df['game_stage'] == 'middle_game'].index.min()
            if middle_game_start is not None:
                transition_moves.append(middle_game_start)

    # Convert to a DataFrame for easier handling
    transition_df = pd.DataFrame(transition_moves, columns=['transition_move'])

    # Determine the range of move numbers for setting bins
    min_move = transition_df['transition_move'].min()
    max_move = transition_df['transition_move'].max()
    bins = range(0, 43)  # +2 to include the last move number

    # Plotting the distribution of transition moves
    fig, ax = plt.subplots(figsize=(15, 6))  # Adjusted for better visibility of individual bars
    ax.set_facecolor('beige')
    fig.patch.set_facecolor('beige')
    transition_df['transition_move'].hist(bins=bins, alpha=0.75, edgecolor='black', color='#003f5c', ax=ax)
    plt.title('Distribution of Opening to Middle Game Transition Moves')
    plt.xlabel('Transition Move Number')
    plt.ylabel('Frequency of Games')
    plt.xticks(bins)  # Set x-ticks to match the bins
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    file_name = "../../../data/pipeline_test/processed_games.json"
    with open(file_name, 'r') as file:
        games = json.load(file)
      #  games = data['games']

    # Convert games to a pandas DataFrame
    games = pd.DataFrame(games)
    analyzed_games = get_analyzed_games(games)

    output_file_path = "../../../data/pipeline_test/analyzed_positions.json"
    games_json = [game.to_json(orient='records') for game in analyzed_games]
    with open(output_file_path, 'w') as file:
        json.dump(games_json, file, indent=4)
