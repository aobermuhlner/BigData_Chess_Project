from flask import request, jsonify

from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import time
from datetime import datetime, timedelta


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



def get_equal_time_spans(start_date, end_date, num_spans):
    start = datetime.strptime(start_date, '%Y-%m-%d') if isinstance(start_date, str) else start_date
    end = datetime.strptime(end_date, '%Y-%m-%d') if isinstance(end_date, str) else end_date

    total_days = (end - start).days + 1
    span_length = total_days // num_spans
    extra_days = total_days % num_spans

    intervals = []
    interval_start = start

    for i in range(num_spans):
        if i < extra_days:
            interval_end = interval_start + timedelta(days=span_length)
        else:
            interval_end = interval_start + timedelta(days=span_length - 1)

        if interval_end > end:
            interval_end = end

        intervals.append((interval_start.strftime('%Y-%m-%d'), interval_end.strftime('%Y-%m-%d')))
        interval_start = interval_end + timedelta(days=1)

    return intervals



def fetch_games(username, color, game_types, rated, time_span):
    url = f"https://lichess.org/api/games/user/{username}"
    headers = {'Accept': 'application/x-ndjson'}
    params = {
        'color': color,
        'since': date_to_unix_ms(time_span[0]),
        'until': date_to_unix_ms(time_span[1]),
        'perfType': ",".join(game_types),
        'rated': 'true' if rated == 'yes' else 'false'
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.text.count('\n') + 1  # Returns the count of games
    else:
        return 0


def download_and_measure_games_multithreaded():
    username = "Apendra"
    color = "both"
    game_types = ["blitz", "bullet", "rapid"]
    rated = "yes"
    start_date = "2023-01-01"
    end_date = "2024-02-01"
    num_threads = 4

    # Get the timespans split into equal parts
    entire_timespan = get_equal_time_spans(start_date, end_date, num_threads)

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for timespan in entire_timespan:
            # Submit a single future for each timespan
            future = executor.submit(fetch_games, username, color, game_types, rated, timespan)
            time.sleep(0.8)
            futures.append(future)

        for future in as_completed(futures):
            try:
                game_count = future.result()
                print(f"Games fetched: {game_count}")
            except Exception as exc:
                print(f"Failed to fetch games: {exc}")




if __name__ == "__main__":
    start = time.time()
    download_and_measure_games_multithreaded()
    print("Duration: " , time.time() - start)

    username = "Apendra"
    color = "both"
    game_types = ["blitz", "bullet", "rapid"]
    rated = "yes"
    start_date = "2023-01-01"
    end_date = "2024-02-01"

    start = time.time()
    results = fetch_games(username,color,game_types,rated,[start_date,end_date])
    print(results, "games")
    print("Duration: " , time.time() - start)
