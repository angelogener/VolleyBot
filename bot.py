import os
import random
import re

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from constructors.team_builder import form_balanced_teams, form_teams
from db.supabase import get_supabase_client
from elo import update_elo
from event.rsvp import (add_rsvp_db, remove_rsvp_db,
                        update_rsvp_message)
from helpers import has_planner_role, has_planner_role_interaction

load_dotenv()

# Global Variables
TOKEN = os.environ.get('DISCORD_TOKEN')
intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    """
    Prepares the bot for use. Will load player data.
    :return: None
    """

    print(f'{bot.user} is now running!')
    keep_supabase_alive.start()

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

@tasks.loop(hours=6)
async def keep_supabase_alive():
    supabase_client = get_supabase_client()
    supabase_client.table('teams').select('*').execute()

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
        await update_rsvp_message(message)
        # update rsvp message
    elif payload.emoji.name == "❌":
        await remove_rsvp_db(message, payload)
        await message.remove_reaction("❌", payload.member)
        await update_rsvp_message(message)

@bot.event
async def on_member_join(member):
    """
    Welcomes a new member to the server.
    Parameters
    ----------
    member : discord.Member
        The member that joined the server.
    """
    channel = member.guild.system_channel
    if channel:
        await channel.send(f'Welcome {member.mention}! Make sure to read through the <#1199212477276246107> channel before you get started!')


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

@bot.tree.command(name="create-session",description="Create a new volleyball session.")
async def create_session(interaction: discord.Interaction, date_time: str, location: str, max_players: int):
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
    if not await has_planner_role_interaction(interaction): return
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
    sessions = supabase_client.table('sessions').select('*').neq('completed', True).order('id', desc=True).limit(5).execute().data

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
    if not await has_planner_role_interaction(interaction): return
    supabase_client = get_supabase_client()
    supabase_client.table('rsvps').delete().eq('session_id', session_id).execute()
    supabase_client.table('sessions').delete().eq('id', session_id).execute()
    await interaction.response.send_message(f"Session {session_id} has been deleted.")

@bot.tree.command(name="end-session",description="End a volleyball session.")
async def end_session(interaction: discord.Interaction, session_id: int):
    """
    Ends a volleyball session.
    Parameters
    ----------
    interaction : discord.Interaction
        The interaction object.
    session_id : int
        The ID of the session to end.
    """
    if not await has_planner_role_interaction(interaction): return
    supabase_client = get_supabase_client()
    supabase_client.table('sessions').update({'completed': True}).eq('id', session_id).execute()
    await interaction.response.send_message(f"Session {session_id} has been ended.")

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
    if not await has_planner_role_interaction(interaction): return
    supabase_client = get_supabase_client()
    # Get the list of players from string of mentions
    players = [int(re.findall(r'\d+', player)[0]) for player in players.split()]
    player_names = [interaction.guild.get_member(player).name for player in players]
    for player in players:
        supabase_client.table('rsvps').insert({'session_id': session_id, 'user_id': player, 'status': 'confirmed', 'order_position': random.randint(-10000, -1)}).execute()
    await interaction.response.send_message(f"Players {', '.join(player_names)} have been added to session {session_id}.")

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
    if not await has_planner_role_interaction(interaction): return
    supabase_client = get_supabase_client()
    # Get the list of players from string of mentions
    players = [int(re.findall(r'\d+', player)[0]) for player in players.split()]
    player_names = [interaction.guild.get_member(player).name for player in players]
    for player in players:
        supabase_client.table('rsvps').delete().eq('session_id', session_id).eq('user_id', player).execute()
    await interaction.response.send_message(f"Players {', '.join(player_names)} have been removed from session {session_id}.")

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
    player_list = [f"<@{player['user_id']}>" for player in players if player['status'] == 'confirmed']
    waitlist = [f"<@{player['user_id']}>" for player in players if player['status'] == 'waitlist']
    embed = discord.Embed(title=f"Players in session {session_id}", color=0x00ff00).add_field(name="Confirmed", value=", ".join(player_list), inline=False).add_field(name="Waitlist", value=", ".join(waitlist), inline=False)
    await interaction.response.send_message(embed=embed)

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
    if not await has_planner_role_interaction(interaction): return
    await interaction.response.defer()
    supabase_client = get_supabase_client()
    supabase_client.table('team_members').delete().neq('id', -1).execute()
    supabase_client.table('matches').delete().eq('session_id', session_id).execute()
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
    embed = discord.Embed(title=f"Session {session_id} Teams", color=0x00ff00)
    for team_member_ids in teams:
        team_members = [interaction.guild.get_member(user_id).mention for user_id in team_member_ids]
        embed.add_field(name=f"Team {teams.index(team_member_ids) + 1}", value=", ".join(team_members), inline=False)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="create-balanced-teams", description="Create balanced teams for the volleyball session.")
