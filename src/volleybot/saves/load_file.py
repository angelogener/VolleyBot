import csv
from typing import Any
from constructors.player import Player
from db.supabase import get_supabase_client

supabase = get_supabase_client()


def load_data():
    response = supabase.table('player_data').select("id, name, elo, wins, games_played").execute()
    players_response = response.data
    players = {}
    for player in players_response:
        new_player = Player(player['id'], player['name'], player['elo'], player['wins'], player['games_played'])
        players[player['id']] = new_player
    return players

def save_data(players: dict[int, Player]):
    for key, values in players.items():
        supabase.table('player_data').upsert({
            'id': key,
            'name': values.name,
            'elo': values.rating,
            'wins': values.wins,
            'games_played': values.games_played
        }).execute()

def load_data_old(file: str) -> dict[int, Player] | dict[Any, Any]:
    """
    :param file: The string name of the .csv file to be read.
    Instantiates Players and creates a dictionary of them.
    :return: A dictionary with Player ID's pointing to the Player.
    """
    try:
        players = {}

        with open(file, 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader, None)
            for row in csv_reader:
                print(row)
                player_num = int(row[0])
                player_name = row[1]
                player_ranking = int(row[2]) if row[2] else 0
                player_wins = int(row[3]) if row[3] else 0
                player_games = int(row[4]) if row[4] else 0
                new_player = Player(player_num, player_name, player_ranking, player_wins, player_games)
                players[player_num] = new_player
        return players
    except FileNotFoundError:
        return {}


def save_data_old(file: str, players: dict[int, Player]):
    """
    Writes the Player Data into the designated .csv file for saving.
    :param file: Name of the file to save data to
    :param players: The dictionary containing Player Data
    :return:
    """
    try:
        with open(file, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['Player ID', 'Player Names', 'Elo Rating', 'Wins', 'Total Games Played'])

            for key, values in players.items():
                csv_writer.writerow([str(key), values.name, values.rating, values.wins, values.games_played])

    except FileNotFoundError:
        print("File not Found")
