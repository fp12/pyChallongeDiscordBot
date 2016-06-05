import discord
import asyncio
from c_users import users_db, ChallongeAccess
from c_servers import servers_db, ChannelType
from const import *
from commands_core import *
from permissions import Permissions
from profiling import collector
from utils import *
import challonge_utils
from challonge import Account, ChallongeException
import string
import re

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
        for page in paginate(collector.dump(), maxChars):
            await client.send_message(message.author, decorate(page))
    if what is None or what == 'servers':
        for page in paginate(servers_db.dump(), maxChars):
            await client.send_message(message.author, decorate(page))
    if what is None or what == 'users':
        for page in paginate(users_db.dump(), maxChars):
            await client.send_message(message.author, decorate(page))


# SERVER OWNER

@required_args('key')
@commands.register(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Private)
async def key(client, message, **kwargs):
    """Store your Challonge API key
    Look for it here: https://challonge.com/settings/developer
    Argument:
    key -- the Challonge API key
    """
    if len(kwargs.get('key')) % 8 != 0:
        await client.send_message(message.author, '❌ Error: please check again your key')
    else:
        users_db.set_key(message.author.id, kwargs.get('key'))
        await client.send_message(message.author, '✅ Thanks, your key has been encrypted and stored on our server!')


@optional_args('organization')
@commands.register(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Mods)
async def organization(client, message, **kwargs):
    """Set up a Challonge organization for a server (optional)
    Challonge organizations can be created here: http://challonge.com/organizations/new
    Optional Argument:
    organization -- if not set, it will be reset for this server
    """
    servers_db.edit(message.server, **kwargs)
    organization = kwargs.get('organization')
    if organization is None:
        await client.send_message(message.channel, '✅ Organization has been reset for this server')
    else:
        await client.send_message(message.channel, '✅ Organization **{0}** has been set for this server'.format(organization))


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
    channelId = servers_db.get_management_channel(message.server)
    await client.delete_channel(discord.Channel(server=message.server, id=channelId))
    roles = [x for x in message.server.me.roles if x.name == C_RoleName]
    if len(roles) == 1:
        try:
            await client.delete_role(message.server, roles[0])
        except discord.errors.Forbidden:
            await client.send_message(message.server.owner, T_RemoveChallongeRoleError)
    await client.leave_server(message.server)


# ORGANIZER

@helpers('account')
@aliases('new')
@optional_args('subdomain')
@required_args('name', 'url', 'type')
@commands.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.NewTourney,
                   challongeAccess=ChallongeAccess.Required)
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
    with Profiler(Scope.Core, name='create_') as p: 
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
    tournament_type = 'single elimination' if kwargs.get('type') == 'singleelim'\
        else 'double elimination' if kwargs.get('type') == 'doubleelim'\
        else 'round robin' if kwargs.get('type') == 'roundrobin'\
        else 'swiss'

    params = {}
    if kwargs.get('subdomain', None):
        params['subdomain'] = kwargs.get('subdomain')
    elif servers_db.get_organization(message.server):
        params['subdomain'] = servers_db.get_organization(
            message.server)

    try:
        t = await kwargs.get('account').tournaments.create(kwargs.get('name'), kwargs.get('url'), tournament_type, **params)
    except ChallongeException as e:
        await client.send_message(message.author, T_OnChallongeException.format(e))
    else:
        role = await client.create_role(message.server, name='Participant_' + kwargs.get('name'), mentionable=True)
        chChannel = await client.create_channel(message.server, 'T_' + kwargs.get('name'))
        servers_db.add_tournament(message.server, channel=chChannel.id, role=role.id, challongeid=t['id'])
        await client.send_message(message.channel, T_TournamentCreated.format(kwargs.get('name'),
                                                                              t['full-challonge-url'],
                                                                              role.mention,
                                                                              chChannel.mention))


@helpers('account', 'tournament_id')
@aliases('shuffle', 'randomize')
@commands.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.Required)
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
                   challongeAccess=ChallongeAccess.Required)
