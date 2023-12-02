import asyncio
import discord

from game import Game
from player import Player
from team import Team
from discord.ext import commands

from team_builder import generate_teams, generate_balanced, team_string
from load_file import load_data, save_data

# Global Variables
FILE_NAME = 'player_data.csv'
TOKEN = 'MTE2ODczODc0OTYzMTQzMDY3Nw.GTvqq2.xLhbp2tVygrQNol4UojlrrRD-7THpgLYCOZcGc'  # Replace with your bot token
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

all_players: dict[int, Player]  # All users in server
players: list[int]  # Player ID's with their Names for team builder
teams: dict[str, Team]  # A list of Teams
curr_game: Game  # The current Game
curr_guild: discord.guild  # The current Guild


@bot.event
async def on_ready():
    """
    Prepares the bot for use. Will load player data.
    :return: None
    """
    global all_players
    all_players = load_data(FILE_NAME)

    print(f'{bot.user} is now running!')


@bot.command()
async def shuffle(ctx):
    """
    Shuffle users that RSVP'd into teams.
    :param ctx: The Message
    :return: None
    """
    global teams

    # Delete the command message
    await ctx.message.delete()
    await ctx.send(f"_ _")
    """
    # Specifically add Planners as the sole role capable of using this command
    role_access = discord.utils.get(ctx.guild.roles, name="Planners")

    if role_access not in ctx.author.roles:
        # Non-planners will get no response
        return
    """
    if not players:
        await ctx.send(f"Please update first!")
        return

    await ctx.send(f"You currently have **{len(players)} players.**")  # Output the number of players

    # In the case we try to make teams with less than 12 players
    if len(players) < 12:
        await ctx.send(f"You will need **{12 - len(players)} more players** to make at least two full teams! \n"
                       f"_ _")

    # Now create teams...
    curr_players = []
    for num in players:
        curr_players.append(all_players[num])

    teams = generate_teams(curr_players)
    result = team_string(teams)
    # Simulate typing! Makes bot look busy
    async with ctx.typing():
        await asyncio.sleep(2)

    await ctx.send(result)
    return


