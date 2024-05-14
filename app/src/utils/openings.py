import pandas as pd

def process_openings():
    # Load the datasets
    apendra_path = './data/processed/apendra_games.csv'
    combined_path = './data/processed/combined_games_data_with_pgn_opening.csv'
    apendra_data = pd.read_csv(apendra_path)
    combined_data = pd.read_csv(combined_path)

    def extract_base_variation(opening):
        parts = opening.split(':')
        if len(parts) > 1:
            return parts[0].strip(), ':'.join(parts[1:]).strip()
        return parts[0].strip(), ''

    # Apply the function to both datasets
    apendra_data['opening_base'], apendra_data['opening_variation'] = zip(*apendra_data['opening_name'].map(extract_base_variation))
    combined_data['opening_base'], combined_data['opening_variation'] = zip(*combined_data['opening_name'].map(extract_base_variation))

    # Categorize results for apendra_data
    def categorize_result(score):
        if score == 1.0:
            return 'win'
        return 'not_win'

    apendra_data['result'] = apendra_data['score'].apply(categorize_result)

    # Group apendra_data to get total games and wins
    grouped_apendra = apendra_data.groupby(['player_color', 'opening_base', 'opening_variation']).agg(
        total_games=pd.NamedAgg(column='score', aggfunc='size'),
        win=pd.NamedAgg(column='result', aggfunc=lambda x: (x == 'win').sum())
    )

    # Calculate win rate
    grouped_apendra['win_rate'] = (grouped_apendra['win'] / grouped_apendra['total_games'] * 100).round(2)

    # Reset index to make sure everything is a column
    grouped_apendra.reset_index(inplace=True)

    # Determine if the URL ends with an even or odd number
    def url_ends_with_even_or_odd(row):
        last_char = row['url'][-1]
        if last_char.isdigit():
            return 'even' if int(last_char) % 2 == 0 else 'odd'
        return 'unknown'

    combined_data['url_even_odd'] = combined_data.apply(url_ends_with_even_or_odd, axis=1)

    # Filter combined_data based on player color and URL even/odd condition
    white_data_filtered = combined_data[
        (combined_data['player_color'] == 'White') & (combined_data['url_even_odd'] == 'odd')
    ]
    black_data_filtered = combined_data[
        (combined_data['player_color'] == 'Black') & (combined_data['url_even_odd'] == 'even')
    ]

    # Combine filtered white and black data
    combined_data_filtered = pd.concat([white_data_filtered, black_data_filtered])

    # Group combined_data_filtered to get average accuracy
    grouped_combined = combined_data_filtered.groupby(['player_color', 'opening_base', 'opening_variation'])['accuracy'].mean().reset_index()
    grouped_combined.rename(columns={'accuracy': 'average_accuracy'}, inplace=True)
    grouped_combined['average_accuracy'] = grouped_combined['average_accuracy'].round(2)

    # Merge the datasets
    final_grouped = pd.merge(grouped_apendra, grouped_combined, on=['player_color', 'opening_base', 'opening_variation'], how='left')

    # Remove rows where average_accuracy is NaN
    final_grouped = final_grouped.dropna(subset=['average_accuracy'])

    # Standardize player_color values to lowercase
    final_grouped['player_color'] = final_grouped['player_color'].str.lower()

    # Separate data for white and black
    white_data = final_grouped[final_grouped['player_color'] == 'white']
    black_data = final_grouped[final_grouped['player_color'] == 'black']

    # Filter openings played at least 5 times
    white_data = white_data[white_data['total_games'] >= 5]
    black_data = black_data[black_data['total_games'] >= 5]

    # Group by opening_base to get stats
    def get_top_openings(data):
        grouped = data.groupby('opening_base').agg(
            total_games=pd.NamedAgg(column='total_games', aggfunc='sum'),
            win=pd.NamedAgg(column='win', aggfunc='sum'),
            average_accuracy=pd.NamedAgg(column='average_accuracy', aggfunc='mean')
        ).reset_index()

        grouped['win_rate'] = (grouped['win'] / grouped['total_games'] * 100).round(2)
        grouped['average_accuracy'] = grouped['average_accuracy'].round(2)

        most_played = grouped.nlargest(5, 'total_games')
        highest_accuracy = grouped.nlargest(5, 'average_accuracy')
        lowest_accuracy = grouped.nsmallest(5, 'average_accuracy')

        return most_played, highest_accuracy, lowest_accuracy

    most_played_white, highest_accuracy_white, lowest_accuracy_white = get_top_openings(white_data)
    most_played_black, highest_accuracy_black, lowest_accuracy_black = get_top_openings(black_data)

    # Function to retrieve variations for a given base opening
    def get_variations(base_openings, original_data):
        variations_dict = {}
        for opening in base_openings['opening_base']:
            variations = original_data[original_data['opening_base'] == opening]
            variations_sorted = variations.sort_values('average_accuracy', ascending=False)
            variations_dict[opening] = variations_sorted[['opening_variation', 'total_games', 'win_rate', 'average_accuracy']].values.tolist()
        return variations_dict

    # Retrieve variations for each category
    most_played_variations_white = get_variations(most_played_white, white_data)
    highest_accuracy_variations_white = get_variations(highest_accuracy_white, white_data)
    lowest_accuracy_variations_white = get_variations(lowest_accuracy_white, white_data)

    most_played_variations_black = get_variations(most_played_black, black_data)
    highest_accuracy_variations_black = get_variations(highest_accuracy_black, black_data)
    lowest_accuracy_variations_black = get_variations(lowest_accuracy_black, black_data)

    # Convert to dictionaries for HTML table rendering
    most_played_white = most_played_white.to_dict('records')
    highest_accuracy_white = highest_accuracy_white.to_dict('records')
    lowest_accuracy_white = lowest_accuracy_white.to_dict('records')

    most_played_black = most_played_black.to_dict('records')
    highest_accuracy_black = highest_accuracy_black.to_dict('records')
    lowest_accuracy_black = lowest_accuracy_black.to_dict('records')
    
    return {
        'most_played_white': most_played_white,
        'highest_accuracy_white': highest_accuracy_white,
        'lowest_accuracy_white': lowest_accuracy_white,
        'most_played_black': most_played_black,
        'highest_accuracy_black': highest_accuracy_black,
        'lowest_accuracy_black': lowest_accuracy_black,
        'most_played_variations_white': most_played_variations_white,
        'highest_accuracy_variations_white': highest_accuracy_variations_white,
        'lowest_accuracy_variations_white': lowest_accuracy_variations_white,
        'most_played_variations_black': most_played_variations_black,
        'highest_accuracy_variations_black': highest_accuracy_variations_black,
        'lowest_accuracy_variations_black': lowest_accuracy_variations_black
    }
