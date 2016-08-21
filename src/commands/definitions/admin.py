import asyncio
import discord

from commands.core import cmds, aliases, required_args, optional_args, helpers
from discord_impl.permissions import Permissions
from discord_impl.channel_type import ChannelType
from database.core import db
from log import set_level
from utils import paginate


# DEV ONLY


@aliases('exit', 'out')
@cmds.register(minPermissions=Permissions.Dev, channelRestrictions=ChannelType.Any)
async def shutdown(client, message, **kwargs):
    await client.send_message(message.channel, 'logging out...')
    await client.logout()


@required_args('level')
@optional_args('what')
@cmds.register(minPermissions=Permissions.Dev, channelRestrictions=ChannelType.Private)
async def log(client, message, **kwargs):
    set_level(kwargs.get('level'), kwargs.get('what', None))
    await client.send_message(message.channel, 'Done')


@optional_args('what')
@aliases('print')
@cmds.register(minPermissions=Permissions.Dev, channelRestrictions=ChannelType.Any)
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
@cmds.register(minPermissions=Permissions.Dev, channelRestrictions=ChannelType.Private)
async def announce(client, message, **kwargs):
    for owner_id in db.get_servers_owners():
        await client.send_message(discord.User(id=owner_id), 'Message from bot author: ```ruby\n{0}```'.format(kwargs.get('announcement')))
