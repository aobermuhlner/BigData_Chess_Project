import pandas as pd
import tqdm
from stockfish import Stockfish
import chess
import chess.engine
from multiprocessing import Pool
import time

# Setup the stockfish engine
stockfish_good = Stockfish("C:/Users/flras/Documents/ZHAW_FS24/PM4/stockfish/stockfish-windows-x86-64-avx2.exe")
stockfish_good.set_depth(10)
stockfish_good.set_skill_level(10)

def get_fen_from_move_sequence(move_sequence):
    board = chess.Board()
    for move_san in move_sequence.split(' '):
        move = board.parse_san(move_san)
        board.push(move)
    return board.fen()

def get_evaluation(stockfish, fen):
    info = stockfish.analyse(chess.Board(fen), chess.engine.Limit(time=0.1))
    return info['score'].white().score(mate_score=10000)

def analyze_positions_chunk(chunk, stockfish_path):
    result_dict = {}
    with chess.engine.SimpleEngine.popen_uci(stockfish_path) as stockfish:
        for _, row in chunk.iterrows():
            position_string = row['position']
            fen = get_fen_from_move_sequence(position_string)
            evaluation = get_evaluation(stockfish, fen)
            result_dict[fen] = evaluation
    return result_dict

def analyze_positions(file_path, amount, stockfish_path, chunksize=1000):
    chunks = pd.read_csv(file_path, chunksize=chunksize)
    pool = Pool()  # Use default number of processes
    results = pool.starmap(analyze_positions_chunk, [(chunk, stockfish_path) for chunk in chunks])
    pool.close()
    pool.join()

    combined_results = {}
    for result in results:
        combined_results.update(result)

    return combined_results

if __name__ == '__main__':
    file_path = './data/test/final_processed_index.csv'
    stockfish_path = "C:/Users/flras/Documents/ZHAW_FS24/PM4/stockfish/stockfish-windows-x86-64-avx2.exe"
    minimum_count = 1000

    start_time = time.time()
    resulting_dict = analyze_positions(file_path, minimum_count, stockfish_path)
    end_time = time.time()

    execution_time = end_time - start_time
    print(resulting_dict)
    print("Execution time:", execution_time, "seconds")
