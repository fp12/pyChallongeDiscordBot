import discord
import asyncio
import urllib.request
import string
# import os (needed with cloudconvert)
# import cloudconvert

from const import *
from utils import *
# from config import appConfig (needed with cloudconvert)
from database.core import db
from commands.core import *
from modules.core import modules
from challonge import ChallongeException
from challonge_impl.accounts import ChallongeAccess, TournamentStateConstraint
from challonge_impl.utils import *
from challonge_impl.events import Events
from discord_impl.permissions import Permissions
from discord_impl.channel_type import ChannelType

# cloudconvertapi = cloudconvert.Api(appConfig['cloudconvert'])


def get_member(name, server):
    member_id = utils.get_user_id_from_mention(name)
    if member_id == 0:
        return server.get_member_named(name)
    else:
        return discord.utils.get(server.members, id=member_id)


async def update_channel_topic(account, t, client, channel):
    desc, exc = await get_channel_desc(account, t)
    if exc:
        await client.send_message(channel, exc)
    elif desc:
        currentTopic = channel.topic
        index = -1
        custom_topic = ''
        if currentTopic and len(currentTopic) > 0:
            index = currentTopic.find(T_ChannelDescriptionSeparator)
            if index > -1:
                currentTopic = currentTopic[:index]
        await client.edit_channel(channel, topic=currentTopic + T_ChannelDescriptionSeparator + desc)
        # Todo: Module!!


# ORGANIZER


@helpers('account')
@aliases('new')
@optional_args('subdomain')
@required_args('name', 'url', 'type')
@cmds.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.NewTourney,
                   challongeAccess=ChallongeAccess.RequiredForAuthor)
async def create(client, message, **kwargs):
    """Create a new tournament
    Required Arguments:
    name -- will be used as the tournament name (Max: 60 characters, no spaces)
    url -- http://challonge.com/url (letters, numbers, and underscores only)
    type -- can be [singleelim, doubleelim, roundrobin, swiss]
    Optional Arguments:
    subdomain -- a valid Challonge organization http://subdomain.challonge.com/url
    """
    # Validate name
    if len(kwargs.get('name')) > 60:
        await client.send_message(message.channel, '❌ Invalid name. Please use less than 60 characters and no spaces')
        return
    # Validate url
    diff = set(kwargs.get('url')) - set(string.ascii_letters + string.digits + '_')
    if diff:
        await client.send_message(message.channel, '❌ Invalid url {}. Please use only letters, numbers and underscores'.format(kwargs.get('url')))
        return
    # Validate type
    if kwargs.get('type') not in ['singleelim', 'doubleelim', 'roundrobin', 'swiss']:
        await client.send_message(message.channel, '❌ Invalid tournament type {}. Please choose from singleelim, doubleelim, roundrobin or swiss'.format(kwargs.get('type')))
        return
    if kwargs.get('type') == 'singleelim':
        tournament_type = 'single elimination'
    elif kwargs.get('type') == 'doubleelim':
        tournament_type = 'double elimination'
    elif kwargs.get('type') == 'roundrobin':
        tournament_type = 'round robin'
    else:
        tournament_type = 'swiss'

    params = {}
    if kwargs.get('subdomain', None):
        params['subdomain'] = kwargs.get('subdomain')

    try:
        t = await kwargs.get('account').tournaments.create(kwargs.get('name'), kwargs.get('url'), tournament_type, **params)
    except ChallongeException as e:
        await client.send_message(message.channel, T_OnChallongeException.format(e))
    else:
        role = await client.create_role(message.server, name='Participant_' + kwargs.get('name'), mentionable=True)
        chChannel = await client.create_channel(message.server, 'T_' + kwargs.get('name'))
        db.add_tournament(t['id'], chChannel, role.id, message.author.id)
        await client.send_message(message.channel, T_TournamentCreated.format(kwargs.get('name'),
                                                                              t['full-challonge-url'],
                                                                              role.mention,
                                                                              chChannel.mention))
        await update_channel_topic(kwargs.get('account'), t, client, chChannel)
        await modules.on_state_change(message.server.id, TournamentState.pending, t_name=kwargs.get('name'), me=message.server.me)


@helpers('account', 'tournament_id')
@aliases('shuffle', 'randomize')
@cmds.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentStateConstraint.Pending)
async def shuffleseeds(client, message, **kwargs):
    """Shuffle tournament seeds
    The tournament MUST NOT have been started yet!
    No Arguments
    """
    try:
        await kwargs.get('account').participants.randomize(kwargs.get('tournament_id'))
    except ChallongeException as e:
        await client.send_message(message.author, T_OnChallongeException.format(e))
    else:
        await client.send_message(message.channel, '✅ Seeds for this tournament have been suffled!')
        # TODO: display list of new players seeds


