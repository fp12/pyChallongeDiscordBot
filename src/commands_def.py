import discord
import asyncio
from channel_type import ChannelType
from db_access import db
from const import *
from commands_core import *
from permissions import Permissions
from utils import *
from challonge import Account, ChallongeException
from challonge_accounts import ChallongeAccess, TournamentState
from challonge_utils import *
import string
# import cloudconvert
from config import appConfig
import os
from datetime import datetime, timedelta

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
            if index > 0:
                custom_topic = currentTopic[:index]
            else:
                custom_topic = currentTopic = currentTopic

        await client.edit_channel(channel, topic=custom_topic + T_ChannelDescriptionSeparator + desc)
        # Todo: better text


# DEV ONLY


@aliases('exit', 'out')
@commands.register(minPermissions=Permissions.Dev, channelRestrictions=ChannelType.Any)
async def shutdown(client, message, **kwargs):
    await client.send_message(message.channel, 'logging out...')
    await client.logout()


@optional_args('what')
@aliases('print')
@commands.register(minPermissions=Permissions.Dev, channelRestrictions=ChannelType.Any)
async def dump(client, message, **kwargs):
    def decorate(s):
        return '```ruby\n' + s + '```'

    maxChars = 1800
    what = kwargs.get('what')
    if what is None or what == 'commands':
        for page in paginate(commands.dump(), maxChars):
            await client.send_message(message.author, decorate(page))
    if what is None or what == 'profile':
        for page in paginate(db.dump_profile(), maxChars):
            await client.send_message(message.author, decorate(page))
    if what is None or what == 'servers':
        for page in paginate(db.dump_servers(), maxChars):
            await client.send_message(message.author, decorate(page))
    if what is None or what == 'users':
        for page in paginate(db.dump_users(), maxChars):
            await client.send_message(message.author, decorate(page))


@helpers('announcement')
@commands.register(minPermissions=Permissions.Dev, channelRestrictions=ChannelType.Private)
async def announce(client, message, **kwargs):
    for owner_id in db.get_servers_owners():
        await client.send_message(discord.User(id=owner_id), 'Message from bot author: ```ruby\n{0}```'.format(kwargs.get('announcement')))


# SERVER OWNER


@commands.register(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Any)
async def ping(client, message, **kwargs):
    timeSpent = datetime.now() - message.timestamp + timedelta(hours=4) # uct correction
    await client.send_message(message.channel, '✅ pong! `{0:.3f}`s'.format(timeSpent.total_seconds()))


@optional_args('trigger')
@commands.register(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Mods)
async def trigger(client, message, **kwargs):
    """Set/Unset a trigger command for the bot
    Since you may use several bots on your server, the Challonge allows you to set its own trigger
    Note: it is always possible to trigger it via a direct mention (@Challonge)
    Optional Argument:
    trigger -- the string to trigger bot actions
    """
    db.set_server_trigger(message.server, kwargs.get('trigger'))
    if kwargs.get('trigger'):
        await client.send_message(message.channel, '✅ You can now trigger the bot with `{0}` (or a mention) on this server'.format(kwargs.get('trigger')))
    else:
        await client.send_message(message.channel, '✅ You can now only trigger the bot with a mention on this server')


@required_args('member')
@commands.register(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Mods)
async def promote(client, message, **kwargs):
    """Promote a member to be able to manage tournaments with you
    You can also simply assign the member the role 'Challonge'
    Arguments:
    member -- mention (@) the member to be granted management rights
    """
    member_id = utils.get_user_id_from_mention(kwargs.get('member'))
    member = message.server.get_member(member_id)
    if member:
        for r in message.server.me.roles:
            if r.name == C_RoleName:
                try:
                    await client.add_roles(member, r)
                    await client.send_message(message.channel, '✅ Member **{0.name}** has been promoted'.format(member))
                except discord.errors.Forbidden:
                    await client.send_message(message.channel, T_PromoteError.format(member, message.server.owner.mention))
                finally:
                    return
        print('command:promote could not find \'{}\' Role? roles: {}'.format(
            C_RoleName, ' '.join([r.name for r in message.server.me.roles])))
    else:
        await client.send_message(message.channel, '❌ Could not find Member **{}**'.format(kwargs.get('member')))


@required_args('member')
@commands.register(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Mods)
async def demote(client, message, **kwargs):
    """Demote a member to be able to manage tournaments with you
    You can also simply unassign the member the role 'Challonge'
    Arguments:
    member -- mention (@) the member to be removed management rights
    """
    member_id = utils.get_user_id_from_mention(kwargs.get('member'))
    member = message.server.get_member(member_id)
    if member:
        for r in message.server.me.roles:
            if r.name == C_RoleName:
                try:
                    await client.remove_roles(member, r)
                    await client.send_message(message.channel, '✅ Member **{0.name}** has been demoted'.format(member))
                except discord.errors.Forbidden:
                    await client.send_message(message.channel, T_DemoteError.format(member, message.server.owner.mention))
                finally:
                    return
        print('command:promote could not find \'{}\' Role? roles: {}'.format(C_RoleName, ' '.join([r.name for r in message.server.me.roles])))
    else:
        await client.send_message(message.channel, '❌ Could not find Member **{}**'.format(kwargs.get('member')))


