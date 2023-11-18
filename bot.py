import asyncio
import discord

import team_builder
from game import Game
from team import Team
from player import Player
from discord.ext import commands

from team_builder import generate_teams
from load_file import load_data

# Global Variables
TOKEN = 'MTE2ODczODc0OTYzMTQzMDY3Nw.GTvqq2.xLhbp2tVygrQNol4UojlrrRD-7THpgLYCOZcGc'  # Replace with your bot token
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

all_players = {}  # All users in server
players = []  # Player ID's with their Names for team builder
teams = {}  # A list of Teams
curr_game = None
curr_guild = None
in_channel = None
out_channel = None


@bot.event
async def on_ready():
    """
    Prepares the bot for use. Will load player data.
    :return: None
    """
    global all_players
    all_players = load_data('player_data.csv')

    print(f'{bot.user} is now running!')


@bot.command()
async def shuffle(ctx):
    global teams
    # Specifically add Planners as the sole role capable of using this command
    role_access = discord.utils.get(ctx.guild.roles, name="Planners")

    if role_access not in ctx.author.roles:
        # Non-planners will get no response
        return

    if not players:
        await out_channel.send(f"Please update first!")
        return
    # In the case we try to make teams with less than 12 players
    if len(players) < 12:
        await out_channel.send(f"You currently have **{len(players)} players.**\n"
                               f"You will need **{12 - len(players)} more players** to make at least two teams!")
        return

    # Now create teams...
    curr_players = []
    for num in players:
        curr_players.append(all_players[num])

    teams = generate_teams(curr_players)
    result = team_builder.team_string(teams)
    # Simulate typing! Makes bot look busy
    async with out_channel.typing():
        await asyncio.sleep(2)

    await out_channel.send(result)
    return


@bot.command()
async def creategame(ctx, *, disc_teams: str):
    """
    Creates a Game object from the Two teams.
    :param ctx: The message
    :param disc_teams: The string containing the Teams to pit against.
    :return: None
    """
    global curr_game

    if not teams:
        await out_channel.send("Please make teams first!")
        return
    opponents = disc_teams.lower().split(',')
    gamers = []
    # Handles case where there weren't exactly "teams" within the string
    if len(opponents) != 2:
        await out_channel.send("Must input two valid team names!")
        return
    # Off case where both strings identical. Weird right?
    if opponents[0] == opponents[1]:
        await out_channel.send("Can't have the team play itself! What?")
        return

    # Get the two Teams for the brawl! Checks if both teams exist in the current team dictionary
    if opponents[0].strip() in teams:
        gamers.append(teams[opponents[0].strip()])
    else:
        await out_channel.send("Game could not be played. Please add two valid teams.")
        return

    if opponents[1].strip() in teams:
        gamers.append(teams[opponents[1].strip()])
    else:
        await out_channel.send("Game could not be played. Please add two valid teams.")
        return

    curr_game = Game(gamers[0], gamers[1])
    # Simulate typing! Makes bot look busy
    async with out_channel.typing():
        await asyncio.sleep(2)
    await out_channel.send(f"Prepare for the following matchup: \n"
                           f"***Team {curr_game.team_one.get_team_name().title()}*** vs "
                           f"***Team {curr_game.team_two.get_team_name().title()}***")
    return


@bot.command()
async def update(ctx):
    """
    Get the players that have last RSVP'd to the latest session and update the current
    list of players.
    :param ctx: The Message
    :return: None
    """

    # Obtain the server that the message was sent in
    global curr_guild, in_channel, out_channel, players
    curr_guild = ctx.guild

    # Obtain this server's instance of Polls and Teams
    for text in curr_guild.text_channels:
        if text.name.lower() == "polls":
            in_channel = curr_guild.get_channel(text.id)
        elif text.name.lower() == "teams":
            out_channel = curr_guild.get_channel(text.id)
    await out_channel.send("Obtained channels!")

    # Specifically add Planners as the sole role capable of using this command
    role_access = discord.utils.get(curr_guild.roles, name="Planners")

    if role_access not in ctx.author.roles:
        # Non-planners will get no response
        await ctx.send("You don't have the necessary permissions to use this command.")
        return

    try:
        # Instantiate the checkmark emoji
        checkmark = '\U00002705'  # Unicode for the checkmark emoji
        reacted = []

        # Parse through the most recent 50 messages
        async for msg in in_channel.history(limit=5):

            # Checks if each of the last 50 messages contains the checkmark emoji
            if checkmark in [reaction.emoji for reaction in msg.reactions]:

                # Now goes through each of the users that reacted
                async for user in msg.reactions[0].users():
                    reacted.append(user.id)
                # We obtain all the users who reacted and fetch nicknames (if they have any)
                # We then try to add them to our list of players
                await out_channel.send(f"Updating player roster!")

                await update_players(reacted)
                players = reacted
                # Simulate typing! Makes bot look busy
                async with out_channel.typing():
                    await asyncio.sleep(2)
                await out_channel.send(f"Ready!")

                return
        else:
            await out_channel.send("No recent reactions found with the specified emoji.")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")


