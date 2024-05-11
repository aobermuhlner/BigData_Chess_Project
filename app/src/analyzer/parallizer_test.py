from concurrent.futures import ProcessPoolExecutor
import json
import time

import pandas as pd

def load_and_expand_game_data(file_name, expansion_factor=1):
    """Load game data from a CSV file and optionally expand it for greater processing load."""
    games = pd.read_csv(file_name)
    # Optionally expand the dataset by repeating it
    games = pd.concat([games] * expansion_factor, ignore_index=True)
    return games

def process_game_data(games):
    """Simulate a time-consuming task on game data."""
    results = []
    # Dummy condition: simulate processing by checking if game index is even
    for index, game in games.iterrows():
        result = {
            'game_id': index,
            'is_even': index % 2 == 0
        }
        results.append(result)
    return results


def parallel_process_games(games, num_workers):
    """Run game data processing in parallel using a specified number of workers."""
    chunk_size = len(games) // num_workers
    game_chunks = [games.iloc[i:i + chunk_size] for i in range(0, len(games), chunk_size)]
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(process_game_data, game_chunks))
    return results

def load_game_data(file_name):
    """Load game data ensuring headers and moves are correctly parsed."""
    games = pd.read_csv(file_name)
    games['moves'] = games['moves'].apply(eval)  # Assuming moves are stored as stringified lists
    games['headers'] = games['headers'].apply(lambda x: json.loads(x) if isinstance(x, str) else x)
    return games
def main():
    file_name = "C:/Users/aober/Documents/Data_Science_Studium/4Semester/BigData/BigData_Chess_Project/data/processed/apendra_games.csv"

    expansion_factor = 50  # Increase to make the dataset larger if needed

    games = load_and_expand_game_data(file_name, expansion_factor)

    core_settings = [1, 2, 4,5,6,7, 8]  # Test with different number of cores

    for num_cores in core_settings:
        start_time = time.time()
        results = parallel_process_games(games, num_cores)
        duration = time.time() - start_time
        print(f"Time taken with {num_cores} cores: {duration:.2f} seconds")

if __name__ == "__main__":
    main()
