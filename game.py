import player
from team import Team
from team_builder import date_string


class Game:

    def __init__(self, team_one: Team, team_two: Team):
        self.team_one = team_one
        self.team_two = team_two
        self.date = date_string()
        self.winner = None

    def play_game(self, name: str):
        if name == self.team_one.get_team_name():
            self.winner = self.team_one
            self.team_one.team_win()
            self.team_two.team_loss()

        elif name == self.team_two.get_team_name():
            self.winner = self.team_two
            self.team_two.team_win()

    def get_event(self) -> tuple[Team, Team, str]:
        if self.winner is not None:
            if self.winner is self.team_one:
                return self.team_one, self.team_two, self.date

            if self.winner is self.team_two:
                return self.team_two, self.team_one, self.date

    def get_winner(self) -> Team:
        if self.winner is not None:
            return self.winner

    def get_teams(self) -> tuple[Team, Team]:
        return self.team_one, self.team_two

    def get_date(self) -> str:
        return self.date
