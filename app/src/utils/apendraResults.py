import pandas as pd
import json

# Load your dataset
file_path = './data/processed/apendra_games.csv'
games_data = pd.read_csv(file_path)

def extract_date(headers):
    try:
        # Replace single quotes with double quotes and handle possible double quote escape issues
        headers_cleaned = headers.replace("\\\"", "\"").replace('"', '\\"').replace("\'", '"')
        header_json = json.loads(headers_cleaned)
        return header_json['_tag_roster']['Date']
    except json.JSONDecodeError as e:
        # Return None if there is an error, which we will filter out later
        return None

# Apply the function to extract dates
games_data['date'] = games_data['headers'].apply(extract_date)

# Define a function to select the player's Elo based on their color
def get_player_elo(row):
    if row['player_color'] == 'White':
        return row['white_elo']
    else:
        return row['black_elo']

# Apply the function to each row to get the player's Elo
games_data['player_elo'] = games_data.apply(get_player_elo, axis=1)

# Remove rows where the date is None
games_data = games_data[games_data['date'].notnull()]

# Generate the lists for dates and Elo ratings
dates = games_data['date'].tolist()
player_elos = games_data['player_elo'].tolist()

# Print the cleaned lists
print('Cleaned Dates:', dates)
print('Cleaned ELO:', player_elos)
