import random

from db.supabase import get_supabase_client


def form_teams(session_id: int, num_teams: int):
    supabase_client = get_supabase_client()
    # Get all RSVPs for the session
    rsvps = supabase_client.table('rsvps').select('*').eq('session_id', session_id).eq('status', 'confirmed').order('order_position').execute().data

    # Get all existing users
    existing_users = supabase_client.table('users').select('id').execute().data
    existing_user_ids = set(user['id'] for user in existing_users)

    # Check and add new users
    new_users = []
    for rsvp in rsvps:
        if rsvp['user_id'] not in existing_user_ids:
            new_users.append({'id': rsvp['user_id']})  # Default ELO of 1000

    if new_users:
        supabase_client.table('users').insert(new_users).execute()

    # Get all groups for the session
    groups = supabase_client.table('player_groups').select('*').eq('session_id', session_id).execute().data
    group_members = supabase_client.table('player_group_members').select('*').execute().data

    # Organize players into groups and individuals
    grouped_players = {}
    individual_players = []
    for rsvp in rsvps:
        user_id = rsvp['user_id']
        is_grouped = False
        for group in groups:
            if any(gm['group_id'] == group['id'] and gm['user_id'] == user_id for gm in group_members):
                if group['id'] not in grouped_players:
                    grouped_players[group['id']] = []
                grouped_players[group['id']].append(user_id)
                is_grouped = True
                break
        if not is_grouped:
            individual_players.append(user_id)

    # Distribute groups and individuals among teams
    teams = [[] for _ in range(num_teams)]

    # First, distribute grouped players
    for _, players in grouped_players.items():
        team_index = min(range(num_teams), key=lambda i: len(teams[i]))
        teams[team_index].extend(players)

    # Then, distribute individual players
    random.shuffle(individual_players)
    for user_id in individual_players:
        team_index = min(range(num_teams), key=lambda i: len(teams[i]))
        teams[team_index].append(user_id)

    return teams

def form_balanced_teams(session_id: int, num_teams: int):
    DEFAULT_ELO = 1200
    supabase_client = get_supabase_client()

    # Get all RSVPs for the session
    rsvps = supabase_client.table('rsvps').select('user_id').eq('session_id', session_id).eq('status', 'confirmed').order('order_position').execute().data
    rsvp_user_ids = [rsvp['user_id'] for rsvp in rsvps]

        # Get all existing users
    existing_users = supabase_client.table('users').select('id').execute().data
    existing_user_ids = set(user['id'] for user in existing_users)

    # Check and add new users
    new_users = []
    for rsvp in rsvps:
        if rsvp['user_id'] not in existing_user_ids:
            new_users.append({'id': rsvp['user_id']})  # Default ELO of 1000

    if new_users:
        supabase_client.table('users').insert(new_users).execute()

    # Get ELO ratings for all RSVP'd users
    users = supabase_client.table('users').select('id, elo').in_('id', rsvp_user_ids).execute().data
    user_elos = {user['id']: user['elo'] for user in users}

    # Get all groups for the session
    groups = supabase_client.table('player_groups').select('*').eq('session_id', session_id).execute().data
    group_members = supabase_client.table('player_group_members').select('*').execute().data

    # Organize players into groups and individuals
    grouped_players = {}
    individual_players = []
    for rsvp_user_id in rsvp_user_ids:
        is_grouped = False
        for group in groups:
            if any(gm['group_id'] == group['id'] and gm['user_id'] == rsvp_user_id for gm in group_members):
                if group['id'] not in grouped_players:
                    grouped_players[group['id']] = []
                grouped_players[group['id']].append(rsvp_user_id)
                is_grouped = True
                break
        if not is_grouped:
            individual_players.append(rsvp_user_id)

    # Sort individual players by ELO
    individual_players.sort(key=lambda user_id: user_elos.get(user_id, DEFAULT_ELO), reverse=True)

    # Distribute groups and individuals among teams
    teams = [[] for _ in range(num_teams)]

    # First, distribute grouped players
    for group_id, players in grouped_players.items():
        team_index = min(range(num_teams), key=lambda i: sum(user_elos.get(user_id, DEFAULT_ELO) for user_id in teams[i]))
        teams[team_index].extend(players)

    # Then, distribute individual players
    team_elo_sums = [sum(user_elos.get(user_id, DEFAULT_ELO) for user_id in team) for team in teams]
    for user_id in individual_players:
        team_index = team_elo_sums.index(min(team_elo_sums))
        teams[team_index].append(user_id)
        team_elo_sums[team_index] += user_elos.get(user_id, DEFAULT_ELO)

    return teams
