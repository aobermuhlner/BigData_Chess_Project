import time
import pandas as pd
from pathlib import Path
from analysis_test import load_game_data, parallel_game_analysis

def run_efficiency_test(file_name, stockfish_path, depth, skill_level, n_games, max_move_number):
    games = load_game_data(file_name)
    games = games.iloc[:n_games]  # Ensure you're slicing correctly
    results = {}

    for workers in range(1, 9):  # Testing with 1 to 8 workers
        start_time = time.time()
        result = parallel_game_analysis(games, max_move_number, stockfish_path, depth, skill_level, workers)
        duration = time.time() - start_time
        results[workers] = duration
        print(f"Time taken with {workers} workers: {duration:.2f} seconds")

    # Save results to a text file
    results_path = Path(__file__).parent / "efficiency_results.txt"
    with open(results_path, "w") as file:
        for workers, duration in results.items():
            file.write(f"{workers} workers: {duration:.2f} seconds\n")

    return results

if __name__ == "__main__":
    file_name = "apendra_games"
    stockfish_path = "C:/Users/aober/Documents/Data_Science_Studium/4Semester/BigData/stockfish/stockfish-windows-x86-64-avx2.exe"
    depth = 15
    skill_level = 10
    n_games = 10
    max_move_number = 10

    # Running the efficiency test
    run_efficiency_test(file_name, stockfish_path, depth, skill_level, n_games, max_move_number)
