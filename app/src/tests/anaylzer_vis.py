import json
import pandas as pd
import matplotlib.pyplot as plt

def load_analyzed_games_from_json(file_path):
    # Load the JSON file
    with open(file_path, 'r') as file:
        games_json = json.load(file)

    # Deserialize each JSON string back into a DataFrame
    analyzed_games = [pd.read_json(game_json, orient='records') for game_json in games_json]
    return analyzed_games

import matplotlib.pyplot as plt
import pandas as pd

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
    bins = range(7, 9)  # +2 to include the last move number

    # Calculate mean and median transition moves
    mean_transition_move = transition_df['transition_move'].mean()
    median_transition_move = transition_df['transition_move'].median()

    # Print the mean and median for user information
    print(f"Mean Transition Move: {mean_transition_move:.2f}")
    print(f"Median Transition Move: {median_transition_move}")

    # Plotting the distribution of transition moves
    plt.figure(figsize=(15, 6))  # Adjusted for better visibility of individual bars
    transition_df['transition_move'].hist(bins=bins, alpha=0.75, edgecolor='black')
    plt.title('Distribution of Opening to Middle Game Transition Moves')
    plt.xlabel('Transition Move Number')
    plt.ylabel('Frequency of Games')
    plt.xticks(bins)  # Set x-ticks to match the bins
    plt.grid(True)
    plt.show()

# Example usage would remain the same; ensure that 'all_game_analysis' is properly formatted


if __name__ == "__main__":
    output_file_path = "../../../data/pipeline_test/analyzed_positions.json"
    analyzed_games = load_analyzed_games_from_json(output_file_path)
    plot_transition_distribution(analyzed_games)
