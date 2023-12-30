# Boots up bot!
import bot
import atexit
import pandas as pd
from constructors.game import Game
from constructors.player import Player
from constructors.team import Team
from constructors.team_builder import generate_teams, generate_balanced, team_string
from saves.load_file import load_data, save_data

if __name__ == '__main__':

    bot.run_bot()
    atexit.register(lambda: save_data('player_data.csv', bot.save_players()))


    """
    all_players = load_data('player_data.csv')
    attended = (('Joaquin', 1), ('Angelo', 1), ('Simon2Coo', 1), ('Ashpan', 1),
                ('Anton', 1), ('Shermane', 1), ('Toseeteeto (Tyler)', 1), ('Anthony', 2),
                ('R3Dcyclic', 2), ('Jen', 2), ('Belle!', 2), ('Kibaaaaa', 2),
                ('John Scott', 2), ('Ryan Jay', 3), ('Hanasune', 3), ('Viv', 3),
                ('Baraka', 3), ('Funny Man', 3), ('Chris', 3), ('Chipsdude (Jasper)', 3))
    people = []
    nums = []
    for person in attended:
        people.append(person[0].lower())
        nums.append(person[1])

    team_one = Team('1', '')
    team_two = Team('2', '')
    team_three = Team('3', '')

    for key, players in all_players.items():
        if players.name in people:
            temp_ind = people.index(players.name)
            to_add = nums[temp_ind]
            match to_add:
                case 1:
                    team_one.add_player(players)
                case 2:
                    team_two.add_player(players)
                case 3:
                    team_three.add_player(players)

    order = (12, 23, 13, 12, 23, 13, 12, 23, 13)
    winner = (2, 2, 1, 2, 2, 3, 1, 2, 1)

    for i in range(len(order)):
        temp_teams = order[i]
        temp = winner[i]
        temp_game = Game(Team('', ''), Team('', ''))
        match temp_teams:
            case 12:
                temp_game = Game(team_one, team_two)
            case 13:
                temp_game = Game(team_one, team_three)
            case 23:
                temp_game = Game(team_two, team_three)

        temp_game.play_game(str(temp))
    save_data('player_data.csv', all_players)

    """
    """
    # Testing to make sure expected rating matches actual rating
    
    one = Player(1, '1', 1200, 0, 0)
    two = Player(2, '2', 1200, 0, 0)
    three = Player(3, '3', 1200, 0, 0)

    team_one = Team('1', '')
    team_one.add_player(one)

    team_two = Team('2', '')
    team_two.add_player(two)

    team_three = Team('3', '')
    team_three.add_player(three)

    order = (12, 23, 13, 12, 23, 13, 12, 23, 13)
    winner = (2, 2, 1, 2, 2, 3, 1, 2, 1)

    for i in range(len(order)):
        temp_teams = order[i]
        temp = winner[i]
        temp_game = Game(Team('', ''), Team('', ''))
        match temp_teams:
            case 12:
                temp_game = Game(team_one, team_two)
            case 13:
                temp_game = Game(team_one, team_three)
            case 23:
                temp_game = Game(team_two, team_three)

        temp_game.play_game(str(temp))

    print((team_one.average_rating(), team_one.get_record()))
    print((team_two.average_rating(), team_two.get_record()))
    print((team_three.average_rating(), team_three.get_record()))
    """



