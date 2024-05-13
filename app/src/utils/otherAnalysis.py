import json
import pandas as pd
from collections import Counter


def analyze_game_results(games):
    """ Analyze games to prepare data for the game results chart. """
    results = [game['win_status'] for game in games]
    result_counts = Counter(results)
    return result_counts

def analyze_game_types(games):
    """ Analyze games to prepare data for the game type distribution chart. """
    types = [game['game_type'] for game in games]
    type_counts = Counter(types)
    return type_counts

def analyze_elo_development(games, player_name):
    """ Prepare data for Elo rating development chart. """
    elo_history = sorted([(game['game_date_unix'], game['white_elo'] if game['white_player'] == player_name else game['black_elo'])
                          for game in games if game['white_player'] == player_name or game['black_player'] == player_name],
                         key=lambda x: x[0])
    dates, elos = zip(*elo_history)
    return dates, elos

def analyze_openings(games):
    """ Analyze openings to find most and least used and their win rates. """
    openings = [game['opening_name'] for game in games]
    opening_counts = Counter(openings)
    most_common = opening_counts.most_common(5)
    least_common = opening_counts.most_common()[:-6:-1]
    return most_common, least_common

def load_json_data(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)

def analyze_move_frequencies(games):
    """Count occurrences of each move in the games."""
    move_counts = Counter()
    for game in games:
        moves = game['moves'].split()
        move_counts.update(moves)
    return move_counts

def analyze_move_outcomes(games):
    """Analyze the outcomes of each move."""
    move_outcomes = {}
    for game in games:
        moves = game['moves'].split()
        result = game['win_status']
        for move in moves:
            if move not in move_outcomes:
                move_outcomes[move] = {'Won': 0, 'Lost': 0, 'Draw': 0}
            move_outcomes[move][result] += 1
    return move_outcomes

if __name__ == "__main__":
    filepath = 'path_to_your_game_data.json'
    games = load_json_data(filepath)
    
    # Assuming 'games' is a list of dictionaries, each containing game metadata
    game_results = analyze_game_results(games)
    game_types = analyze_game_types(games)
    dates, elos = analyze_elo_development(games, 'Apendra')
    most_used_openings, least_used_openings = analyze_openings(games)
    
    print("Game Results:", game_results)
    print("Game Types:", game_types)
    print("Elo Development:", list(zip(dates, elos)))
    print("Most Used Openings:", most_used_openings)
    print("Least Used Openings:", least_used_openings)
