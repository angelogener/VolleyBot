import asyncio
import datetime
import random
import discord
import os
from dotenv import load_dotenv
import time

from constructors.game import Game
from constructors.player import Player
from constructors.team import Team
from discord.ext import commands

from constructors.team_builder import form_teams, generate_teams, generate_balanced, team_string, date_string
from saves.load_file import load_data, save_data
from event.rsvp import add_rsvp_db, insert_event, delete_event, remove_rsvp_db
from helpers import has_planner_role, has_planner_role_interaction
from db.supabase import get_supabase_client
import re

load_dotenv()

# Global Variables
FILE_NAME = 'player_data.csv'
TOKEN = os.environ.get('DISCORD_TOKEN')
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

all_players: dict[int, Player]  # All past and current attendees to volleyball
players: list[int]  # Player ID's with their Names for team builder
teams: dict[int, Team]  # A list of Teams
curr_game: Game  # The current Game
curr_guild: discord.guild  # The current Guild


@bot.event
async def on_ready():
    """
    Prepares the bot for use. Will load player data.
    :return: None
    """
    global all_players
    all_players = load_data()
    # await bot.tree.sync()
    # print("Commands synced")

    print(f'{bot.user} is now running!')

@bot.command(name='sync')
async def sync_commands(ctx):
    if not has_planner_role(ctx): return
    guild = ctx.guild
    ctx.bot.tree.copy_global_to(guild=guild)
    await ctx.bot.tree.sync(guild=guild)
    await ctx.send("Synced!")


@bot.command(name='deletecommands')
async def delete_commands(ctx):
    if not has_planner_role(ctx): return
    guild = ctx.guild
    ctx.bot.tree.clear_commands(guild=guild)
    ctx.bot.tree.clear_commands(guild=None)
    await ctx.bot.tree.sync()
    await ctx.send("Cleared!")


@bot.event
async def on_raw_reaction_add(payload):
    """
    Adds the user to the RSVP list when they react with a ✅ emoji.
    Removes the user from the RSVP list when they react with a ❌ emoji.
    Deletes the event when the user reacts with a 🗑️ emoji.

    Parameters
    ----------
    payload : discord.RawReactionActionEvent
        The payload of the reaction event.

    Returns
    -------
    None
    """
    if payload.member == bot.user:
        return

    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)

    if payload.emoji.name == "✅":
        await add_rsvp_db(message, payload)
        await message.remove_reaction("✅", payload.member)
        # update rsvp message
    elif payload.emoji.name == "❌":
        await remove_rsvp_db(message, payload)
        await message.remove_reaction("❌", payload.member)
    # elif payload.emoji.name == "🗑️":
    #     await delete_event(bot, payload)



@bot.command()
async def clear(ctx, value: int):
    """
    Purges the last couple of messages, determined by value.
    """
    if not has_planner_role(ctx): return
    assert isinstance(value, int), await ctx.send(f"Not a valid number!")
    assert 0 < value < 51, await ctx.send(f"Can only be between 1 and 50 messages!")

    await ctx.channel.purge(limit=value + 1)  # Limit is set to "20 + 1" to include the command message
    await ctx.send(f'Cleared the last {value} messages.',
                   delete_after=5)  # Delete the confirmation message after 5 seconds


# -------------------------- #
@bot.tree.command(name="create-session",description="Create a new volleyball session.")
async def create(interaction: discord.Interaction, date_time: str, location: str, max_players: int):
    """
    Creates a new volleyball session and sends an RSVP message to the channel.
    Parameters
    ----------
    interaction : discord.Interaction
        The interaction object.
    date_time : str
        The date and time of the session.
    location : str
        The location of the session.
    max_players : int
        The maximum number of players allowed in the session.
    """
    supabase_client = get_supabase_client()
    session_data = {
        'datetime': date_time,
        'location': location,
        'max_players': max_players
    }
    result = supabase_client.table('sessions').insert(session_data).execute()
    session_id = result.data[0]['id']

    # Create and send RSVP message
    event_embed = discord.Embed(
                    title="Volleyball Session", color=0x00ff00
                ).add_field(
                    name="Date",
                    value=date_time,
                    inline=False
                ).add_field(
                    name="Location",
                    value=location,
                    inline=False
                ).add_field(
                    name="Max Players",
                    value=max_players,
                    inline=False
                ).set_footer(
                    text="React with a ✅ to RSVP. If you can no longer make it react with a ❌ to give up your spot to someone else!")

    await interaction.response.send_message(embed=event_embed)
    rsvp_message = await interaction.original_response()
    await rsvp_message.add_reaction("✅")
    await rsvp_message.add_reaction("❌")
    # Store message ID for later reference
    supabase_client.table('sessions').update({'rsvp_message_id': rsvp_message.id}).eq('id', session_id).execute()


