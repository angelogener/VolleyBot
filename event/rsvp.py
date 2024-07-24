import discord
import time
from db.supabase import get_supabase_client

supabase = get_supabase_client()

async def insert_event(id, rsvp_id, event_date, event_location, max_players):
    supabase.table('event_data').insert({
        'id': id,
        'rsvp_id': rsvp_id,
        'event_date': event_date,
        'event_location': event_location,
        'max_players': max_players,
        'created_time': int(time.time()),
    }).execute()

async def add_rsvp_db(message, payload):
    supabase_client = get_supabase_client()
    session = supabase_client.table('sessions').select('*').eq('rsvp_message_id', message.id).execute().data[0]

    if not session:
        return

    # Get the current highest order position for this session
    max_order = supabase_client.table('rsvps').select('order_position').eq('session_id', session['id']).order('order_position', desc=True).limit(1).execute().data
    new_order = 1 if not max_order else max_order[0]['order_position'] + 1

    current_rsvps = supabase_client.table('rsvps').select('*').eq('session_id', session['id']).eq('status', 'confirmed').execute()

    if len(current_rsvps.data) < session['max_players']:
        status = 'confirmed'
    else:
        status = 'waitlist'

    supabase_client.table('rsvps').insert({
        'session_id': session['id'],
        'user_id': payload.member.id,
        'status': status,
        'order_position': new_order
    }).execute()

async def add_rsvp_old(bot, payload):
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

async def remove_rsvp_db(message, payload):
    supabase_client = get_supabase_client()
    session = supabase_client.table('sessions').select('*').eq('rsvp_message_id', message.id).execute().data[0]

    if not session:
        return

    # Remove the RSVP
    removed_rsvp = supabase_client.table('rsvps').delete().eq('session_id', session['id']).eq('user_id', payload.member.id).execute().data[0]

    if removed_rsvp['status'] == 'confirmed':
        # Find the first person on the waitlist
        first_waitlist = supabase_client.table('rsvps').select('*').eq('session_id', session['id']).eq('status', 'waitlist').order('order_position').limit(1).execute().data

        if first_waitlist:
            # Move the first waitlisted person to confirmed status
            supabase_client.table('rsvps').update({'status': 'confirmed'}).eq('id', first_waitlist[0]['id']).execute()

    # Reorder the remaining RSVPs
    all_rsvps = supabase_client.table('rsvps').select('*').eq('session_id', session['id']).order('order_position').execute().data

    for i, rsvp in enumerate(all_rsvps, start=1):
        supabase_client.table('rsvps').update({'order_position': i}).eq('id', rsvp['id']).execute()


async def remove_rsvp_old(bot, payload):
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
    # SELECT * FROM event_data WHERE id = id
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
