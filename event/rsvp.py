import discord
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def insert_event(id, rsvp_id, event_date, event_location, max_players):
    supabase.table('event_data').insert({
        'id': id,
        'rsvp_id': rsvp_id,
        'event_date': event_date,
        'event_location': event_location,
        'max_players': max_players
    }).execute()

async def add_rsvp(bot, payload):
    id = payload.message_id
    response = supabase.table('event_data').select("*").eq("id", id).execute()
    rsvp = response.data[0]['rsvp_list']
    rsvp_id = response.data[0]['rsvp_id']
    waitlist = response.data[0]['waitlist']
    max_players = response.data[0]['max_players']
    if payload.user_id in rsvp or payload.user_id in waitlist:
        return
    if len(rsvp) < max_players:
        rsvp.append(payload.user_id)
    else:
        waitlist.append(payload.user_id)
    supabase.table('event_data').update({
        'rsvp_list': rsvp,
        'waitlist': waitlist
    }).eq("id", id).execute()
    await update_rsvp_message(bot, payload, rsvp, waitlist, rsvp_id)
    return


async def remove_rsvp(bot, payload):
    id = payload.message_id
    response = supabase.table('event_data').select("*").eq("id", id).execute()
    rsvp = response.data[0]['rsvp_list']
    rsvp_id = response.data[0]['rsvp_id']
    waitlist = response.data[0]['waitlist']
    if payload.user_id not in rsvp and payload.user_id not in waitlist:
        return
    # If the user is in RSVP and the waitlist has players, then remove the player from RSVP and move the top waitlist player to RSVP
    if payload.user_id in rsvp:
        rsvp.remove(payload.user_id)
        if waitlist:
            rsvp.append(waitlist.pop(0))
    elif payload.user_id in waitlist:
        waitlist.remove(payload.user_id)
    supabase.table('event_data').update({
        'rsvp_list': rsvp,
        'waitlist': waitlist
    }).eq("id", id).execute()
    await update_rsvp_message(bot, payload, rsvp, waitlist, rsvp_id)
    return

async def delete_event(bot, payload):
    guild = bot.get_guild(payload.guild_id)
    role_access = discord.utils.get(guild.roles, name="Planners")
    if role_access not in payload.member.roles:
        print("User does not have permission to delete event.")
        return

    channel = bot.get_channel(payload.channel_id)
    id = payload.message_id
    response = supabase.table('event_data').select("*").eq("id", id).execute()
    rsvp_id = response.data[0]['rsvp_id']

    message1 = await channel.fetch_message(payload.message_id)
    message2 = await channel.fetch_message(rsvp_id)

    await message1.delete()
    await message2.delete()
    supabase.table('event_data').delete().eq("id", id).execute()
    return

async def update_rsvp_message(bot, payload, rsvp, waitlist, rsvp_id):
    channel = bot.get_channel(payload.channel_id)
    print(channel)
    if channel:
        message = await channel.fetch_message(rsvp_id)
        print(message)
        rsvp_message_content = f"RSVP:\n"
        waitlist_message_content = f"Waitlist:\n"
        for player in rsvp:
            rsvp_message_content += f"<@{player}>\n"
        for player in waitlist:
            waitlist_message_content += f"<@{player}>\n"
        await message.edit(content=f"{rsvp_message_content}\n{waitlist_message_content}")
    else:
        print(f"Channel with ID {payload.channel_id} not found.")


