# Boots up bot!
import bot
import atexit

from constructors.game import Game
from constructors.player import Player
from constructors.team import Team
from constructors.team_builder import generate_teams, generate_balanced, team_string
from saves.load_file import load_data, save_data

if __name__ == '__main__':
    """
    # Runs the Bot
    bot.run_bot()
    atexit.register(lambda: save_data('player_data.csv', bot.save_players()))
    """

    """
    # This code is to fix incorrect/duplicated Player ID's
    all_players = load_data('player_data.csv')
    names = {}
    for player in all_players:
        temp_num = str(player)
        if all_players[player].get_name() not in names:
            if temp_num[-5:] != "00000":
                names[all_players[player].get_name()] = player

    new_players = {}
    for player in all_players:
        temp_player = all_players[player]
        temp_name = temp_player.get_name()
        if player not in new_players and temp_name in names:
            new_players[names[temp_name]] = temp_player
            new_players[names[temp_name]].disc_id = names[temp_name]

    save_data('player_data.csv', new_players)
    """

    # Manually creates games between players.
    all_players = load_data('player_data.csv')

    # Put Players with their Intended Teams
    with open('teams.txt', 'r') as file:
        lines = file.readlines()
    # Remove newline characters and empty lines
    teams_data = [line.strip() for line in lines if line.strip()]

    team_num = 0
    to_team = {}
    for item in teams_data:
        try:
            team_num = int(item)
        except ValueError:
            to_team[item.lower()] = team_num

    team_one = Team(1)
    team_two = Team(2)
    team_three = Team(3)
    team_four = Team(4)

    for key, players in all_players.items():
        if players.name in to_team:
            to_add = to_team[players.get_name()]
            match to_add:
                case 1:
                    team_one.add_player(players)
                case 2:
                    team_two.add_player(players)
                case 3:
                    team_three.add_player(players)
                case 4:
                    team_four.add_player(players)

    # Order: Put team numbers together for each game
    # Winner: Indicate each winner corresponding to the order
    order = (12, 34)
    winner = (2, 4)

    assert len(order) == len(winner)

    for i in range(len(order)):
        temp_teams = order[i]
        temp = winner[i]
        match temp_teams:
            case 12:
                temp_game = Game(team_one, team_two)
                temp_game.play_game(temp)
            case 13:
                temp_game = Game(team_one, team_three)
                temp_game.play_game(temp)
            case 14:
                temp_game = Game(team_one, team_four)
                temp_game.play_game(temp)
            case 23:
                temp_game = Game(team_two, team_three)
                temp_game.play_game(temp)
            case 24:
                temp_game = Game(team_two, team_four)
                temp_game.play_game(temp)
            case 34:
                temp_game = Game(team_three, team_four)
                temp_game.play_game(temp)

    save_data('player_data.csv', all_players)

    """"""