@bot.command()
async def balance(ctx):
    """
    Matchmake the users that RSVP'd into balanced teams.
    :param ctx: The Message
    :return: None
    """
    global teams

    # Delete the command message
    await ctx.message.delete()
    await ctx.send(f"_ _")

    # Specifically add Planners as the sole role capable of using this command
    role_access = discord.utils.get(ctx.guild.roles, name="Planners")

    if role_access not in ctx.author.roles:
        # Non-planners will get no response
        return

    if not players:
        await ctx.send(f"Please update first!")
        return

    await ctx.send(f"You currently have **{len(players)} players.**")  # Output the number of players

    # In the case we try to make teams with less than 12 players
    if len(players) < 12:
        await ctx.send(f"You will need **{12 - len(players)} more players** to make at least two full teams! \n"
                       f"_ _")
    # Now create teams...
    curr_players = []
    for num in players:
        curr_players.append(all_players[num])

    teams = generate_balanced(curr_players)
    result = team_string(teams)
    # Simulate typing! Makes bot look busy
    async with ctx.typing():
        await asyncio.sleep(2)

    await ctx.send(result)
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

    # Delete the command message
    await ctx.message.delete()
    await ctx.send(f"_ _")

    # Specifically add Planners as the sole role capable of using this command
    role_access = discord.utils.get(ctx.guild.roles, name="Planners")

    if role_access not in ctx.author.roles:
        # Non-planners will get no response
        return

    if not teams:
        await ctx.send("Please make teams first!")
        return

    opponents = disc_teams.lower().split(',')
    gamers = []

    # Handles case where there weren't exactly "teams" within the string
    if len(opponents) != 2:
        await ctx.send("Must input two valid team names!")
        return
    # Off case where both strings identical. Weird right?
    if opponents[0] == opponents[1]:
        await ctx.send("Can't have the team play itself! What?")
        return

    # Get the two Teams for the brawl! Checks if both teams exist in the current team dictionary
    if opponents[0].strip() in teams:
        gamers.append(teams[opponents[0].strip()])
    else:
        await ctx.send("Game could not be played. Please add two valid teams.")
        return

    if opponents[1].strip() in teams:
        gamers.append(teams[opponents[1].strip()])
    else:
        await ctx.send("Game could not be played. Please add two valid teams.")
        return

    curr_game = Game(gamers[0], gamers[1])
    # Simulate typing! Makes bot look busy
    async with ctx.typing():
        await asyncio.sleep(2)
    await ctx.send(f"Prepare for the following matchup: \n"
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
    global curr_guild, players
    curr_guild = ctx.guild

    # Delete the command message
    await ctx.message.delete()
    await ctx.send(f"**---------------**\n" + f"**Updating...**\n" + f"_ _")
    """
    # Specifically add Planners as the sole role capable of using this command
    role_access = discord.utils.get(curr_guild.roles, name="Planners")
    if role_access not in ctx.author.roles:
        # Non-planners will get no response
        await ctx.send("You don't have the necessary permissions to use this command.")
        return
    """
    # Obtain this server's latest Volleyball event
    events = await curr_guild.fetch_scheduled_events()

    # If no event was created
    if len(events) == 0:
        await ctx.send("Please make an event first!")
        return

    curr_event = events[0]
    await ctx.send("Obtained players who RSVP'd! Thank you signing up!")

    try:
        reacted = []

        # Now goes through each of the users that reacted
        async for user in curr_event.users():
            reacted.append(user.id)

        # We obtain all the users who indicated they are coming and fetch nicknames (if they have any)
        # We then try to add them to our list of players
        await ctx.send(f"Updating player roster!")

        await update_players(reacted)
        players = reacted

        # Simulate typing! Makes bot look busy
        async with ctx.typing():
            await asyncio.sleep(2)
        await ctx.send(f"Ready!")

        return

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")


@bot.command()
async def rsvp(ctx, *members: commands.MemberConverter):
    """
    For players who did not RSVP but arrived, add them to the list of players.
    :param ctx: The Message.
    :param members: An unspecified number of users to add.
    :return:
    """

    # Obtain the server that the message was sent in
    global curr_guild, players
    curr_guild = ctx.guild

    # Delete the command message
    await ctx.message.delete()
    await ctx.send(f"**---------------**\n" + f"**Updating...**\n" + f"_ _")

    late = []
    try:
        # Now goes through each of the users that reacted
        late = [member.id for member in members]

        # We obtain all the users who indicated they are coming and fetch nicknames (if they have any)
        # We then try to add them to our list of players
        await ctx.send(f"Adding players!")
        await update_players(late)

        temp_list = set(late) - set(players)  # Obtain unique players
        players.extend(temp_list)

        # Simulate typing! Makes bot look busy
        async with ctx.typing():
            await asyncio.sleep(2)
        await ctx.send(f"Ready!")
        return

    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

@bot.command()
async def clear(ctx, value: int):
    """
    Purges the last couple of messages, determined by value.
    """

    # Specifically add Planners as the sole role capable of using this command
    role_access = discord.utils.get(ctx.guild.roles, name="Planners")

    """if role_access not in ctx.author.roles:
        # Non-planners will get no response
        await ctx.send("You don't have the necessary permissions to use this command.")
        return"""
    assert isinstance(value, int), await ctx.send(f"Not a valid number!")
    assert 0 < value < 51, await ctx.send(f"Can only be between 1 and 50 messages!")

    await ctx.channel.purge(limit=value + 1)  # Limit is set to "20 + 1" to include the command message
    await ctx.send(f'Cleared the last {value} messages.',
                   delete_after=5)  # Delete the confirmation message after 5 seconds


@bot.command()
async def winner(ctx, champ: str):
    """
    Declares the winning team of the game! Ensures all players from each team
    gets their ratings updated.
    :param ctx: The message.
    :param champ: The string representation of the winning team
    :return: None
    """
    global curr_game

    # Delete the command message
    await ctx.message.delete()
    await ctx.send(f"_ _")

    # Specifically add Planners as the sole role capable of using this command
    role_access = discord.utils.get(ctx.guild.roles, name="Planners")

    if role_access not in ctx.author.roles:
        # Non-planners will get no response
        return

    if not curr_game:
        await ctx.send("Please make a game first!")
        return

    if champ.lower() not in curr_game.get_team_names():
        await ctx.send(f"Please enter a valid winner!")
        return

    curr_game.play_game(champ.lower())
    # Simulate typing! Makes bot look busy // ADDS SUSPENSE MUAHHAAH
    async with ctx.typing():
        await asyncio.sleep(2)
    await ctx.send(f"Congratulations to ***{curr_game.get_winner().get_team_name().title()}*** for taking the "
                   f"cake!")
    # Game is done! So we have no more current game!
    curr_game = None

    # Now we update the .csv with the changes
    save_data(FILE_NAME, all_players)


@bot.command()
async def deleteteam(ctx, to_delete: str):
    """
    Delete the specified team.
    :param ctx: The message
    :param to_delete: The string representation of the team to be deleted
    :return: None
    """
    global teams

    # Delete the command message
    await ctx.message.delete()
    await ctx.send(f"_ _")

    if to_delete.lower() not in teams:
        await ctx.send(f"Please enter a valid team")
        return
    del_team = teams[to_delete.lower()].get_team_name()
    del teams[to_delete.lower()]
    await ctx.send(f"**Team {del_team.title()}*** has been disbanded. \n"
                   f"Thanks for playing!")


@bot.command()
async def addplayer(ctx, *, ctx_input: str):
    """
    Adds a player to a given team. Accounts for players that did not RSVP.
    :param ctx: The Message.
    :param ctx_input: Split into names
    :return:
    """


    # Specifically add Planners as the sole role capable of using this command
    role_access = discord.utils.get(ctx.guild.roles, name="Planners")

    if role_access not in ctx.author.roles:
        # Non-planners will get no response
        return

    # Avoid infinite loops by ignoring messages from the bot itself
    if ctx.author == bot.user:
        return

    # Delete the command message
    await ctx.message.delete()
    await ctx.send(f"_ _")

    if not teams:
        await ctx.send("Please make teams first!")
        return

    words = ctx_input.lower().split(',')

    # Handles case where there weren't exactly "teams" within the string
    if len(words) != 2:
        await ctx.send("Must input a player and a team!")
        return

    mentioned_users = ctx.message.mentions

    if not mentioned_users:
        await ctx.send("Please mention which user to add!")
        return
    elif len(mentioned_users) > 1:
        await ctx

    person = mentioned_users[0]
    # If they have not been instantiated in all_players
    if person.id not in all_players:
        await update_players([person.id])

    # If they forgot to RSVP
    if person.id not in players:
        players.append(person.id)

    to_team = words[1].lower().strip()
    if to_team not in teams:
        await ctx.send("Please enter valid team!")
        return

    teams[to_team].add_player(all_players[person.id])
    await ctx.send(f"**{all_players[person.id].get_name().title()}** "
                   f"has joined **Team {teams[to_team].get_team_name().title()}**!")
    return


@bot.command()
async def removeplayer(ctx, *, ctx_input: str):
    """
    Removes a player from a given team. Both items must exist and be specified correctly.
    :param ctx: The Message.
    :param ctx_input: The string containing the player and team they currently belong to
    :return:
    """

    # Specifically add Planners as the sole role capable of using this command
    role_access = discord.utils.get(ctx.guild.roles, name="Planners")

    if role_access not in ctx.author.roles:
        # Non-planners will get no response
        return

    # Avoid infinite loops by ignoring messages from the bot itself
    if ctx.author == bot.user:
        return

    # Delete the command message
    await ctx.message.delete()
    await ctx.send(f"_ _")

    if not teams:
        await ctx.send("Please make teams first!")
        return

    words = ctx_input.lower().split(',')

    # Handles case where there weren't exactly "teams" within the string
    if len(words) != 2:
        await ctx.send("Must input a player and a team!")
        return

    mentioned_users = ctx.message.mentions

    if not mentioned_users:
        await ctx.send("Please mention which user to add!")
        return
    elif len(mentioned_users) > 1:
        await ctx.send("Please mention one user!")
        return

    person = mentioned_users[0]

    to_team = words[1].lower().strip()
    if to_team not in teams:
        await ctx.send("Please enter valid team!")
        return

    # Can you remove player?
    in_team = False
    for player in teams[to_team].get_players():
        if player.get_id() == person.id:
            in_team = True
    if not in_team:
        await ctx.send("Player is not in team!")
        return

    teams[to_team].remove_player(all_players[person.id])
    await ctx.send(f"**{all_players[person.id].get_name().title()}** "
                   f"has left **Team {teams[to_team].get_team_name().title()}**!")
    return


@bot.command()
async def show(ctx):
    """
    Returns current iteration of all Teams.

    :param ctx: The Message.
    :return: None
    """
    # Delete the command message
    await ctx.message.delete()
    await ctx.send(f"_ _")

    # Simulate typing! Makes bot look busy
    async with ctx.typing():
        await asyncio.sleep(2)

    await ctx.send(team_string(teams))
    return


@bot.command()
async def cost(ctx, hours: int):
    """
    Returns the split cost of all players attending.

    :param ctx: The Message.
    :param hours: The number of hours a session is. We assert that hours > 1
    :return: None
    """
    # Delete the command message
    await ctx.message.delete()
    await ctx.send(f"_ _")

    RATE = 60
    people = len(players)

    if type(hours) != int or hours < 1:
        await ctx.send(f"Please enter a valid number to calculate costs!")
        return

    per_person = round((RATE * hours) / people, 2)

    # Simulate typing! Makes bot look busy
    async with ctx.typing():
        await asyncio.sleep(2)

    await ctx.send(f"Th cost for the **{people} players** coming is ${per_person}")
    return


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


def save_players() -> dict[int, Player]:
    """
    In the event that a game is played or the bot ends,
    write and save changes to a file.
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
