import random
from datetime import date

from constructors.player import Player
from constructors.team import Team


def generate_balanced(people: list[Player]) -> dict[int, Team]:
    """
    Generates a dictionary of balanced teams from a list of people attending a session.
    Accounts for elo when making the teams. Higher rated players are split amongst each other
    and algorithm continues as we proceed through the list.
    We will aim to shuffle the order of Players so that skill distribution is not exposed
    when teams are made.
    :param people: A list of Players
    :return: A dict of Teams
    """
    teams = (len(people) // 6) if len(people) // 6 >= 2 else 2  # We get a minimum of 2 teams
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


def generate_teams(people: list[Player]) -> dict[int, Team]:
    """
    Generates a dictionary of random teams from a list of people attending a session.
    Teams each have at least 6 players and are numbered starting from 1.
    :param people: A list of Players
    :return: A dict of Teams
    """
    # Initialize variables
    teams = (len(people) // 6) if len(people) // 6 >= 2 else 2  # We get a minimum of 2 teams
    team_dict: dict[int, Team] = {}
    counter = 0

    # Randomizes list of players
    random.shuffle(people)

    # Prepares teams
    for i in range(teams):
        team_dict[i+1] = Team(i + 1)

    # Numbers players as so: 1, 2, 3, 1, 2, 3 (etc. if at least 3 teams are made)
    for person in people:
        if counter == teams:
            counter = 0
        team_dict[counter + 1].add_player(person)
        counter += 1

    return team_dict


def team_string(teams: dict[int, Team]) -> str:
    """
    Formats the string announcing the teams on the Discord Server
    :param teams: A dictionary containing the arrangement of Teams
    :return: A formatted string to be read, with Teams, Players and the Session Date.
    """
    formatted = f"The following teams on **{date_string()}** are: \n" + "\n"
    for team, players in teams.items():

        # List the team and its players
        temp_string = f"***Team {str(team)}***" + f": **({len(players.get_players())} Players)** \n"
        temp_string += f"***---------------***\n"
        formatted += temp_string

        for player in players.get_players():
            temp_string = f" - {player.get_name().title()}\n"
            formatted += temp_string

            # If we are past the first team, add a new line character
            if player == players.get_players()[-1]:
                formatted += "\n"

    formatted += f"**Have fun!**"
    return formatted


def date_string() -> str:
    """
    Gets the date of the game on the current day.
    :return: A string of the date
    """
    curr_date = date.today()
    to_format = curr_date.strftime("%A, %B %d")
    return to_format
