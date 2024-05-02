import pandas as pd
import tqdm
from stockfish import Stockfish
import random
import chess
import chess.engine
import pandas as pd
import tqdm
import json
import os

# Setup the stockfish engine
stockfish_good=Stockfish("C:/Users/flras/Documents/ZHAW_FS24/PM4/stockfish/stockfish-windows-x86-64-avx2.exe")
stockfish_good.set_depth(20) 
stockfish_good.set_skill_level(20) 

def get_fen_from_move_sequence(move_sequence):
    board = chess.Board()
    for move_san in move_sequence.split(' '):
        move = board.parse_san(move_san)
        board.push(move)
    return board.fen()


def analyze_positions_from_csv(file_path, amount):
    """
    Processes a CSV file of move sequences, evaluates positions with a minimum occurrence count,
    and returns a dictionary with the FEN as the key and the evaluation score as the value.

    :param file_path: Path to the CSV file containing the positions and counts.
    :param amount: The minimum count a position must have to be evaluated.
    :return: A dictionary of evaluated positions.
    """
    games_df = pd.read_csv(file_path)
    positions_dict = {}
    print(games_df.head())

    # Filter rows where the 'count' is at least the specified 'amount'
    filtered_games_df = games_df[games_df['count'] >= amount]

    for _, row in tqdm.tqdm(filtered_games_df.iterrows(), total=filtered_games_df.shape[0]):
        position = row['position']
        fen = get_fen_from_move_sequence(position)

        # Only evaluate if this position does not already exist in the dictionary
        if fen not in positions_dict:
            evaluation = stockfish_good.get_evaluation()
            positions_dict[fen] = evaluation['value']

    return positions_dict

def get_evaluation(stockfish, fen):
    info = stockfish.analyse(chess.Board(fen), chess.engine.Limit(time=0.1))
    return info['score'].white().score(mate_score=10000)

def analyze_positions(file_path, amount, stockfish_path, existing_positions=None):
    with chess.engine.SimpleEngine.popen_uci(stockfish_path) as stockfish:
        games_df = pd.read_csv(file_path)
        analysis_dict = {}  # Dictionary to store the FEN and evaluation
        existing_positions = existing_positions or {}
        duplicate_counter = 0  # Counter for duplicates

        # Filter based on 'count' value
        filtered_df = games_df[games_df['count'] >= amount]
        
        for _, row in tqdm.tqdm(filtered_df.iterrows(), total=filtered_df.shape[0]):
            position_string = row['position']
            fen = get_fen_from_move_sequence(position_string)

            if fen not in existing_positions:
                evaluation = get_evaluation(stockfish, fen)
                analysis_dict[fen] = evaluation
            else:
                duplicate_counter += 1

        print(f"Duplicate positions skipped: {duplicate_counter}")
        return analysis_dict


if __name__ == '__main__':
    file_path = './data/test/final_processed_index.csv'
    stockfish_path = ("C:/Users/flras/Documents/ZHAW_FS24/PM4/stockfish/stockfish-windows-x86-64-avx2.exe")
    file_path_json = './data/test/final_processed_index.json'
    os.makedirs(os.path.dirname(file_path_json), exist_ok=True)
    minimum_count = 1

    existing_positions_dict = {}  
    print('started')
    resulting_dict = analyze_positions(file_path, minimum_count, stockfish_path)

    print(len(resulting_dict))
    with open(file_path_json, 'w') as file:
        json.dump(resulting_dict, file, indent=4)