@commands.register(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Mods)
async def leaveserver(client, message, **kwargs):
    """Kick the Challonge bot out of your server
    Using this command, the bot will also remove the management channel it created
    """
    channelId = db.get_server(message.server).management_channel_id
    await client.delete_channel(discord.Channel(server=message.server, id=channelId))
    for r in message.server.me.roles:
        if x.name == C_RoleName:
            try:
                await client.delete_role(message.server, roles[0])
            except discord.errors.HTTPException as e:
                await client.send_message(message.server.owner, T_RemoveChallongeRoleError.format(e))
            else:
                break
    await client.leave_server(message.server)


# ORGANIZER


@helpers('account')
@aliases('new')
@optional_args('subdomain')
@required_args('name', 'url', 'type')
@commands.register(minPermissions=Permissions.Organizer,
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


@helpers('account', 'tournament_id')
@aliases('shuffle', 'randomize')
@commands.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentState.Pending)
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
@commands.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentState.Pending)
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
@commands.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentState.Underway)
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
        await client.send_message(message.channel, '✅ Tournament is has been reset!')
        await update_channel_topic(kwargs.get('account'), t, client, message.channel)
        # TODO real text ?


@helpers('account', 'tournament_id')
@required_args('date', 'time', 'duration')
@commands.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentState.Pending)
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
        await update_channel_topic(kwargs.get('account'), t, client, message.channel)
        # TODO real text ?


@helpers('account', 'tournament_id')
@commands.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentState.Pending)
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
        await update_channel_topic(kwargs.get('account'), t, client, message.channel)
        # TODO real text ?


@helpers('account', 'tournament_id')
@commands.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentState.Pending)
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
        await update_channel_topic(kwargs.get('account'), t, client, message.channel)
        # TODO real text ?


@helpers('account', 'tournament_id', 'tournament_role')
@commands.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentState.AwaitingReview)
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
        await update_channel_topic(kwargs.get('account'), t, client, message.channel)
        # TODO real text + show rankings


@helpers('account', 'tournament_id', 'tournament_role')
@commands.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentState.Any)
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
@commands.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentState.Any)
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
            matchesRepr, exc = await get_current_matches_repr(account, t)
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
@commands.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentState.Underway)
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
    p1_as_member, exc = get_member(kwargs.get('p1'), message.server)
    if exc:
        await client.send_message(message.channel, exc)
        return
    elif not p1_as_member:
        await client.send_message(message.channel, '❌ I could not find player 1 on this server')
        return

    # Verify second player: mention first, then name, then nick
    p2_as_member, exc = get_member(kwargs.get('p2'), message.server)
    if exc:
        await client.send_message(message.channel, exc)
        return
    elif not p2_as_member:
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
        await update_channel_topic(kwargs.get('account'), t, client, message.channel)


# PARTICIPANT


@helpers('account', 'tournament_id', 'participant_name')
@required_args('score', 'opponent')
@commands.register(minPermissions=Permissions.Participant,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentState.Underway)
async def update(client, message, **kwargs):
    """Report your score against another participant
    Required Arguments:
    score -- [YourScore]-[OpponentScore] : 5-0. Can be comma separated: 5-0,4-5,5-3
    opponent -- Your opponnent name or nickname or mention (mention is safer)
    """
    # Verify score format
    if not verify_score_format(kwargs.get('score')):
        await client.send_message(message.channel, '❌ Invalid score format. Please use the following 5-0,4-5,5-3')
        return

    # Verify other member: mention first, then name, then nick
    opponent_as_member = get_member(kwargs.get('opponent'), message.server)
    if not opponent_as_member:
        await client.send_message(message.channel, '❌ I could not find your opponent on this server')
        return

    p1_id, p2_id, exc = await get_players(kwargs.get('account'), kwargs.get('tournament_id'), message.author.name, opponent_as_member.name)
    if exc:
        await client.send_message(message.channel, exc)
        return
    elif not p1_id:
        await client.send_message(message.channel, '❌ I could not find you in this tournament')
        return
    elif not p2_id:
        await client.send_message(message.channel, '❌ I could not find your opponent in this tournament')
        return

    match, is_reversed, exc = await get_match(kwargs.get('account'), kwargs.get('tournament_id'), p1_id, p2_id)
    if exc:
        await client.send_message(message.channel, exc)
        return
    elif not match:
        await client.send_message(message.channel, '❌ Your current opponent is not ' + opponent_as_member.name)
        return

    winner_id = p1_id if author_is_winner(kwargs.get('score')) else p2_id
    score = kwargs.get('score') if not is_reversed else reverse_score(kwargs.get('score'))
    msg, exc = await update_score(kwargs.get('account'), kwargs.get('tournament_id'), match['id'], score, winner_id)
    if exc:
        await client.send_message(message.channel, exc)
        return
    else:
        await client.send_message(message.channel, msg)
        await update_channel_topic(kwargs.get('account'), t, client, message.channel)


