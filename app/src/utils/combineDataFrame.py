import pandas as pd
import json

# Load the CSV file
csv_file_path = './data/processed/apendra_games.csv'
df_csv = pd.read_csv(csv_file_path)

# Load the JSON data
with open('./data/processed/apendra_games_analyzed.json', 'r') as file:
    json_data = json.load(file)

# Flatten the JSON data into a list of dataframes
json_dfs = [pd.DataFrame(records) for records in json_data]

# Concatenate the list of dataframes into a single dataframe
df_json = pd.concat(json_dfs, ignore_index=True)

# Extract the `lichess_id` from the `url` in the JSON dataframe
df_json['lichess_id'] = df_json['url'].apply(lambda x: x.split('#')[0])
df_json['move_number'] = df_json['url'].apply(lambda x: int(x.split('#')[1]))

# Merge the JSON dataframe with the CSV dataframe on the `lichess_id`
merged_df = pd.merge(df_json, df_csv, left_on='lichess_id', right_on='lichess_id', how='inner')

# Include PGN notation from the CSV dataframe
# Assuming 'moves' column in the CSV contains the PGN moves as a list
def get_pgn(moves, move_number):
    try:
        return moves.split(', ')[move_number - 1].strip("[]'")
    except IndexError:
        return None

merged_df['pgn'] = merged_df.apply(lambda row: get_pgn(row['moves'], row['move_number']), axis=1)

# Select relevant columns and rename them
final_df = merged_df[['lichess_id', 'url', 'fen', 'pgn', 'accuracy', 'evaluation', 'ECO', 'opening_name', 'player_color', 'score']]

# Save the final dataframe to a CSV file
output_file_path = 'combined_games_data_with_pgn_opening.csv'
final_df.to_csv(output_file_path, index=False)

print(f'Combined data saved to {output_file_path}')