@helpers('account', 'tournament_id', 'tournament_role')
@aliases('launch')
@cmds.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentStateConstraint.Pending)
async def start(client, message, **kwargs):
    """Start a tournament
    This channel will be locked for writing except for participants / organizers
    No Arguments
    """
    try:
        t = await kwargs.get('account').tournaments.start(kwargs.get('tournament_id'))
    except ChallongeException as e:
        await client.send_message(message.author, T_OnChallongeException.format(e))
    else:
        allow = discord.Permissions.none()
        allow.send_messages = True
        await client.edit_channel_permissions(message.channel, kwargs.get('tournament_role'), allow=allow)

        for r in message.server.me.roles:
            if r.name == C_RoleName:
                await client.edit_channel_permissions(message.channel, r, allow=allow)

        deny = discord.Permissions.none()
        deny.send_messages = True
        await client.edit_channel_permissions(message.channel, message.server.default_role, deny=deny)
        await client.send_message(message.channel, '✅ Tournament is now started!')
        await update_channel_topic(kwargs.get('account'), t, client, message.channel)
        await modules.on_state_change(message.server.id, TournamentState.underway, t_name=t['name'], me=message.server.me)
        # TODO real text (with games to play...)
        """
        process = cloudconvertapi.convert({
            "inputformat": "svg",
            "outputformat": "png",
            "input": "download",
            "file": t['live-image-url']
        })
        process.wait()
        process.download(localfile='data/temp.png')
        await client.send_file(message.channel, 'data/temp.png')
        try:
            os.remove('data/temp.png')
        except OSError as e:
            print ("Error: %s - %s." % (e.filename,e.strerror))
        """


@helpers('account', 'tournament_id')
@cmds.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentStateConstraint.Underway)
async def reset(client, message, **kwargs):
    """Reset a tournament
    All scores and attachments will be cleared. You will be able to edit participants then start again
    No Arguments
    """
    try:
        await kwargs.get('account').tournaments.reset(kwargs.get('tournament_id'))
    except ChallongeException as e:
        await client.send_message(message.author, T_OnChallongeException.format(e))
    else:
        await client.send_message(message.channel, '✅ Tournament has been reset!')
        try:
            t = await kwargs.get('account').tournaments.show(kwargs.get('tournament_id'))
        except ChallongeException as e:
            print('reset exc=: %s' % e)
        else:
            await update_channel_topic(kwargs.get('account'), t, client, message.channel)
            await modules.on_state_change(message.server.id, TournamentState.pending, t_name=t['name'], me=message.server.me)
        # TODO real text ?


@helpers('account', 'tournament_id')
@required_args('date', 'time', 'duration')
@cmds.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentStateConstraint.Pending)
async def checkin_setup(client, message, **kwargs):
    """Setup the checkin process for participants
    Required Arguments:
    date -- date of the tournament: YYYY/MM/DD
    time -- time of the tournament: HH:MM (24h format)
    duration -- length of the participant check-in window in minutes.
    """
    # verify date
    date = get_date(kwargs.get('date'))
    if not date:
        await client.send_message(message.channel, '❌ Wrong date format. Must be `YYYY/MM/DD`.')
        return

    # verify time
    time = get_time(kwargs.get('time'))
    if not time:
        await client.send_message(message.channel, '❌ Wrong time format. Must be `HH:MM` (24h format).')
        return

    # verify duration
    try:
        duration = int(kwargs.get('duration'))
    except ValueError:
        await client.send_message(message.channel, '❌ Duration must be an integer')
        return
    else:
        if duration <= 0:
            await client.send_message(message.channel, '❌ Duration must be a positive integer')
            return

    # combime date & time
    full_date_time = datetime.strptime(kwargs.get('date') + ' ' + kwargs.get('time'), '%Y/%m/%d %H:%M')

    try:
        await kwargs.get('account').tournaments.update(kwargs.get('tournament_id'), start_at=full_date_time, check_in_duration=duration)
    except ChallongeException as e:
        await client.send_message(message.author, T_OnChallongeException.format(e))
    else:
        await client.send_message(message.channel, '✅ Start date and check-in duration have been processed')

        try:
            t = await kwargs.get('account').tournaments.show(kwargs.get('tournament_id'), include_participants=1, include_matches=1)
        except ChallongeException as e:
            print(T_OnChallongeException.format(e))
        else:
            await update_channel_topic(kwargs.get('account'), t, client, message.channel)
        # TODO real text ?


