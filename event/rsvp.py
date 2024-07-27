import discord
from db.supabase import get_supabase_client

supabase = get_supabase_client()

async def add_rsvp_db(message, payload):
    supabase_client = get_supabase_client()
    session = supabase_client.table('sessions').select('*').eq('rsvp_message_id', message.id).neq('completed', True).execute().data


    if not session:
        return

    session = session[0]

    # Get the current highest order position for this session
    max_order = supabase_client.table('rsvps').select('order_position').eq('session_id', session['id']).order('order_position', desc=True).limit(1).execute().data
    new_order = 1 if not max_order else max_order[0]['order_position'] + 1

    current_rsvps = supabase_client.table('rsvps').select('*').eq('session_id', session['id']).eq('status', 'confirmed').execute()
    current_waitlist = supabase_client.table('rsvps').select('*').eq('session_id', session['id']).eq('status', 'waitlist').execute()
    current_rsvps_ids = [rsvp['user_id'] for rsvp in current_rsvps.data]
    current_waitlist_ids = [rsvp['user_id'] for rsvp in current_waitlist.data]
    if (payload.member.id in current_rsvps_ids) or (payload.member.id in current_waitlist_ids):
        return


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

async def remove_rsvp_db(message, payload):
    supabase_client = get_supabase_client()
    session = supabase_client.table('sessions').select('*').eq('rsvp_message_id', message.id).neq('completed', True).execute().data
    print(session)
    if not session:
        return

    session = session[0]

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

async def update_rsvp_message(message):
    supabase_client = get_supabase_client()
    session = supabase_client.table('sessions').select('location, datetime, max_players, rsvps(user_id, order_position, status)').eq('rsvp_message_id', message.id).neq('completed', True).execute().data
    if not session:
        return
    confirmed_ids = []
    waitlist_ids = []
    for rsvp in session[0]['rsvps']:
        if rsvp['status'] == 'confirmed':
            confirmed_ids.append(rsvp['user_id'])
        else:
            waitlist_ids.append(rsvp['user_id'])
    event_embed = discord.Embed(
                title="Volleyball Session", color=0x00ff00
            ).add_field(
                name="Date",
                value=session[0]['datetime'],
                inline=False
            ).add_field(
                name="Location",
                value=session[0]['location'],
                inline=False
            ).add_field(
                name="Max Players",
                value=f"{len(confirmed_ids)}/{session[0]['max_players']}",
                inline=False
            ).add_field(
                name="RSVP",
                value=f"Confirmed: {', '.join(f'<@{player}>' for player in confirmed_ids)}\nWaitlist: {', '.join(f'<@{player}>' for player in waitlist_ids)}",
                inline=False
            ).set_footer(
                text="React with a ✅ to RSVP. If you can no longer make it react with a ❌ to give up your spot to someone else!"
            )
    await message.edit(embed=event_embed)