@helpers('account', 'tournament_id', 'tournament_role')
@commands.register(minPermissions=Permissions.Participant,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentState.Any)
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


@helpers('account', 'tournament_id', 'participant_name')
@commands.register(minPermissions=Permissions.Participant,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentState.Underway)
async def next(client, message, **kwargs):
    """Get information about your next game
    No Arguments
    """
    author_id, exc = await get_player(kwargs.get('account'), kwargs.get('tournament_id'), message.author.name)
    if exc:
        await client.send_message(message.channel, exc)
        return
    elif author_id:
        try:
            openMatches = await kwargs.get('account').matches.index(kwargs.get('tournament_id'), state='open', participant_id=author_id)
        except ChallongeException as e:
            await client.send_message(message.author, T_OnChallongeException.format(e))
        else:
            if len(openMatches) > 0:
                if openMatches[0]['player1-id'] == author_id:
                    opponent_id = openMatches[0]['player2-id']
                else:
                    opponent_id = openMatches[0]['player1-id']

                try:
                    opponent = await kwargs.get('account').participants.show(kwargs.get('tournament_id'), opponent_id)
                except ChallongeException as e:
                    await client.send_message(message.author, T_OnChallongeException.format(e))
                else:
                    await client.send_message(message.channel, '✅ You have an open match 🆚 {0}'.format(opponent['name']))
            else:
                try:
                    pendingMatches = await kwargs.get('account').matches.index(kwargs.get('tournament_id'), state='pending', participant_id=author_id)
                except ChallongeException as e:
                    await client.send_message(message.author, T_OnChallongeException.format(e))
                else:
                    if len(openMatches) > 0:
                        await client.send_message(message.channel, '✅ You have a pending match. Please wait for it to open')
                    else:
                        await client.send_message(message.channel, '✅ You have no pending nor open match. It seems you\'re out of the tournament')
                    # TODO: better management of names


@helpers('account', 'tournament_id')
@commands.register(minPermissions=Permissions.Participant,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentState.Pending)
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


@helpers('account', 'tournament_id', 'participant_name')
@commands.register(minPermissions=Permissions.Participant,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentState.Pending)
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
@commands.register(channelRestrictions=ChannelType.Any)
async def username(client, message, **kwargs):
    """Set your Challonge username
    Required Argument:
    username -- If you don't have one, you can sign up here for free https://challonge.com/users/new
    """
    db.set_username(message.author, kwargs.get('username'))
    await client.send_message(message.channel, '✅ Your username \'{}\' has been set!'.format(kwargs.get('username')))


@optional_args('key')
@commands.register(channelRestrictions=ChannelType.Private)
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


@optional_args('command')
@commands.register(channelRestrictions=ChannelType.Any)
async def help(client, message, **kwargs):
    """Get help on usable commands
    If no argument is provided, a concise list of usable commands will be displayed
    Optional Argument:
    command -- the command you want more info on
    """
    commandName = kwargs.get('command')
    if commandName:
        command = commands.find(commandName)
        if command:
            try:
                await command.validate_context(client, message, [])
            except (InsufficientPrivileges, WrongChannel):
                await client.send_message(message.channel, '❌ Invalid command or you can\'t use it on this channel')
                return
            except:
                pass

            await client.send_message(message.channel, command.pretty_print())
        else:
            await client.send_message(message.channel, '❌ Inexistent command or you don\'t have enough privileges to use it')
    else:
        commandsStr = []
        async for c in AuthorizedCommandsWrapper(client, message):
            commandsStr.append(c)
        await client.send_message(message.channel, T_HelpGlobal.format('\n  '.join(commandsStr)))


@helpers('account', 'tournament_id', 'participant_username', 'tournament_role')
@commands.register(channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.RequiredForHost,
                   tournamentState=TournamentState.Pending)
async def join(client, message, **kwargs):
    """Join the current tournament
    No Arguments
    """
    try:
        participant = await kwargs.get('account').participants.create(kwargs.get('tournament_id'), message.author.name, user_name=kwargs.get('participant_username'))
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
        # TODO more info


@commands.register(channelRestrictions=ChannelType.Any)
async def info(client, message, **kwArgs):
    await client.send_message(message.channel, T_Info)
