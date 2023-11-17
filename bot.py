import asyncio
import discord
from discord.ext import commands

import teams
from load_file import load_data

# Global Variables
TOKEN = 'MTE2ODczODc0OTYzMTQzMDY3Nw.GTvqq2.xLhbp2tVygrQNol4UojlrrRD-7THpgLYCOZcGc'  # Replace with your bot token
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

all_players = {}  # All users in server
players = []  # Player ID's with their Names for team builder
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
    # Specifically add Planners as the sole role capable of using this command
    role_access = discord.utils.get(ctx.guild.roles, name="Planners")

    if role_access not in ctx.author.roles:
        # Non-planners will get no response
        return
    # In the case we try to make teams with less than 12 players
    if len(players) < 12:
        await out_channel.send(f"You currently have **{len(players)} players.**\n"
                               f"You will need **{12 - len(players)} more players** to make at least two teams!")
        return

    # Now create teams...
    server_names = []
    for num in players:
        server_names.append(all_players[num][0])

    new_teams = teams.generate_teams(server_names)
    result = teams.team_string(new_teams)
    # Simulate typing! Makes bot look busy
    async with out_channel.typing():
        await asyncio.sleep(2)

    await out_channel.send(result)
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
    Creates a dict of players who RSVP'd and compares them to the players in the .csv file
    (players = {}) to see if any changes are to be made.
    Changes are made IF:
        - The player has been saved but has changed their display name (1)
        - The player does not yet exist in the data (1)

    Runs data through clean() to ensure we get the best possible username for teams and sharing

    :param ids: A list containing the id's of players.
    :return: None
    """

    global all_players
    updated = {}
    for reacted in ids:
        member = await curr_guild.fetch_member(reacted)

        # 1
        if member.id in all_players and member.display_name != all_players[member.id][0]:
            if clean(member.display_name):
                updated[member.id] = [member.display_name, all_players[member.id][1], all_players[member.id][2]]
            else:
                updated[member.id] = [member.name, all_players[member.id][1], all_players[member.id][2]]

        # 2
        elif member.id not in all_players:
            if clean(member.display_name):
                updated[member.id] = [member.display_name, 0, 0]
            else:
                updated[member.id] = [member.name, 0, 0]

    all_players.update(updated)


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