async def create_balanced_teams(interaction: discord.Interaction, session_id: int, num_teams: int = 2):
    """
    Creates balanced teams for the volleyball session.
    Parameters
    ----------
    interaction : discord.Interaction
        The interaction object.
    session_id : int
        The ID of the session.
    num_teams : int
        The number of teams to create.
    """
    if not await has_planner_role_interaction(interaction): return
    supabase_client = get_supabase_client()
    supabase_client.table('team_members').delete().neq('id', -1).execute()
    supabase_client.table('matches').delete().eq('session_id', session_id).execute()
    supabase_client.table('teams').delete().eq('session_id', session_id).execute()
    teams = form_balanced_teams(session_id, num_teams)

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
    embed = discord.Embed(title=f"Session {session_id} Teams", color=0x00ff00)
    for team_member_ids in teams:
        team_members = [interaction.guild.get_member(user_id).mention for user_id in team_member_ids]
        embed.add_field(name=f"Team {teams.index(team_member_ids) + 1}", value=", ".join(team_members), inline=False)
    await interaction.response.send_message(embed=embed)

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
    embed = discord.Embed(title=f"Session {session_id} Teams")
    for team in teams:
        team_members = supabase_client.table('team_members').select('user_id').eq('team_id', team['id']).execute().data
        embed.add_field(name=f"Team {team['team_number']}", value=", ".join([interaction.guild.get_member(member['user_id']).mention for member in team_members]), inline=False)
    await interaction.response.send_message(embed=embed or "No teams found.")

@bot.tree.command(name="move-player", description="Move a player from one team to another team")
async def move_player(interaction: discord.Interaction, session_id: int, player: discord.Member, team_number: int):
    """
    Move a player from one team to another team
    Parameters
    ----------
    interaction : discord.Interaction
        The interaction object.
    session_id : int
        The ID of the session.
    player : int
        The player to move.
    team_number : int
        The number of the team to move the player to.
    """
    if not await has_planner_role_interaction(interaction): return
    supabase_client = get_supabase_client()
    team = supabase_client.table('teams').select('id').eq('session_id', session_id).eq('team_number', team_number).execute().data[0]
    supabase_client.table('team_members').update({'team_id': team['id']}).eq('user_id', player.id).execute()
    await interaction.response.send_message(f"Player {player.name} has been moved to team {team_number}.")

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
    if not await has_planner_role_interaction(interaction): return
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
    embed = discord.Embed(title=f"Group {group_name}", color=0x00ff00)
    embed.add_field(name="Members", value=", ".join([interaction.guild.get_member(member).mention for member in members]), inline=False)
    await interaction.response.send_message(embed=embed)

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
    embed = discord.Embed(title=f"Session {session_id} Groups")
    for group in groups:
        group_members = supabase_client.table('player_group_members').select('user_id').eq('group_id', group['id']).execute().data
        embed.add_field(name=f"Group {group['group_name']}", value=", ".join([interaction.guild.get_member(member['user_id']).mention for member in group_members]), inline=False)
    await interaction.response.send_message(embed=embed or "No groups found.")

@bot.tree.command(name="add-group-members", description="Add members to a group.")
async def add_group_members(interaction: discord.Interaction, group_id: int, members: str):
    """
    Add members to a group.
    Parameters
    ----------
    interaction : discord.Interaction
        The interaction object.
    group_id : int
        The ID of the group.
    members : str
        The list of members to add to the group.
    """
    if not await has_planner_role_interaction(interaction): return
    supabase_client = get_supabase_client()
    members = [int(re.findall(r'\d+', member)[0]) for member in members.split()]
    members_mention = [interaction.guild.get_member(member).mention for member in members]
    for member in members:
        member = interaction.guild.get_member(member)
        supabase_client.table('player_group_members').insert({
            'group_id': group_id,
            'user_id': member.id
        }).execute()

    await interaction.response.send_message(f"Members {', '.join(members_mention)} have been added to group {group_id}.")

