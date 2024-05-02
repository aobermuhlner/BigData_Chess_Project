import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import chess.pgn

def load_game_data():
    games = pd.read_json("../../testData/games_1000.json", orient='records', lines=True)
    return games

def load_game_analysis_data():
    with open("../../testData/games_analysis_1000.json", "r") as file:
        games_analysis = json.load(file)
    games_analysis = [pd.DataFrame(records) for records in games_analysis]
    return games_analysis

def map_sub_opening_names(games):
    eco = pd.read_csv("../../testData/ECO.csv")
    eco_dict = eco.set_index('ECO Code')['Name'].to_dict()
    games['sub_opening_name'] = games['ECO'].map(eco_dict)
    return games

def aggregate_data(games, games_analysis, player_color):
    index = games.index[games['player_color'] == player_color].tolist()
    games_analysis_filtered = [games_analysis[i] for i in index]
    games['average_accuracy'] = [np.mean(game["accuracy"]) for game in games_analysis_filtered]
    agg_data = games.groupby('sub_opening_name')['average_accuracy'].mean().reset_index(name='mean_accuracy')
    agg_data['count'] = games.groupby('sub_opening_name').size().reset_index(name='count')['count']
    return agg_data.sort_values('mean_accuracy', ascending=False)

def plot_data(agg_data, player_color, plot_type='bar'):
    plt.figure(figsize=(10, 6))
    if plot_type == 'bar':
        sns.barplot(x='mean_accuracy', y='sub_opening_name', data=agg_data, color='black')
        plt.title(f'Mean Accuracy by Main-Opening, playing {player_color}')
        plt.xlabel('Mean Accuracy')
        plt.ylabel('Sub-Opening Name')
    elif plot_type == 'scatter':
        sns.scatterplot(x='count', y='mean_accuracy', hue='sub_opening_name', data=agg_data, palette='tab10', s=100)
        plt.title(f'Accuracy vs. Count of Games by Main-Opening ({player_color})')
        plt.xlabel('Count of Games')
        plt.ylabel('Mean Accuracy')
        plt.legend(title='Sub-Opening Name')
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    games = load_game_data()
    games_analysis = load_game_analysis_data()
    games = map_sub_opening_names(games)

    white_agg_data = aggregate_data(games, games_analysis, "White")
    black_agg_data = aggregate_data(games, games_analysis, "Black")

    plot_data(white_agg_data, "white", plot_type='bar')
    plot_data(black_agg_data, "black", plot_type='bar')
    plot_data(white_agg_data, "white", plot_type='scatter')
    plot_data(black_agg_data, "black", plot_type='scatter')

