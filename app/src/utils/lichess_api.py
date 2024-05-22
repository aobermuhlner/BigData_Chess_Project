import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import json

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
        'since': date_to_unix_ms(time_span[0]),
        'until': date_to_unix_ms(time_span[1]),
        'perfType': ",".join(game_types)
    }
    if color in ['black', 'white']:
        params['color'] = color
    if rated == 'yes':
        params['rated'] = 'true'
    elif rated == 'no':
        params['rated'] = 'false'
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.text  # Return the raw ndjson data
    else:
        return None

def download_and_measure_games_multithreaded(username, since_date, until_date, color, rated, game_types):
    num_threads = 4

    # Get the timespans split into equal parts
    entire_timespan = get_equal_time_spans(since_date, until_date, num_threads)
    results = []

    print('in download')
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for timespan in entire_timespan:
            # Submit a single future for each timespan
            future = executor.submit(fetch_games, username, color, game_types, rated, timespan)
            time.sleep(10.0)  # Adjust sleep if necessary to avoid rate limiting
            futures.append(future)

        for future in as_completed(futures):
            try:
                game_data = future.result()
                print(f"Games fetched for timespan {timespan}: {len(game_data.splitlines())} games")
                if game_data:
                    results.extend(game_data.splitlines())  # Split ndjson into individual JSON objects and extend the results list
            except Exception as exc:
                print(f"Failed to fetch games: {exc}")

    # Convert results from ndjson to a list of JSON objects
    games_list = [json.loads(game) for game in results]
    return {'total_games': len(games_list), 'games': games_list}