@helpers('account', 'tournament_id')
@cmds.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentStateConstraint.Pending)
async def checkin_validate(client, message, **kwargs):
    """Finalize the check-in process once check-in time is done
    Participants that didn't check-in will be moved to bottom seeds
    No arguments
    """
    try:
        await kwargs.get('account').tournaments.process_check_ins(kwargs.get('tournament_id'))
    except ChallongeException as e:
        await client.send_message(message.author, T_OnChallongeException.format(e))
    else:
        await client.send_message(message.channel, '✅ Check-ins have been processed')
        try:
            t = await kwargs.get('account').tournaments.show(kwargs.get('tournament_id'), include_participants=1, include_matches=1)
        except ChallongeException as e:
            print(T_OnChallongeException.format(e))
        else:
            await update_channel_topic(kwargs.get('account'), t, client, message.channel)
        # TODO real text ?


@helpers('account', 'tournament_id')
@cmds.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentStateConstraint.Pending)
async def checkin_abort(client, message, **kwargs):
    """Stop or reset the check-in process
    No arguments
    """
    try:
        await kwargs.get('account').tournaments.abort_check_in(kwargs.get('tournament_id'))
    except ChallongeException as e:
        await client.send_message(message.author, T_OnChallongeException.format(e))
    else:
        await client.send_message(message.channel, '✅ Check-ins have been aborted')
        try:
            t = await kwargs.get('account').tournaments.show(kwargs.get('tournament_id'), include_participants=1, include_matches=1)
        except ChallongeException as e:
            print(T_OnChallongeException.format(e))
        else:
            await update_channel_topic(kwargs.get('account'), t, client, message.channel)
        # TODO real text ?


@helpers('account', 'tournament_id', 'tournament_role')
@cmds.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentStateConstraint.AwaitingReview)
async def finalize(client, message, **kwargs):
    """Finalize a tournament
    Tournament will be closed and no further modifications will be possible
    Be sure to upload attachements before finalizing
    This Channel will be locked for writing except for organizers
    No Arguments
    """
    try:
        t = await kwargs.get('account').tournaments.finalize(kwargs.get('tournament_id'))
    except ChallongeException as e:
        await client.send_message(message.author, T_OnChallongeException.format(e))
    else:
        # let's remove the role associated to this tournament.
        # only the Challonge role will be able to write in it
        await client.delete_role(message.server, kwargs.get('tournament_role'))
        await client.send_message(message.channel, '✅ Tournament has been finalized!')
        try:
            t = await kwargs.get('account').tournaments.show(kwargs.get('tournament_id'), include_participants=1, include_matches=1)
        except ChallongeException as e:
            print(T_OnChallongeException.format(e))
        else:
            await update_channel_topic(kwargs.get('account'), t, client, message.channel)
        await modules.on_state_change(message.server.id, TournamentState.complete, t_name=t['name'], me=message.server.me)
        # TODO real text + show rankings


@helpers('account', 'tournament_id', 'tournament_role')
@cmds.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentStateConstraint.Any)
async def destroy(client, message, **kwargs):
    """Delete a tournament on Challonge and cleanup Discord bindings
    Use with caution! This action can't be reversed!
    No Arguments
    """
    try:
        t = await kwargs.get('account').tournaments.show(kwargs.get('tournament_id'))
        await kwargs.get('account').tournaments.destroy(kwargs.get('tournament_id'))
    except ChallongeException as e:
        await client.send_message(message.author, T_OnChallongeException.format(e))
    else:
        if kwargs.get('tournament_role'):  # tournament role may have been deleted by finalize before
            await client.delete_role(message.server, kwargs.get('tournament_role'))
        await client.delete_channel(message.channel)
        channelId = db.get_server(message.server).management_channel_id
        await client.send_message(discord.Channel(server=message.server, id=channelId), '✅ Tournament {0} has been destroyed by {1}!'.format(t['name'], message.author.mention))
        db.remove_tournament(kwargs.get('tournament_id'))


