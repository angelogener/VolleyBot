import bot
import atexit
from game import Game
from team import Team
from player import Player
from load_file import save_data

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    bot.run_bot()
    atexit.register(lambda: save_data('player_data.csv', bot.save_players()))
