from datetime import datetime, timedelta
import asyncio
import urllib.request
import discord

from const import *
from discord_impl.permissions import Permissions
from discord_impl.channel_type import ChannelType
from database.core import db
from commands.core import cmds, aliases, required_args, optional_args, helpers, AuthorizedCommandsWrapper, MissingParameters
from log import log_commands_def


# SERVER OWNER


@required_args('module')
@cmds.register(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Mods)
async def module(client, message, **kwargs):
    try:
        f = urllib.request.urlopen('http://hastebin.com/raw/%s' % kwargs.get('module'))
    except urllib.error.HTTPError as e:
        await client.send_message(message.channel, '❌ Something went wrong while setting module... %s' % e)
    else:
        if await modules.load_from_raw(f.read().decode("utf-8"), message.server.id):
            await client.send_message(message.channel, '✅ Module has been set!')
        else:
            await client.send_message(message.channel, '❌ Something went wrong while setting module...')


@cmds.register(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Any)
async def ping(client, message, **kwargs):
    timeSpent = datetime.now() - message.timestamp + timedelta(hours=4)  # uct correction
    await client.send_message(message.channel, '✅ pong! `{0:.3f}`s'.format(timeSpent.total_seconds()))


@optional_args('trigger')
@cmds.register(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Mods)
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
@cmds.register(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Mods)
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
        log_commands_def.info('command:promote could not find \'{}\' Role? roles: {}'.format(
            C_RoleName, ' '.join([r.name for r in message.server.me.roles])))
    else:
        await client.send_message(message.channel, '❌ Could not find Member **{}**'.format(kwargs.get('member')))


@required_args('member')
@cmds.register(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Mods)
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
        log_commands_def.info('command:promote could not find \'{}\' Role? roles: {}'.format(C_RoleName, ' '.join([r.name for r in message.server.me.roles])))
    else:
        await client.send_message(message.channel, '❌ Could not find Member **{}**'.format(kwargs.get('member')))


@cmds.register(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Mods)
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


# USER


@optional_args('command')
@cmds.register(channelRestrictions=ChannelType.Any)
async def help(client, message, **kwargs):
    """Get help on usable commands
    If no argument is provided, a concise list of usable commands will be displayed
    Optional Argument:
    command -- the command you want more info on
    """
    commandName = kwargs.get('command')
    if commandName:
        command = cmds.find(commandName)
        if command:
            context_cache = {'db_server': db.get_server(message.server) if message.server else None}
            context_cache = cmds.get_context_cache_update(context_cache, message)
            validated, exc = await command.validate_context(client, message, [], context_cache)
            if validated or isinstance(exc, MissingParameters):
                await client.send_message(message.channel, command.pretty_print())
    else:
        commandsStr = []
        async for c in AuthorizedCommandsWrapper(client, message):
            commandsStr.append(c)
        await client.send_message(message.channel, T_HelpGlobal.format('\n  '.join(commandsStr)))


@cmds.register(channelRestrictions=ChannelType.Any)
async def info(client, message, **kwArgs):
    """Get info about the Challonge Bot
    No Arguments
    """
    await client.send_message(message.channel, T_Info)