@helpers('account', 'tournament_id')
@cmds.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentStateConstraint.Any)
async def status(client, message, **kwargs):
    """Get the tournament status
    No Arguments
    """
    try:
        t = await kwargs.get('account').tournaments.show(kwargs.get('tournament_id'), include_participants=1, include_matches=1)
    except ChallongeException as e:
        await client.send_message(message.author, T_OnChallongeException.format(e))
    else:
        if t['state'] == 'underway':
            matchesRepr, exc = await get_current_matches_repr(kwargs.get('account'), t)
            if exc:
                await client.send_message(message.channel, exc)
            else:
                await client.send_message(message.channel, '✅ Status for tournament `{0}` ({1})\nOpen Matches:\n{2}'.format(t['name'], t['full-challonge-url'], matchesRepr))

        elif t['state'] == 'pending':
            info = []
            info.append('✅ Tournament: {0} ({1}) is pending.'.format(t['name'], t['full-challonge-url']))
            info.append('%d participants have registered right now. More can still join until tournament is started' % t['participants-count'])
            await client.send_message(message.channel, '\n'.join(info))

        elif t['state'] == 'awaiting_review':
            await client.send_message(message.channel, '✅ Tournament: {0} ({1}) has been completed and is waiting for final review (finalize)'.format(t['name'], t['full-challonge-url']))

        elif t['state'] == 'complete':
            rankingRepr, exc = get_final_ranking_repr(account, t)
            if exc:
                await client.send_message(message.channel, exc)
            else:
                await client.send_message(message.channel, '✅ Tournament: {0} ({1}) has been completed\n{2}'.format(t['name'], t['full-challonge-url'], rankingRepr))

        else:
            print('[status] Unknown state: ' + t['state'])


@helpers('account', 'tournament_id')
@required_args('p1', 'score', 'p2')
@cmds.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentStateConstraint.Underway)
async def updatex(client, message, **kwargs):
    """Report a match score
    Required Arguments:
    p1 -- Player 1 name or nickname or mention (mention is safer)
    score -- [YourScore]-[OpponentScore] : 5-0. Can be comma separated: 5-0,4-5,5-3
    p2 -- Player 2 name or nickname or mention (mention is safer)
    """
    # Verify score format
    if not verify_score_format(kwargs.get('score')):
        await client.send_message(message.channel, '❌ Invalid score format. Please use the following 5-0,4-5,5-3')
        return

    # Verify first player: mention first, then name, then nick
    p1_as_member = get_member(kwargs.get('p1'), message.server)
    if not p1_as_member:
        await client.send_message(message.channel, '❌ I could not find player 1 on this server')
        return

    # Verify second player: mention first, then name, then nick
    p2_as_member = get_member(kwargs.get('p2'), message.server)
    if not p2_as_member:
        await client.send_message(message.channel, '❌ I could not find player 2 on this server')
        return

    p1_id, p2_id, exc = await get_players(kwargs.get('account'), kwargs.get('tournament_id'), p1_as_member.name, p2_as_member.name)
    if exc:
        await client.send_message(message.channel, exc)
        return
    elif not p1_id:
        await client.send_message(message.channel, '❌ I could not find player 1 in this tournament')
        return
    elif not p2_id:
        await client.send_message(message.channel, '❌ I could not find player 2 in this tournament')
        return

    match, is_reversed, exc = await get_match(kwargs.get('account'), kwargs.get('tournament_id'), p1_id, p2_id)
    if exc:
        await client.send_message(message.channel, exc)
        return
    elif not match:
        await client.send_message(message.channel, '❌ No open match found for these players')
        return

    winner_id = p1_id if author_is_winner(kwargs.get('score')) else p2_id
    score = kwargs.get('score') if not is_reversed else reverse_score(kwargs.get('score'))
    msg, exc = await update_score(kwargs.get('account'), kwargs.get('tournament_id'), match['id'], score, winner_id)
    if exc:
        await client.send_message(message.channel, exc)
        return
    else:
        await client.send_message(message.channel, msg)
        try:
            t = await kwargs.get('account').tournaments.show(kwargs.get('tournament_id'), include_participants=1, include_matches=1)
        except ChallongeException as e:
            print(T_OnChallongeException.format(e))
        else:
            await update_channel_topic(kwargs.get('account'), t, client, message.channel)
        await modules.on_event(message.server.id, Events.on_update_score, p1_name=p1_as_member.name, score=kwargs.get('score'), p2_name=p2_as_member.name, me=message.server.me)


