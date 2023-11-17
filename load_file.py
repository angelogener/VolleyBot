import csv
from typing import Dict, List, Any


def load_data(file: str) -> dict[str, list[int, str]] | dict[Any, Any]:
    try:
        players = {}
        with open(file, 'r') as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader, None)
            for row in csv_reader:
                player_num = int(row[0])
                player_name = row[1]
                player_wins = int(row[2]) if row[2] else 0
                player_games = int(row[3]) if row[3] else 0
                players[player_num] = [player_name, player_wins, player_games]
        return players
    except FileNotFoundError:
        return {}


def save_data(file: str, players: dict[str, list[str]]):
    try:
        with open(file, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(['Player ID', 'Player Names', 'Wins', 'Total Games Played'])

            for key, values in players.items():
                csv_writer.writerow([str(key), values[0].title()] + values[1:])

    except FileNotFoundError:
        print("File not Found")
