from math import pow

from db.supabase import get_supabase_client


def calculate_elo(my_rating: int, their_rating: int, games: int, is_winner: bool) -> int:
    """
    Precondition: win = 0 or 1
    Uses Elo's Formula to calculate a players new rating. Accounts for
    the difference in skill rating between the two players.


    :param my_rating: Player's Elo Rating
    :param their_rating: Another Player's Elo Rating or another
    Team's Average Rating
    :param games: The number of games the current Player has played.
    Determines the value to be gained/lost (k in formula)
    :param is_winner: True if the Player won. False if the Player lost.
    :return: The Player's new rank rating
    """

    """
    Similar to popular games using the Elo Method, we must use the first 5 games a baseline to
    easily determine the skill level of any given player. Hence we weight the first 5 games more to
    place them in their appropriate Elo ranking quickly.
    """
    k = 50 if games > 50 else 100

    den = 1 + pow(10, (their_rating - my_rating) / 400)
    estimate = 1 / den

    # Our formula adapts based on the success of the player
    if is_winner:
        new_rating = my_rating + round(k*(1 - estimate))
    else:
        new_rating = my_rating - round(k * estimate)
    return new_rating

def update_elo(winning_id, losing_id):
    supabase_client = get_supabase_client()

    # Get the winning and losing team members user id's
    winning_team_members = supabase_client.table('team_members').select('user_id').eq('team_id', winning_id).execute().data
    losing_team_members = supabase_client.table('team_members').select('user_id').eq('team_id', losing_id).execute().data
    winning_team_members = [member['user_id'] for member in winning_team_members]
    losing_team_members = [member['user_id'] for member in losing_team_members]

    # Calcuate average elo of each team
    winning_team_elo = 0
    losing_team_elo = 0
    for member in winning_team_members:
        user = supabase_client.table('users').select('elo').eq('id', member).execute().data[0]
        winning_team_elo += user['elo']
    for member in losing_team_members:
        user = supabase_client.table('users').select('elo').eq('id', member).execute().data[0]
        losing_team_elo += user['elo']
    winning_team_elo = winning_team_elo / len(winning_team_members)
    losing_team_elo = losing_team_elo / len(losing_team_members)

    # Update elo for each team member
    for member in winning_team_members:
        user = supabase_client.table('users').select('elo', 'games_played').eq('id', member).execute().data[0]
        new_elo = calculate_elo(user['elo'], losing_team_elo, user['games_played'], True)
        supabase_client.table('users').update({'elo': new_elo, 'games_played': user['games_played'] + 1}).eq('id', member).execute()
    for member in losing_team_members:
        user = supabase_client.table('users').select('elo', 'games_played').eq('id', member).execute().data[0]
        new_elo = calculate_elo(user['elo'], winning_team_elo, user['games_played'], False)
        supabase_client.table('users').update({'elo': new_elo, 'games_played': user['games_played'] + 1}).eq('id', member).execute()