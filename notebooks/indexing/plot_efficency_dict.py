import chess
import pandas as pd
import json
import matplotlib.pyplot as plt
from stockfish import Stockfish
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import joblib


def load_evaluations_cache():
    file_path = "../../data/indexed_positions/final_processed_index.json"
    with open(file_path, 'r') as file:
        cache = json.load(file)
    return cache


def initialize_stockfish(path, depth, skill_level):
    stockfish = Stockfish(path)
    stockfish.set_depth(depth)
    stockfish.set_skill_level(skill_level)
    return stockfish


def build_stored_game_analysis(game, move_number, stockfish, evaluations_cache):
    row = {}
    row['move_number'] = move_number
    board = chess.Board()

    for san in game.moves[:move_number]:
        move = board.parse_san(san)
        board.push(move)

    fen = board.fen()
    row['fen'] = fen
    row['cached'] = fen in evaluations_cache

    return row


def analyze_games(chunk, stockfish_path, depth, skill_level):
    stockfish = initialize_stockfish(stockfish_path, depth, skill_level)
    evaluations_cache = load_evaluations_cache()

    all_game_analysis = []
    for game in chunk.itertuples(index=False):
        if not game.moves:
            print(f"Skipping game with no moves: {game}")
            continue

        game_analysis = []
        move_number = 1

        while move_number <= len(game.moves):
            analysis_result = build_stored_game_analysis(game, move_number, stockfish, evaluations_cache)
            game_analysis.append(analysis_result)
            move_number += 1

        if game_analysis:
            df = pd.DataFrame(game_analysis)
            df.set_index('move_number', inplace=True)
            all_game_analysis.append(df)
        else:
            print(f"Skipping game with no valid analysis: {game}")

    return all_game_analysis


def parallel_game_analysis(games, stockfish_path, depth, skill_level, workers):
    chunk_size = len(games) // workers
    game_chunks = [games.iloc[i:i + chunk_size] for i in range(0, len(games), chunk_size)]
    args = [(chunk, stockfish_path, depth, skill_level) for chunk in game_chunks]

    results = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(analyze_games, *arg) for arg in args]
        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception as e:
                print(f"Error processing chunk: {e}")
    return results


def get_analyzed_games(games):
    n_games = len(games)
    print(len(games))
    skill_level = 1
    depth = 1
    num_threads = 4  # Adjust the number of threads as necessary
    stockfish_path = "C:/Users/aober/Documents/Data_Science_Studium/4Semester/BigData/stockfish/stockfish-windows-x86-64-avx2.exe"

    games = games[:n_games]
    games.loc[:, 'moves'] = games['moves'].apply(lambda x: x.split() if isinstance(x, str) else x)

    results = parallel_game_analysis(games, stockfish_path, depth, skill_level, num_threads)
    return results


def plot_cached_positions_distribution(all_game_analysis):
    move_numbers = []
    cached_counts = []
    not_cached_counts = []

    for game_df in all_game_analysis:
        move_numbers.extend(game_df.index)
        cached_counts.extend([1 if cached else 0 for cached in game_df['cached']])
        not_cached_counts.extend([0 if cached else 1 for cached in game_df['cached']])

    df = pd.DataFrame({
        'move_number': move_numbers,
        'cached': cached_counts,
        'not_cached': not_cached_counts
    })

    # Aggregate counts by move number
    aggregated_df = df.groupby('move_number').sum()

    # Limit to the first 30 moves
    aggregated_df = aggregated_df.head(30)

    # Plotting the stacked bar chart
    fig, ax = plt.subplots(figsize=(15, 6))
    ax.set_facecolor('beige')
    fig.patch.set_facecolor('beige')
    aggregated_df.plot(kind='bar', stacked=True, color=['#003f5c', '#ffa600'], alpha=0.75, edgecolor='black', ax=ax)
    plt.title('Cached vs. Not Cached Positions by Move Number (First 30 Moves)')
    plt.xlabel('Move Number')
    plt.ylabel('Count of Positions')
    plt.xticks(rotation=0)  # Keep the x-axis labels horizontal
    plt.grid(True)
    plt.show()

# Example usage (assuming 'all_game_analysis' is defined and populated)
# plot_cached_positions_distribution(all_game_analysis)



if __name__ == "__main__":
    file_name = "../../data/pipeline_test/processed_games.json"
    with open(file_name, 'r') as file:
        games = json.load(file)

    games = pd.DataFrame(games)
    analyzed_games = get_analyzed_games(games)

    plot_cached_positions_distribution(analyzed_games)
