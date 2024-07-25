import random
from datetime import date

import discord

from constructors.player import Player
from constructors.team import Team
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


def generate_balanced(people: list[Player], num_teams: int = 2) -> dict[int, Team]:
    """
    Generates a dictionary of balanced teams from a list of people attending a session.
    Accounts for elo when making the teams. Higher rated players are split amongst each other
    and algorithm continues as we proceed through the list.
    We will aim to shuffle the order of Players so that skill distribution is not exposed
    when teams are made.
    :param people: A list of Players
    :param num_teams: An optional parameter for the max number of teams.
    :return: A dict of Teams
    """
    teams = max(num_teams, 2)  # We get a minimum of 2 teams
    team_dict: dict[int, Team] = {}
    counter = 0
    balance = sorted(people, key=lambda x: x.rating, reverse=True)  # Sorts players based on rating

    # Prepares teams
    for i in range(teams):
        team_dict[i + 1] = Team(i + 1)

    # Numbers players as so: 1, 2, 3, 1, 2, 3 (etc. if at least 3 teams are made)
    for person in balance:
        if counter == teams:
            counter = 0
        team_dict[counter + 1].add_player(person)
        counter += 1

    # Rearranges each team to avoid higher skilled players showing up top
    for team in team_dict.values():
        team.rearrange()
    return team_dict


async def generate_teams(people: list[int], num_teams: int = 2) -> dict[int, Team]:
    """
    Generates a dictionary of random teams from a list of people attending a session.
    Teams each have at least 6 players and are numbered starting from 1.
    :param people: A list of Players
    :param num_teams: An optional parameter for the max number of teams.
    :return: A dict of Teams
    """
    # Initialize variables

    # Uncomment to test with random players id's
    for _ in range(30):
        people.append(random.randint(1, 1000))

    supabase = get_supabase_client()
    teams = max(num_teams, 2)  # We get a minimum of 2 teams
    team_dict: dict[int, list[int]] = {}
    supabase.table('current_event').delete().neq('user_id', 0).execute()

    # Randomizes list of players
    random.shuffle(people)

    # Initialize empty lists for each team
    team_dict = {i + 1: [] for i in range(teams)}

    # Assign players to teams
    for person_iter, person in enumerate(people):
        team_number = (person_iter % teams) + 1
        team_dict[team_number].append(person)

    # Insert teams into the database
    team_object_array = [{'team': team, 'user_id': player} for team, players in team_dict.items() for player in players]
    print(team_object_array)
    supabase.table('current_event').insert(team_object_array).execute()

    return team_dict


def team_string() -> str:
    supabase = get_supabase_client()
    # DB will return an array of players and their teams
    # [ {team: 1, user_id: 1234}, {team: 2, user_id: 5678}, ... ]
    # We will convert this into a dictionary of teams and their players
    db_teams = supabase.table('current_event').select('*').execute().data
    teams = {}
    for team in db_teams:
        if team['team'] not in teams:
            teams[team['team']] = []
        teams[team['team']].append(team['user_id'])

    teams_embed = discord.Embed(title="Teams", description="The following teams are:", color=0x00ff00)
    for team in teams:
        teams_embed.add_field(name=f"Team {str(team)}", value=f"{', '.join(f'<@{player}>' for player in teams[team])}", inline=False)
    teams_embed.set_footer(text=f"Have fun!")
    return teams_embed


def date_string() -> str:
    """
    Gets the date of the game on the current day.
    :return: A string of the date
    """
    curr_date = date.today()
    to_format = curr_date.strftime("%A, %B %d")
    return to_format
