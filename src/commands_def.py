import discord
import asyncio
from c_users import users_db
from c_servers import servers_db
from const import *
from commands import commands, required_args, optional_args, aliases
from permissions import Permissions, ChannelType


@aliases('exit', 'out')
@commands.register(minPermissions=Permissions.Dev, channelRestrictions=ChannelType.Any)
async def shutdown(client, message):
    await client.send_message(message.channel, 'logging out...')
    await client.logout()


@required_args('key')
@commands.register(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Private)
async def key(client, message, **kwArgs):
    users_db.set_key(message.author.id, kwArgs.get('key'))
    await client.send_message(message.author, 'Thanks, your key has been set!')


@optional_args('organization')
@commands.register(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Mods)
async def organization(client, message, **kwargs):
    servers_db.edit(message.channel.server, **kwargs)
    organization = kwargs.get('organization')
    if organization == None:
        await client.send_message(message.channel, 'Organization has been reset for this server')
    else:
        await client.send_message(message.channel, 'Organization **{0}** has been set for this server'.format(organization))


@required_args('member')
@commands.register(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Mods)
async def promote(client, message, **kwargs):
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
    channelId = servers_db.get_management_channel(message.channel.server)
    await client.delete_channel(discord.Channel(server=message.channel.server, id=channelId))
    roles = [x for x in message.channel.server.me.roles if x.name == C_RoleName]
    #if len(roles) == 1:
    #    await client.delete_role(message.channel.server, roles[0])
    await client.leave_server(message.channel.server)


@aliases('new')
@required_args('name', 'type')
@commands.register(minPermissions=Permissions.Organizer, channelRestrictions=ChannelType.NewTourney)
async def create(client, message, **kwArgs):
    await client.send_message(message.channel, 'create')


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
async def username(client, message, **kwArgs):
    users_db.set_username(message.author.id, kwArgs.get('username'))
    await client.send_message(message.author, 'Your username \'{}\' has been set!'.format(kwArgs.get('username')))


@optional_args('command')
@commands.register(minPermissions=Permissions.User, channelRestrictions=ChannelType.Any)
async def help(client, message, **kwargs):
    await client.send_message(message.channel, 'help')


@commands.register(minPermissions=Permissions.User, channelRestrictions=ChannelType.Tournament)
async def join(client, message):
    await client.send_message(message.channel, 'join')


@required_args('feedback')
@commands.register(minPermissions=Permissions.User, channelRestrictions=ChannelType.Private)
async def feedback(client, message, **kwArgs):
    await client.send_message(message.channel, 'feedback')



#commands.dump()