@helpers('account', 'tournament_id')
@required_args('participant')
@cmds.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentStateConstraint.Underway)
async def nextx(client, message, **kwargs):
    """Get information about your next game
    Required Arguments
    participant -- Participant name or nickname or mention (mention is safer)
    """
    # Verify first player: mention first, then name, then nick
    p_as_member = get_member(kwargs.get('participant'), message.server)
    if not p_as_member:
        await client.send_message(message.channel, '❌ I could not find the participant on this server')
        return

    msg, exc = await get_next_match(kwargs.get('account'), kwargs.get('tournament_id'), p_as_member.name)
    if exc:
        await client.send_message(message.channel, exc)
    elif msg:
        await client.send_message(message.channel, msg)
    else:
        await client.send_message(message.channel, '❌ Something went wrong. Sorry...')


# PARTICIPANT


@helpers('account', 'tournament_id')
@required_args('score', 'opponent')
@cmds.register(minPermissions=Permissions.Participant,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentStateConstraint.Underway)
async def update(client, message, **kwargs):
    """Report your score against another participant
    Required Arguments:
    score -- [YourScore]-[OpponentScore] : 5-0. Can be comma separated: 5-0,4-5,5-3
    opponent -- Your opponnent name or nickname or mention (mention is safer)
    """
    account = kwargs.get('account')
    t_id = kwargs.get('tournament_id')
    score = kwargs.get('score')

    # Verify score format
    if not verify_score_format(score):
        await client.send_message(message.channel, '❌ Invalid score format. Please use the following 5-0,4-5,5-3')
        return

    # Verify other member: mention first, then name, then nick
    opponent_as_member = get_member(kwargs.get('opponent'), message.server)
    if not opponent_as_member:
        await client.send_message(message.channel, '❌ I could not find your opponent on this server')
        return

    p1_id, p2_id, exc = await get_players(account, t_id, message.author.name, opponent_as_member.name)
    if exc:
        await client.send_message(message.channel, exc)
        return
    elif not p1_id:
        await client.send_message(message.channel, '❌ I could not find you in this tournament')
        return
    elif not p2_id:
        await client.send_message(message.channel, '❌ I could not find your opponent in this tournament')
        return

    match, is_reversed, exc = await get_match(account, t_id, p1_id, p2_id)
    if exc:
        await client.send_message(message.channel, exc)
        return
    elif not match:
        await client.send_message(message.channel, '❌ Your current opponent is not ' + opponent_as_member.name)
        return

    winner_id = p1_id if author_is_winner(score) else p2_id
    if is_reversed:
        score = reverse_score(score)
    msg, exc = await update_score(account, t_id, match['id'], score, winner_id)
    if exc:
        await client.send_message(message.channel, exc)
    else:
        next_for_p1, exc1 = await get_next_match(account, t_id, message.author.name)
        next_for_p2, exc2 = await get_next_match(account, t_id, opponent_as_member.name)
        if exc1 or exc2:
            # something went wrong with the next games, don't bother the author and send the result msg
            await client.send_message(message.channel, msg)
            print(exc1, exc2)
        else:
            if next_for_p1:
                msg = msg + '\n' + next_for_p1
            if next_for_p2:
                msg = msg + '\n' + next_for_p2
            await client.send_message(message.channel, msg)

        try:
            t = await account.tournaments.show(t_id, include_participants=1, include_matches=1)
        except ChallongeException as e:
            print(T_OnChallongeException.format(e))
        else:
            await update_channel_topic(account, t, client, message.channel)
        await modules.on_event(message.server.id, Events.on_update_score, p1_name=message.author.name, score=kwargs.get('score'), p2_name=opponent_as_member.name, me=message.server.me)


@helpers('account', 'tournament_id', 'tournament_role')
@cmds.register(minPermissions=Permissions.Participant,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentStateConstraint.Any)
async def forfeit(client, message, **kwargs):
    """Forfeit for the current tournament
    If the tournament is pending, you will be removed from the participants list
    If the tournament is in progress, Challonge will forfeit your potential remaining games
    and you won't be able to write in this channel anymore
    No Arguments
    """
    author_id, exc = await get_player(kwargs.get('account'), kwargs.get('tournament_id'), message.author.name)
    if exc:
        await client.send_message(message.channel, exc)
        return
    elif author_id:
        try:
            await kwargs.get('account').participants.destroy(kwargs.get('tournament_id'), author_id)
        except ChallongeException as e:
            await client.send_message(message.author, T_OnChallongeException.format(e))
    await client.remove_roles(message.author, kwargs.get('tournament_role'))
    await client.send_message(message.channel, '✅ You forfeited from this tournament')
    try:
        t = await kwargs.get('account').tournaments.show(kwargs.get('tournament_id'), include_participants=1, include_matches=1)
    except ChallongeException as e:
        await client.send_message(message.author, T_OnChallongeException.format(e))
    else:
        await update_channel_topic(kwargs.get('account'), t, client, message.channel)
        await modules.on_event(message.server.id, Events.on_forfeit, p1_name=message.author.name, t_name=t['name'], me=message.server.me)


