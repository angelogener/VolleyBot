from Player import Player


class Team:
    """
    A full Volleyball Team composed of Players.

    Attributes:
        name (str): The name of the Team.
        players (list[Player]): The list containing the Players in the team.
        record (int): The number of wins accumulated by this team.
    """
    def __init__(self, name, date):
        self.name = name
        self.players = []
        self.record = 0
        self.date = date

    def __eq__(self, other):
        if isinstance(other, Team):
            return (self.name, self.players, self.record, self.date) == \
                (other.name, other.players, other.record, other.date)

    def add_player(self, player: Player):
        """
        Adds a player to the team.
        :param player: The Player to be added to this Team.
        :return: Null
        """
        self.players.append(player)

    def remove_player(self, player: Player):
        """
        Removes a player from the team, if they are in the team.
        :param player: The Player to remove from this Team.
        :return: Null
        """
        if player in self.get_players():
            self.players.remove(player)

    def team_win(self):
        """
        Declares all players on a team as winners. Adds to total wins.
        :return: Null
        """
        self.record += 1
        for player in self.players:
            player.win()

    def team_loss(self):
        """
        Declares all players as losers.
        :return: Null
        """
        for player in self.players:
            player.loss()

    def get_players(self) -> list[Player]:
        """
        Returns a list of the players in the team.
        :return: The Players in the team.
        """
        return self.players

    def get_team_name(self) -> str:
        """
        Returns a name of the team.
        :return: The team name
        """
        return self.name

    def get_record(self) -> int:
        """
        Returns the record of the team.
        :return: The number of wins by a team.
        """
        return self.record