@bot.command()
async def clear(ctx, value: int):
    """
    Purges the last 20 messages.
    """

    # Specifically add Planners as the sole role capable of using this command
    role_access = discord.utils.get(ctx.guild.roles, name="Planners")

    if role_access not in ctx.author.roles:
        # Non-planners will get no response
        await ctx.send("You don't have the necessary permissions to use this command.")
        return
    assert isinstance(value, int), await out_channel.send(f"Not a valid number!")
    assert 0 < value < 50, await out_channel.send(f"Can only be between 1 and 50 messages!")

    await ctx.channel.purge(limit=value + 1)  # Limit is set to '20 + 1' to include the command message
    await ctx.send(f'Cleared the last {value} messages.',
                   delete_after=5)  # Delete the confirmation message after 5 seconds


async def update_players(ids: list[str]) -> None:
    """
    Creates a dict of Players who RSVP'd and compares them to the players in the .csv file
    (players = {}) to see if any changes are to be made.
    Changes are made IF:
        - The player has been saved but has changed their display name (1)
        - The player does not yet exist in the data (1)

    Runs data through clean() to ensure we get the best possible username for teams and sharing.

    :param ids: A list containing the id's of players.
    :return: None
    """

    global all_players
    updated = {}
    for reacted in ids:
        member = await curr_guild.fetch_member(reacted)

        # 1: The player has been saved but has changed their display name
        if member.id in all_players and member.display_name != all_players[member.id].name:
            if clean(member.display_name):
                # Changes all_players directly
                all_players[member.id].name = member.display_name.lower()

        # 2: The player does not yet exist in the data
        elif member.id not in all_players:
            if clean(member.display_name):
                updated[member.id] = Player(member.id, member.display_name.lower(), 1200, 0, 0)
            else:
                updated[member.id] = Player(member.id, member.name.lower(), 1200, 0, 0)

    all_players.update(updated)


@bot.command()
async def winner(ctx, champ: str):
    """
    Declares the winning team of the game! Ensures all players from each team
    gets their ratings updated
    :param ctx: The message.
    :param champ: The string representation of the winning team
    :return: None
    """
    global curr_game
    if not curr_game:
        await out_channel.send("Please make a game first!")
        return

    if champ.lower() not in curr_game.get_team_names():
        await out_channel.send(f"Please enter a valid winner!")
        return

    curr_game.play_game(champ.lower())
    # Simulate typing! Makes bot look busy // ADDS SUSPENSE MUAHHAAH
    async with out_channel.typing():
        await asyncio.sleep(2)
    await out_channel.send(f"Congratulations to ***{curr_game.get_winner().get_team_name()}*** for taking the cake!")
    # Game is done! So we have no more current game!
    curr_game = None


@bot.command()
async def delete(ctx, to_delete: str):
    """
    Delete the specified team.
    :param ctx: The message
    :param to_delete: The string representation of the team to be deleted
    :return: None
    """
    global teams
    if to_delete.lower() not in teams:
        await out_channel.send(f"Please enter a valid team")
        return

    del teams[to_delete.lower()]


def save_players():
    """
    In the event that the bot ends, main.py will receive the latest iteration of players, and
    in turn write and save it to a file.
    """
    return all_players


def clean(username: str) -> bool:
    """
    Checks if the username is a "clean" string that can be used in csv for saving
    :param username: The username to check
    :return: True if username can be used in csv
    """
    return isinstance(username, str) and all(ord(char) < 128 for char in username)


def run_bot():
    bot.run(TOKEN)
