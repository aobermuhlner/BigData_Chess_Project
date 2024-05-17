import pandas as pd

def load_and_aggregate_data():
    # Load the data
    games_data = pd.read_csv('./data/processed/combined_games_data_with_pgn_opening.csv')
    games_data['move_number'] = games_data['url'].str.extract(r'(\d+)$').astype(int)

    # Calculate the average accuracy per move
    white_moves = games_data[games_data['move_number'] % 2 == 1]
    black_moves = games_data[games_data['move_number'] % 2 == 0]
    white_avg_accuracy = white_moves.groupby(['opening_name', 'player_color', 'move_number'])['accuracy'].mean().reset_index()
    black_avg_accuracy = black_moves.groupby(['opening_name', 'player_color', 'move_number'])['accuracy'].mean().reset_index()
    avg_accuracy_per_move = pd.concat([white_avg_accuracy, black_avg_accuracy]).reset_index(drop=True)

    # Get unique combinations of opening_name and player_color
    unique_combinations = avg_accuracy_per_move[['opening_name', 'player_color']].drop_duplicates().reset_index(drop=True)
    
    return avg_accuracy_per_move, unique_combinations
