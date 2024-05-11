from flask import Flask, request, jsonify
import requests
from datetime import datetime


def download_games():
    # User input processing
    username = request.args.get('username')
    color = request.args.get('color', 'both')  # Default to 'both' if nothing is selected
    game_types = request.args.getlist('game_type')  # Retrieves all checked game types
    rated = request.args.get('rated', 'all')

    # Date processing: convert from YYYY-MM-DD to Unix timestamp in milliseconds
    since_date = request.args.get('since')
    until_date = request.args.get('until')
    since_unix_ms = date_to_unix_ms(since_date)
    until_unix_ms = date_to_unix_ms(until_date)

    # Building the URL and parameters for the API request
    url = f"https://lichess.org/api/games/user/{username}"
    headers = {'Accept': 'application/x-ndjson'}
    params = {
        'color': color,
        'since': since_unix_ms,
        'until': until_unix_ms,
        'perfType': ",".join(game_types) if game_types else None,
        'rated': 'true' if rated == 'yes' else 'false' if rated == 'no' else None
    }

    # Filter out None values from parameters
    params = {k: v for k, v in params.items() if v is not None}

    # Fetch the games
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        # Parse and return the response content directly as JSON
        return jsonify({'games': response.text}), 200
    else:
        return jsonify({'error': 'Failed to fetch games', 'status_code': response.status_code}), response.status_code

def date_to_unix_ms(date_str):
    """Converts a date string in YYYY-MM-DD format to Unix timestamp in milliseconds."""
    if date_str:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return int(dt.timestamp() * 1000)
    return None
