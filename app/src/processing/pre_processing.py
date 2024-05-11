def shortenGameMeta(games, player_name='Apendra'):
    games_shorter = []

    for game in games:
        if game.get('variant') == 'standard':
            moves_list = game.get('moves', '').split()
            midgame_index = game.get('division', {}).get('middle', 0)
            # Ensure we slice up to midgame + 8 moves
            moves_up_to_midgame_plus_8 = ' '.join(moves_list[:midgame_index + 8])

            # Determine the game outcome for the player
            if game.get('winner'):
                if game['players']['white']['user']['name'] == player_name and game['winner'] == 'white':
                    win_status = 'Won'
                elif game['players']['black']['user']['name'] == player_name and game['winner'] == 'black':
                    win_status = 'Won'
                elif game['winner'] != 'draw' and (game['players']['white']['user']['name'] == player_name or game['players']['black']['user']['name'] == player_name):
                    win_status = 'Lost'
                else:
                    win_status = 'Draw'
            else:
                win_status = 'Draw'  # Handle cases where there might not be a clear winner recorded

            # Convert createdAt to Unix time in milliseconds if it exists
            game_date_unix = int(game['createdAt']) if 'createdAt' in game else None

            game_meta = {
                'id': game.get('id'),
                'white_elo': game['players']['white'].get('rating', None),
                'black_elo': game['players']['black'].get('rating', None),
                'white_player': game['players']['white']['user'].get('name', None),
                'black_player': game['players']['black']['user'].get('name', None),
                'winner': game.get('winner'),
                'win_status': win_status,
                'ECO': game.get('opening', {}).get('eco', 'Unknown'),
                'opening_name': game.get('opening', {}).get('name', 'Unknown'),
                'game_type': f"{game.get('variant')} - {game.get('speed')} - {game.get('perf')}",
                'moves': moves_up_to_midgame_plus_8,
                'division': game.get('division', {}),
                'game_date_unix': game_date_unix  # Unix timestamp of the game creation
            }
            games_shorter.append(game_meta)

    return games_shorter