async def start(client, message, **kwargs):
    """Start a tournament
    This channel will be locked for writing except for participants / organizers
    No Arguments
    """
    try:
        await kwargs.get('account').tournaments.start(kwargs.get('tournament_id'))
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
        # TODO real text (with games to play...)
        # Discord won't display SVGs yet, so have a look at:
        # https://cloudconvert.com/api/svgtopng


@helpers('account', 'tournament_id')
@commands.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.Required)
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
        # TODO real text ?


@helpers('account', 'tournament_id')
@commands.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.Required)
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
        # TODO real text ?


@helpers('account', 'tournament_id')
@commands.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.Required)
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
        # TODO real text ?


@helpers('account', 'tournament_id', 'tournament_role')
@commands.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.Required)
async def finalize(client, message, **kwargs):
    """Finalize a tournament
    Tournament will be closed and no further modifications will be possible
    Be sure to upload attachements before finalizing
    This Channel will be locked for writing except for organizers
    No Arguments
    """
    try:
        await kwargs.get('account').tournaments.finalize(kwargs.get('tournament_id'))
    except ChallongeException as e:
        await client.send_message(message.author, T_OnChallongeException.format(e))
    else:
        # let's remove the role associated to this tournament.
        # only the Challonge role will be able to write in it
        await client.delete_role(message.server, kwargs.get('tournament_role'))
        await client.send_message(message.channel, '✅ Tournament has been finalized!')
        # TODO real text ?


@helpers('account', 'tournament_id', 'tournament_role')
@commands.register(minPermissions=Permissions.Organizer,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.Required)
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
        channelId = servers_db.get_management_channel(message.server)
        await client.send_message(discord.Channel(server=message.server, id=channelId), '✅ Tournament {0} has been destroyed by {1}!'.format(t['name'], message.author.mention))
        servers_db.remove_tournament(message.server, kwargs.get('tournament_id'))


# PARTICIPANT

@helpers('account', 'tournament_id', 'participant_name')
@required_args('score', 'opponent')
@commands.register(minPermissions=Permissions.Participant,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.Required)
async def update(client, message, **kwargs):
    """Report your score against another participant
    Required Arguments:
    score -- [YourScore]-[OpponentScore] : 5-0. Can be comma separated: 5-0,4-5,5-3
    opponent --Your opponnent name or nickname or mention (mention is safer)
    """
    # Verify score format
    result = re.compile('(\d+-\d+)(,\d+-\d+)*')
    if not result.match(kwargs.get('score')):
        await client.send_message(message.channel, '❌ Invalid score format. Please use the following 5-0,4-5,5-3')
        return
    # Verify other member: mention first, then name, then nick
    opponentId = utils.get_user_id_from_mention(kwargs.get('opponent'))
    if opponentId == 0:
        member = message.server.get_member_named(
            kwargs.get('opponent'))
        if member:
            opponentId = member.id

    member = discord.utils.get(message.server.members, id=opponentId)
    if member is None:
        await client.send_message(message.channel, '❌ I could not find your opponent on this server')
        return

    # Process
    try:
        participants = await kwargs.get('account').participants.index(kwargs.get('tournament_id'))
    except ChallongeException as e:
        await client.send_message(message.author, T_OnChallongeException.format(e))
    else:
        for x in participants:
            if x['name'] == member.name:
                opponentId = x['id']
            elif x['name'] == message.author.name:
                authorId = x['id']
        if not authorId:
            await client.send_message(message.channel, '❌ I could not find you in this tournament')
            return
        elif not opponentId:
            await client.send_message(message.channel, '❌ I could not find your opponent in this tournament')
            return
        else:
            try:
                openMatches = await kwargs.get('account').matches.index(kwargs.get('tournament_id'), state='open', participant_id=authorId)
            except ChallongeException as e:
                await client.send_message(message.author, T_OnChallongeException.format(e))
            else:
                for m in openMatches:
                    if m['player1-id'] == authorId and m['player2-id'] == opponentId or\
                            m['player2-id'] == authorId and m['player1-id'] == opponentId:
                        winner_id = authorId if challonge_utils.author_is_winner(kwargs.get('score')) else opponentId
                        score = kwargs.get('score') if m['player1-id'] == authorId else challonge_utils.reverse_score(kwargs.get('score'))
                        try:
                            await kwargs.get('account').matches.update(kwargs.get('tournament_id'), m['id'], scores_csv=score, winner_id=winner_id)
                        except ChallongeException as e:
                            await client.send_message(message.author, T_OnChallongeException.format(e))
                            return
                        else:
                            await client.send_message(message.channel, '✅ Your results have been uploaded')
                            # TODO: print next games for both players
                            return
                await client.send_message(message.channel, '❌ Your current opponent is not ' + member.name)
                            


