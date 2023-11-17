import random
from datetime import date
from player import Player
from team import Team
from game import Game
import bot


def generate_teams(people: list[Player]) -> list[Team]:
    """
    Generates random teams from a list of people attending a session.
    :param people: A list of Players
    :return: A list of Teams
    """
    teams = len(people) // 6
    team_lists = []
    counter = 0
    # Randomizes list of players
    random.shuffle(people)

    # Instantiate empty teams
    for i in range(teams):
        temp_team = Team("", date_string())
        team_lists.append(temp_team)

    # Numbers players as so: 1, 2, 3, 1, 2, 3 (etc. if at least 3 teams are made)
    for person in people:
        if counter == teams:
            counter = 0
        team_lists[counter].add_player(person)
        # Sets the first player of each team as it's respective captain.
        if len(team_lists[counter].get_players()) == 1:
            team_lists[counter].name = f"Team {person.name}"
        counter += 1

    return team_lists


def team_string(teams: list[Team]) -> str:
    formatted = f"The following teams on **{date_string()}** are: \n" + "\n"
    for team in teams:
        temp_team = team.get_players()
        for player in temp_team:
            # We assume that the first person is a team captain, list the number of players and re-add them
            if player == temp_team[0]:
                temp_string = f"***{team.get_team_name().title()}***" + f": **({len(temp_team)} Players)** \n"
                temp_string += f"***---------------***\n"
                temp_string += f" - {player.get_name().title()}\n"
            # Otherwise we just add them as normal
            else:
                temp_string = f" - {player.get_name().title()}\n"

            formatted += temp_string

            # If we are past the first team, add a new line character
            if player == temp_team[-1]:
                formatted += "\n"
    formatted += f"**Have fun!**"
    return formatted


def date_string() -> str:
    curr_date = date.today()
    to_format = curr_date.strftime("%A, %B %d")
    return to_format


"""
 a = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l']
    player_list = []
    num = 1
    for letter in a:
        player_list.append(Player(letter, num))

    random.shuffle(player_list)

    teams = [Team('Team 1', ''), Team('Team 2', '')]
    counter = 0

    for gamer in player_list:
        if counter == 2:
            counter = 0
        teams[counter].add_player(gamer)

        counter += 1

    game_one = Game(teams[0], teams[1], '')
    game_two = Game(teams[0], teams[1], '')
    game_three = Game(teams[0], teams[1], '')
    game_one.play_game('Team 1')
    game_two.play_game('Team 2')
    game_three.play_game('Team 1')

    last = teams[0].get_players()
    check = teams[1].get_players()
    for oop in last:
        print((oop.get_wins(), oop.get_name()))

    for ahh in check:
        print((ahh.get_wins(), ahh.get_name()))"""