@helpers('account', 'tournament_id')
@cmds.register(minPermissions=Permissions.Participant,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentStateConstraint.Underway)
async def next(client, message, **kwargs):
    """Get information about your next game
    No Arguments
    """
    msg, exc = await get_next_match(kwargs.get('account'), kwargs.get('tournament_id'), message.author.name)
    if exc:
        await client.send_message(message.channel, exc)
    elif msg:
        await client.send_message(message.channel, msg)
    else:
        await client.send_message(message.channel, '❌ Something went wrong. Sorry...')


@helpers('account', 'tournament_id')
@cmds.register(minPermissions=Permissions.Participant,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentStateConstraint.Pending)
async def checkin(client, message, **kwargs):
    """Check-in for the current tournament
    No Arguments
    """
    author_id, exc = await get_player(kwargs.get('account'), kwargs.get('tournament_id'), message.author.name)
    if exc:
        await client.send_message(message.channel, exc)
        return
    elif author_id:
        try:
            await kwargs.get('account').participants.check_in(kwargs.get('tournament_id'), author_id)
        except ChallongeException as e:
            await client.send_message(message.author, T_OnChallongeException.format(e))
        else:
            await client.send_message(message.channel, '✅ You have successfully checked in. Please wait for the organizers to start the tournament')


@helpers('account', 'tournament_id')
@cmds.register(minPermissions=Permissions.Participant,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentStateConstraint.Pending)
async def undocheckin(client, message, **kwargs):
    """Undo check-in for the current tournament
    No Arguments
    """
    try:
        participants = await kwargs.get('account').participants.index(kwargs.get('tournament_id'))
        for x in participants:
            if x['name'] == message.author.name:
                await kwargs.get('account').participants.undo_check_in(kwargs.get('tournament_id'), x['id'])
                break
    except ChallongeException as e:
        await client.send_message(message.author, T_OnChallongeException.format(e))
    else:
        await client.send_message(message.channel, '✅ Your checked in has been successfully reverted')


# USER


@required_args('username')
@cmds.register(channelRestrictions=ChannelType.Any)
async def username(client, message, **kwargs):
    """Set your Challonge username
    Required Argument:
    username -- If you don't have one, you can sign up here for free https://challonge.com/users/new
    """
    db.set_username(message.author, kwargs.get('username'))
    await client.send_message(message.channel, '✅ Your username \'{}\' has been set!'.format(kwargs.get('username')))


@optional_args('key')
@cmds.register(channelRestrictions=ChannelType.Private)
async def key(client, message, **kwargs):
    """Store your Challonge API key
    Look for it here: https://challonge.com/settings/developer
    Optional Argument:
    key -- the Challonge API key
    """
    if kwargs.get('key') and len(kwargs.get('key')) % 8 != 0:
        await client.send_message(message.author, '❌ Error: please check again your key')
    else:
        db.set_api_key(message.author, kwargs.get('key'))
        if kwargs.get('key'):
            await client.send_message(message.author, '✅ Thanks, your key has been encrypted and stored on our server!')
        else:
            await client.send_message(message.author, '✅ Thanks, your key has been removed from our server!')




@helpers('account', 'tournament_id', 'participant_username', 'tournament_role')
@cmds.register(channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentStateConstraint.Pending)
async def join(client, message, **kwargs):
    """Join the current tournament
    No Arguments
    """
    try:
        participant = await kwargs.get('account').participants.create(kwargs.get('tournament_id'), message.author.name, challonge_username=kwargs.get('participant_username'))
    except ChallongeException as e:
        await client.send_message(message.author, T_OnChallongeException.format(e))
    else:
        await client.add_roles(message.author, kwargs.get('tournament_role'))
        await client.send_message(message.channel, '✅ You have successfully joined the tournament')
        try:
            t = await kwargs.get('account').tournaments.show(kwargs.get('tournament_id'), include_participants=1, include_matches=1)
        except ChallongeException as e:
            await client.send_message(message.author, T_OnChallongeException.format(e))
        else:
            await update_channel_topic(kwargs.get('account'), t, client, message.channel)
            await modules.on_event(message.server.id, Events.on_join, p1_name=message.author.name, t_name=t['name'], me=message.server.me)
        # TODO more info