@helpers('account', 'tournament_id', 'participant_name', 'tournament_role')
@commands.register(minPermissions=Permissions.Participant,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.Required)
async def forfeit(client, message, **kwargs):
    """Forfeit for the current tournament
    If the tournament is pending, you will be removed from the participants list
    If the tournament is in progress, Challonge will forfeit your potential remaining games
    and you won't be able to write in this channel anymore
    No Arguments
    """
    try:
        participants = await kwargs.get('account').participants.index(kwargs.get('tournament_id'))
        for x in participants:
            if x['name'] == message.author.name:
                await kwargs.get('account').participants.destroy(kwargs.get('tournament_id'), x['id'])
                break
    except ChallongeException as e:
        await client.send_message(message.author, T_OnChallongeException.format(e))
    else:
        await client.remove_roles(message.author, kwargs.get('tournament_role'))
        await client.send_message(message.channel, '✅ You forfeited from this tournament')


@helpers('account', 'tournament_id', 'participant_name')
@commands.register(minPermissions=Permissions.Participant,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.Required)
async def next(client, message, **kwargs):
    await client.send_message(message.channel, 'next')


@helpers('account', 'tournament_id')
@commands.register(minPermissions=Permissions.Participant,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.Required)
async def checkin(client, message, **kwargs):
    """Check-in for the current tournament
    No Arguments
    """
    try:
        participants = await kwargs.get('account').participants.index(kwargs.get('tournament_id'))
        for x in participants:
            if x['name'] == message.author.name:
                await kwargs.get('account').participants.check_in(kwargs.get('tournament_id'), x['id'])
                break
    except ChallongeException as e:
        await client.send_message(message.author, T_OnChallongeException.format(e))
    else:
        await client.send_message(message.channel, '✅ You have successfully checked in. Please wait for the organizers to start the tournament')


@helpers('account', 'tournament_id', 'participant_name')
@commands.register(minPermissions=Permissions.Participant,
                   channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.Required)
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
    """Sets your Challonge username
    Argument:
    username -- If you don't have one, you can sign up here for free https://challonge.com/users/new
    """
    users_db.set_username(message.author.id, kwargs.get('username'))
    await client.send_message(message.channel, '✅ Your username \'{}\' has been set!'.format(kwargs.get('username')))


@optional_args('command')
@commands.register(minPermissions=Permissions.User, channelRestrictions=ChannelType.Any)
async def help(client, message, **kwargs):
    """Gets help on usable commands
    If no argument is provided, a concise list of usable commands will be displayed
    Optional Argument:
    command -- the command you want more info on
    """
    commandName = kwargs.get('command')
    if commandName is not None:
        command = commands.find(commandName)
        if command is not None:
            try:
                command.validate_context(client, message, [])
            except (ContextValidationError_InsufficientPrivileges, ContextValidationError_WrongChannel):
                await client.send_message(message.channel, '❌ Invalid command or you can\'t use it on this channel')
                return
            except:
                pass

            await client.send_message(message.channel, command.pretty_print())
        else:
            await client.send_message(message.channel, '❌ Inexistent command or you don\'t have enough privileges to use it')
    else:
        commandsStr = []
        for c in commands.get_authorized_commands(client, message):
            commandsStr.append(c.simple_print())
        await client.send_message(message.channel, 'Usable commands for you in this channel:\n' + '\n'.join(commandsStr) + '')


@helpers('account', 'tournament_id', 'participant_username', 'tournament_role')
@commands.register(channelRestrictions=ChannelType.Tournament,
                   challongeAccess=ChallongeAccess.Required)
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
        # TODO more info


@required_args('feedback')
@commands.register(channelRestrictions=ChannelType.Private)
async def feedback(client, message, **kwArgs):
    await client.send_message(message.channel, 'feedback')