@bot.tree.command(name="list-sessions",description="List all upcoming volleyball sessions.")
async def list_sessions(interaction: discord.Interaction):
    """
    Lists all upcoming volleyball sessions.
    Parameters
    ----------
    interaction : discord.Interaction
        The interaction object.
    """
    supabase_client = get_supabase_client()
    sessions = supabase_client.table('sessions').select('*').order('id', desc=True).limit(5).execute().data

    session_embed = discord.Embed(title="Upcoming Volleyball Sessions", color=0x00ff00)
    for session in sessions:
        session_embed.add_field(name=f"Session {session['id']}", value=f"Date: {session['datetime']}\nLocation: {session['location']}\nMax Players: {session['max_players']}", inline=False)
    await interaction.response.send_message(embed=session_embed)


@bot.tree.command(name="delete-session",description="Delete a volleyball session.")
async def delete_session(interaction: discord.Interaction, session_id: int):
    """
    Deletes a volleyball session.
    Parameters
    ----------
    interaction : discord.Interaction
        The interaction object.
    session_id : int
        The ID of the session to delete.
    """
    supabase_client = get_supabase_client()
    supabase_client.table('rsvps').delete().eq('session_id', session_id).execute()
    supabase_client.table('sessions').delete().eq('id', session_id).execute()
    await interaction.response.send_message(f"Session {session_id} has been deleted.")


@bot.tree.command(name="add-players", description="Add players to the volleyball session player list.")
async def add_players(interaction: discord.Interaction, session_id: int, players: str):
    """
    Adds players to the volleyball session player list.
    Parameters
    ----------
    interaction : discord.Interaction
        The interaction object.
    session_id : int
        The ID of the session.
    players : list[int]
        The list of player IDs to add.
    """
    supabase_client = get_supabase_client()
    # Get the list of players from string of mentions
    players = [int(re.findall(r'\d+', player)[0]) for player in players.split()]
    for player in players:
        supabase_client.table('rsvps').insert({'session_id': session_id, 'user_id': player, 'status': 'confirmed', 'order_position': random.randint(-10000, -1)}).execute()
    await interaction.response.send_message(f"Players {players} have been added to session {session_id}.")


@bot.tree.command(name="remove-players", description="Remove players from the volleyball session player list.")
async def remove_players(interaction: discord.Interaction, session_id: int, players: str):
    """
    Removes players from the volleyball session player list.
    Parameters
    ----------
    interaction : discord.Interaction
        The interaction object.
    session_id : int
        The ID of the session.
    players : list[int]
        The list of player IDs to remove.
    """
    supabase_client = get_supabase_client()
    # Get the list of players from string of mentions
    players = [int(re.findall(r'\d+', player)[0]) for player in players.split()]
    for player in players:
        supabase_client.table('rsvps').delete().eq('session_id', session_id).eq('user_id', player).execute()
    await interaction.response.send_message(f"Players {players} have been removed from session {session_id}.")


@bot.tree.command(name="list-players", description="List the players in the volleyball session player list.")
async def list_players(interaction: discord.Interaction, session_id: int):
    """
    Lists the players in the volleyball session player list.
    Parameters
    ----------
    interaction : discord.Interaction
        The interaction object.
    session_id : int
        The ID of the session.
    """
    supabase_client = get_supabase_client()
    players = supabase_client.table('rsvps').select('user_id', 'status').eq('session_id', session_id).execute().data
    player_list = [f"<@ {player['user_id']}>" for player in players if player['status'] == 'confirmed']
    waitlist = [f"<@ {player['user_id']}>" for player in players if player['status'] == 'waitlist']
    await interaction.response.send_message(f"Players in session {session_id}: {', '.join(player_list)}\nWaitlist: {', '.join(waitlist)}")


