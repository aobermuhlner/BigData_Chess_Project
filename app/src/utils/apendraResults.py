import pandas as pd
import json

def load_data(file_path):
    return pd.read_csv(file_path)

def generate_table_data(df, group_col):
    grouped = df.groupby(group_col).agg(
        count=('accuracy', 'size'),
        avg_accuracy=('accuracy', 'mean')
    ).reset_index()
    grouped['avg_accuracy'] = grouped['avg_accuracy'].round(2)
    return grouped

def extract_date(headers):
    try:
        headers_cleaned = headers.replace("\\\"", "\"").replace('"', '\\"').replace("\'", '"')
        header_json = json.loads(headers_cleaned)
        return header_json['_tag_roster']['Date']
    except json.JSONDecodeError as e:
        return None

def get_player_elo(row):
    return row['white_elo'] if row['player_color'] == 'White' else row['black_elo']

def get_game_type(event):
    if 'Blitz' in event:
        return 'Blitz'
    elif 'Bullet' in event:
        return 'Bullet'
    elif 'Rapid' in event:
        return 'Rapid'
    else:
        return 'Other'

def prepare_time_scale_data(dates, elos):
    dates_sorted, elos_sorted = zip(*sorted(zip(dates, elos)))
    return list(dates_sorted), list(elos_sorted)

def process_combined_data(file_path):
    games_data_merged = load_data(file_path)
    
    game_results_aggregated = games_data_merged.groupby('score').size()
    game_types_aggregated = games_data_merged['ECO'].value_counts()

    most_played_openings_aggregated = generate_table_data(games_data_merged, 'opening_name').nlargest(5, 'count')
    mostPlayedOpeningsData = {
        'labels': most_played_openings_aggregated['opening_name'].tolist(),
        'datasets': [{
            'data': most_played_openings_aggregated[['count', 'avg_accuracy']].values.tolist(),
            'backgroundColor': ['#01161E', '#124559', '#598392', '#AEC3B0', '#929F93']
        }]
    }

    least_played_openings_aggregated = generate_table_data(games_data_merged, 'opening_name').nsmallest(5, 'count')
    leastPlayedOpeningsData = {
        'labels': least_played_openings_aggregated['opening_name'].tolist(),
        'datasets': [{
            'data': least_played_openings_aggregated[['count', 'avg_accuracy']].values.tolist(),
            'backgroundColor': ['#01161E', '#124559', '#598392', '#AEC3B0', '#929F93']
        }]
    }

    most_played_eco_aggregated = generate_table_data(games_data_merged, 'ECO').nlargest(5, 'count')
    mostPlayedEcoData = {
        'labels': most_played_eco_aggregated['ECO'].tolist(),
        'datasets': [{
            'data': most_played_eco_aggregated[['count', 'avg_accuracy']].values.tolist(),
            'backgroundColor': ['#01161E', '#124559', '#598392', '#AEC3B0', '#929F93']
        }]
    }

    least_played_eco_aggregated = generate_table_data(games_data_merged, 'ECO').nsmallest(5, 'count')
    leastPlayedEcoData = {
        'labels': least_played_eco_aggregated['ECO'].tolist(),
        'datasets': [{
            'data': least_played_eco_aggregated[['count', 'avg_accuracy']].values.tolist(),
            'backgroundColor': ['#01161E', '#124559', '#598392', '#AEC3B0', '#929F93']
        }]
    }

    return {
        'game_results_aggregated': game_results_aggregated,
        'game_types_aggregated': game_types_aggregated,
        'mostPlayedOpeningsData': mostPlayedOpeningsData,
        'leastPlayedOpeningsData': leastPlayedOpeningsData,
        'mostPlayedEcoData': mostPlayedEcoData,
        'leastPlayedEcoData': leastPlayedEcoData
    }

def process_apendra_data(file_path):
    games_data = load_data(file_path)
    
    games_data['date'] = games_data['headers'].apply(extract_date)
    games_data['player_elo'] = games_data.apply(get_player_elo, axis=1)
    games_data = games_data[games_data['date'].notnull()]
    games_data['game_type'] = games_data['event'].apply(get_game_type)

    blitz_games = games_data[games_data['game_type'] == 'Blitz']
    bullet_games = games_data[games_data['game_type'] == 'Bullet']
    rated_games = games_data[games_data['game_type'] == 'Rapid']

    dates_blitz, player_elos_blitz = prepare_time_scale_data(pd.to_datetime(blitz_games['date']).tolist(), blitz_games['player_elo'].tolist())
    dates_bullet, player_elos_bullet = prepare_time_scale_data(pd.to_datetime(bullet_games['date']).tolist(), bullet_games['player_elo'].tolist())
    dates_rated, player_elos_rated = prepare_time_scale_data(pd.to_datetime(rated_games['date']).tolist(), rated_games['player_elo'].tolist())

    dataElo = {
        'blitz': {
            'labels': dates_blitz,
            'data': player_elos_blitz
        },
        'bullet': {
            'labels': dates_bullet,
            'data': player_elos_bullet
        },
        'rapid': {
            'labels': dates_rated,
            'data': player_elos_rated
        }
    }

    results_count = games_data['score'].value_counts()
    total_games = results_count.sum()
    win_percentage = (results_count.get(1.0, 0) / total_games) * 100
    draw_percentage = (results_count.get(0.5, 0) / total_games) * 100
    loss_percentage = (results_count.get(0.0, 0) / total_games) * 100

    win_draw_loss_ratio = {
        'Win Percentage': round(win_percentage, 2),
        'Draw Percentage': round(draw_percentage, 2),
        'Loss Percentage': round(loss_percentage, 2)
    }

    gameResultsData = {
        'labels': ['Wins', 'Draws', 'Losses'],
        'datasets': [{
            'data': [round(win_percentage, 2), round(draw_percentage, 2), round(loss_percentage, 2)],
            'backgroundColor': ['#01161E', '#124559', '#598392']
        }]
    }

    return {
        'dataElo': dataElo,
        'win_draw_loss_ratio': win_draw_loss_ratio,
        'gameResultsData': gameResultsData
    }
