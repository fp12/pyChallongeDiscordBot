import discord
import asyncio
from c_users import users_db
from c_servers import servers_db, ChannelType
from const import *
from commands_core import commands, required_args, optional_args, aliases, ContextValidationError_InsufficientPrivileges
from permissions import Permissions


@aliases('exit', 'out')
@commands.register(minPermissions=Permissions.Dev, channelRestrictions=ChannelType.Any)
async def shutdown(client, message):
    await client.send_message(message.channel, 'logging out...')
    await client.logout()


@required_args('key')
@commands.register(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Private)
async def key(client, message, **kwargs):
    """Store your Challonge API key
    Look for it here: https://challonge.com/settings/developer
    Argument:
    key -- the Challonge API key
    """
    users_db.set_key(message.author.id, kwargs.get('key'))
    await client.send_message(message.author, 'Thanks, your key has been set!')


@optional_args('organization')
@commands.register(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Mods)
async def organization(client, message, **kwargs):
    """Set up a Challonge organization for a server (optional)
    Challonge organizations can be created here: http://challonge.com/organizations/new
    Optional Argument:
    organization -- if not set, it will be reset for this server
    """
    servers_db.edit(message.channel.server, **kwargs)
    organization = kwargs.get('organization')
    if organization == None:
        await client.send_message(message.channel, 'Organization has been reset for this server')
    else:
        await client.send_message(message.channel, 'Organization **{0}** has been set for this server'.format(organization))


@required_args('member')
@commands.register(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Mods)
async def promote(client, message, **kwargs):
    """Promote a server member to be able to manage tournaments with you
    You can also simply assign the member the role 'Challonge'
    Arguments:
    member -- the member to be granted management rights
    """
    member = message.channel.server.get_member_named(kwargs.get('member'))
    if member != None:
        for r in message.channel.server.me.roles:
            if r.name == C_RoleName:
                try:
                    await client.add_roles(member, *[r])
                    await client.send_message(message.channel, 'Member **{0.name}** has been promoted'.format(member))
                except discord.errors.Forbidden:
                    await client.send_message(message.channel, 'Could not promote Member **{0.name}** because of insufficient permissions.\n{1} could you add Role \'Challonge\' to this member? Thanks!'.format(member, message.channel.server.owner.mention))
                finally:
                    return
        print('command:promote could not find \'{}\' Role? roles: {}'.format(C_RoleName, ' '.join([r.name for r in message.channel.server.me.roles])))
    else:
        await client.send_message(message.channel, 'Could not find Member **{}**'.format(kwargs.get('member')))


@commands.register(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Mods)
async def leaveserver(client, message):
    """Kicks the Challonge bot out of your server
    Using this command, the bot will also remove the management channel it created
    """
    channelId = servers_db.get_management_channel(message.channel.server)
    await client.delete_channel(discord.Channel(server=message.channel.server, id=channelId))
    roles = [x for x in message.channel.server.me.roles if x.name == C_RoleName]
    #if len(roles) == 1:
    #    await client.delete_role(message.channel.server, roles[0])
    await client.leave_server(message.channel.server)


@aliases('new')
@required_args('name', 'urlname', 'type')
@commands.register(minPermissions=Permissions.Organizer, channelRestrictions=ChannelType.NewTourney)
async def create(client, message, **kwargs):
    """Creates a new tournament
    Arguments:
    name -- will be used as the tournament name
    urlname -- name used for the url http://challonge.com/urlname
    type -- can be [singleelim, doubleelim]
    """
    role = await client.create_role(message.channel.server, **{'name':'Participant_' + kwargs.get('name'), 'mentionable':True})
    chChannel = await client.create_channel(message.channel.server, 'T_' + kwargs.get('name'))
    servers_db.add_tournament(message.channel.server, **{'channel':chChannel.id, 'role':role.id, 'challongeid':0})
    await client.send_message(message.channel, T_TournamentCreated.format(kwargs.get('name'),
                                                                          'http://challonge.com/' + kwargs.get('urlname'),
                                                                          role.mention,
                                                                          chChannel.mention))