@bot.tree.command(name="create-teams", description="Create teams for the volleyball session.")
async def create_teams(interaction: discord.Interaction, session_id: int, num_teams: int = 2):
    """
    Creates teams for the volleyball session.
    Parameters
    ----------
    interaction : discord.Interaction
        The interaction object.
    session_id : int
        The ID of the session.
    num_teams : int
        The number of teams to create.
    """
    supabase_client = get_supabase_client()
    supabase_client.table('team_members').delete().neq('id', -1).execute()
    supabase_client.table('teams').delete().eq('session_id', session_id).execute()
    teams = form_teams(session_id, num_teams)
    # Store teams in the database
    for i, team in enumerate(teams, start=1):
        team_data = {'session_id': session_id, 'team_number': i}
        team_result = supabase_client.table('teams').insert(team_data).execute().data[0]

        for player in team:
            supabase_client.table('team_members').insert({
                'team_id': team_result['id'],
                'user_id': player
            }).execute()

    # Display teams
    team_display = "\n".join([f"Team {i+1}: {', '.join([interaction.guild.get_member(user_id).name for user_id in team])}" for i, team in enumerate(teams)])
    await interaction.response.send_message(f"Teams have been formed:\n{team_display}")


@bot.tree.command(name="list-teams", description="List the teams for the volleyball session.")
async def list_teams(interaction: discord.Interaction, session_id: int):
    """
    Lists the teams for the volleyball session.
    Parameters
    ----------
    interaction : discord.Interaction
        The interaction object.
    session_id : int
        The ID of the session.
    """
    supabase_client = get_supabase_client()
    teams = supabase_client.table('teams').select('*').eq('session_id', session_id).execute().data
    team_display = ""
    for team in teams:
        team_members = supabase_client.table('team_members').select('user_id').eq('team_id', team['id']).execute().data
        team_display += f"Team {team['team_number']}: {', '.join([interaction.guild.get_member(member['user_id']).name for member in team_members])}\n"
    await interaction.response.send_message(team_display)

@bot.tree.command(name="create-group", description="Create a new group.")
async def create_group(interaction: discord.Interaction, session_id: int, group_name: str, members: str):
    """
    Creates a new group.
    Parameters
    ----------
    interaction : discord.Interaction
        The interaction object.
    session_id : int
        The ID of the session.
    group_name : str
        The name of the group.
    members : str
        The list of members in the group.
    """
    supabase_client = get_supabase_client()
    # Create a new group
    group = supabase_client.table('player_groups').insert({
        'session_id': session_id,
        'group_name': group_name
    }).execute().data[0]
    members = [int(re.findall(r'\d+', member)[0]) for member in members.split()]
    # Add members to the group
    for member in members:
        member = interaction.guild.get_member(member)
        supabase_client.table('player_group_members').insert({
            'group_id': group['id'],
            'user_id': member.id
        }).execute()

    await interaction.response.send_message(f"Group '{group_name}' created with {len(members)} members.")

@bot.tree.command(name="list-groups", description="List the groups for the volleyball session.")
async def list_groups(interaction: discord.Interaction, session_id: int):
    """
    Lists the groups for the volleyball session.
    Parameters
    ----------
    interaction : discord.Interaction
        The interaction object.
    session_id : int
        The ID of the session.
    """
    supabase_client = get_supabase_client()
    groups = supabase_client.table('player_groups').select('*').eq('session_id', session_id).execute().data
    group_display = ""
    for group in groups:
        group_members = supabase_client.table('player_group_members').select('user_id').eq('group_id', group['id']).execute().data
        group_display += f"Group {group['group_name']} ({group['id']}): {', '.join([interaction.guild.get_member(member['user_id']).name for member in group_members])}\n"
    await interaction.response.send_message(group_display or "No groups found.")

@bot.tree.command(name="delete-group", description="Delete a group.")
async def delete_group(interaction: discord.Interaction, group_id: int):
    """
    Deletes a group.
    Parameters
    ----------
    interaction : discord.Interaction
        The interaction object.
    group_id : int
        The ID of the group to delete.
    """
    supabase_client = get_supabase_client()
    supabase_client.table('player_group_members').delete().eq('group_id', group_id).execute()
    supabase_client.table('player_groups').delete().eq('id', group_id).execute()
    await interaction.response.send_message(f"Group {group_id} has been deleted.")

def run_bot():
    bot.run(TOKEN)