@bot.tree.command(name="remove-group-members", description="Remove members from a group.")
async def remove_group_members(interaction: discord.Interaction, group_id: int, members: str):
    """
    Remove members from a group.
    Parameters
    ----------
    interaction : discord.Interaction
        The interaction object.
    group_id : int
        The ID of the group.
    members : str
        The list of members to remove from the group.
    """
    if not await has_planner_role_interaction(interaction): return
    supabase_client = get_supabase_client()
    members = [int(re.findall(r'\d+', member)[0]) for member in members.split()]
    members_mention = [interaction.guild.get_member(member).mention for member in members]
    for member in members:
        member = interaction.guild.get_member(member)
        supabase_client.table('player_group_members').delete().eq('group_id', group_id).eq('user_id', member.id).execute()
    await interaction.response.send_message(f"Members {', '.join(members_mention)} have been removed from group {group_id}.")

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
    if not await has_planner_role_interaction(interaction): return
    supabase_client = get_supabase_client()
    supabase_client.table('player_group_members').delete().eq('group_id', group_id).execute()
    supabase_client.table('player_groups').delete().eq('id', group_id).execute()
    await interaction.response.send_message(f"Group {group_id} has been deleted.")

@bot.tree.command(name="create-match", description="Creates a match for the volleyball session.")
async def create_match(interaction: discord.Interaction, session_id: int, team_1: int, team_2: int):
    """
    Creates a match for the volleyball session.
    Parameters
    ----------
    interaction : discord.Interaction
        The interaction object.
    session_id : int
        The ID of the session.
    team_1 : int
        The number of the first team.
    team_2 : int
        The number of the second team.
    """
    if not await has_planner_role_interaction(interaction): return
    supabase_client = get_supabase_client()
    teams = supabase_client.table('teams').select('id, team_number').eq('session_id', session_id).execute().data
    team_1_id = next(team['id'] for team in teams if team['team_number'] == team_1)
    team_2_id = next(team['id'] for team in teams if team['team_number'] == team_2)

    supabase_client.table('matches').insert({
        'session_id': session_id,
        'team1_id': team_1_id,
        'team2_id': team_2_id,
    }).execute()
    await interaction.response.send_message(f"Match created with for Team {team_1} against {team_2}. Good luck!")

@bot.tree.command(name="list-matches", description="List the matches scheduled for the volleyball session.")
async def list_matches(interaction: discord.Interaction, session_id: int):
    """
    Lists the matches scheduled for the volleyball session.
    Parameters
    ----------
    interaction : discord.Interaction
        The interaction object.
    session_id : int
        The ID of the session.
    """
    supabase_client = get_supabase_client()
    # Get all matches for the session
    matches = supabase_client.table('matches').select('*').eq('session_id', session_id).neq('completed', True).execute().data

    if not matches:
        await interaction.response.send_message("No matches scheduled for this session.")
        return

    # Get team names
    team_ids = set(match['team1_id'] for match in matches) | set(match['team2_id'] for match in matches)
    teams = supabase_client.table('teams').select('*').in_('id', list(team_ids)).execute().data
    team_names = {team['id']: f"Team {team['team_number']}" for team in teams}

    # Create schedule message
    embed = discord.Embed(title="Match Schedule", color=0x00ff00)
    for match in matches:
        team1 = team_names[match['team1_id']]
        team2 = team_names[match['team2_id']]
        embed.add_field(name=f"Match {match['id']}", value=f"{team1} vs {team2}", inline=False)
    await interaction.response.send_message(embed=embed or "No matches found.")

@bot.tree.command(name="winner", description="Declare the winning team.")
async def winner(interaction: discord.Interaction, session_id: int, match_number: int, winning_team_number: int):
    """
    Declare the winning team.
    Parameters
    ----------
    interaction : discord.Interaction
        The interaction object.
    session_id : int
        The ID of the session.
    match_number : int
        The number of the match.
    winning_team_number : int
        The number of the winning team.
    """
    if not await has_planner_role_interaction(interaction): return
    supabase_client = get_supabase_client()
    match = supabase_client.table('matches').select('*').eq('session_id', session_id).eq('id', match_number).neq('completed', True).execute().data
    if not match:
        await interaction.response.send_message(f"Match {match_number} does not exist or already has been submitted")
        return
    match = match[0]

    winning_team_id = supabase_client.table('teams').select('id').eq('session_id', session_id).eq('team_number', winning_team_number).execute().data[0]['id']
    losing_team_id = match['team1_id'] if match['team2_id'] == winning_team_id else match['team2_id']
    update_elo(winning_team_id, losing_team_id)
    supabase_client.table('matches').update({'completed': True, 'winner_id': winning_team_id}).eq('id', match['id']).execute()

    await interaction.response.send_message(f"Team {winning_team_number} has been declared the winner for Match {match_number}, congrats!")

def run_bot():
    bot.run(TOKEN)