@aliases('shuffle')
@commands.register(minPermissions=Permissions.Organizer, channelRestrictions=ChannelType.Tournament)
async def shuffleseeds(client, message):
    await client.send_message(message.channel, 'shuffleseeds')


@aliases('launch')
@commands.register(minPermissions=Permissions.Organizer, channelRestrictions=ChannelType.Tournament)
async def start(client, message):
    await client.send_message(message.channel, 'start')


@commands.register(minPermissions=Permissions.Organizer, channelRestrictions=ChannelType.Tournament)
async def reset(client, message):
    await client.send_message(message.channel, 'reset')


@commands.register(minPermissions=Permissions.Organizer, channelRestrictions=ChannelType.Tournament)
async def checkin_start(client, message):
    await client.send_message(message.channel, 'checkin_start')


@commands.register(minPermissions=Permissions.Organizer, channelRestrictions=ChannelType.Tournament)
async def checkin_stop(client, message):
    await client.send_message(message.channel, 'checkin_stop')


@commands.register(minPermissions=Permissions.Organizer, channelRestrictions=ChannelType.Tournament)
async def finalize(client, message):
    await client.send_message(message.channel, 'finalize')


@required_args('player1', 'player2')
@commands.register(minPermissions=Permissions.Organizer, channelRestrictions=ChannelType.Tournament)
async def reopen(client, message, **kwargs):
    await client.send_message(message.channel, 'reopen')


@required_args('score')
@commands.register(minPermissions=Permissions.Participant, channelRestrictions=ChannelType.Tournament)
async def update(client, message, **kwargs):
    await client.send_message(message.channel, 'update')


@commands.register(minPermissions=Permissions.Participant, channelRestrictions=ChannelType.Tournament)
async def forfeit(client, message):
    await client.send_message(message.channel, 'forfeit')


@commands.register(minPermissions=Permissions.Participant, channelRestrictions=ChannelType.Tournament)
async def next(client, message):
    await client.send_message(message.channel, 'next')


@commands.register(minPermissions=Permissions.Participant, channelRestrictions=ChannelType.Tournament)
async def checkin(client, message):
    await client.send_message(message.channel, 'checkin')


@required_args('username')
@commands.register(minPermissions=Permissions.User, channelRestrictions=ChannelType.Any)
async def username(client, message, **kwargs):
    users_db.set_username(message.author.id, kwargs.get('username'))
    await client.send_message(message.author, 'Your username \'{}\' has been set!'.format(kwargs.get('username')))


@optional_args('command')
@commands.register(minPermissions=Permissions.User, channelRestrictions=ChannelType.Any)
async def help(client, message, **kwargs):
    commandName = kwargs.get('command')
    if commandName != None:
        command = commands.find(commandName)
        if command != None:
            try:
                command.validate_context(client, message, [])
            except ContextValidationError_InsufficientPrivileges:
                await client.send_message(message.channel, 'Inexistent command or you don\'t have enough privileges to use it')
                return
            except:
                pass
                
            await client.send_message(message.channel, command.pretty_print())
        else:
            await client.send_message(message.channel, 'Inexistent command or you don\'t have enough privileges to use it')
    else:
        commandsStr = []
        for c in commands.get_authorized_commands(client, message):
            commandsStr.append(c.simple_print())
        await client.send_message(message.channel, '```Usable commands for you in this channel:```\n' + '\n'.join(commandsStr) + '')


@commands.register(minPermissions=Permissions.User, channelRestrictions=ChannelType.Tournament)
async def join(client, message):
    await client.send_message(message.channel, 'join')


@required_args('feedback')
@commands.register(minPermissions=Permissions.User, channelRestrictions=ChannelType.Private)
async def feedback(client, message, **kwArgs):
    await client.send_message(message.channel, 'feedback')



#commands.dump()

