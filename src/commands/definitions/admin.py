import asyncio
import discord

from challonge import ChallongeException

from config import app_config
from commands.core import cmds, aliases, required_args, optional_args, helpers
from discord_impl.permissions import Permissions
from discord_impl.channel_type import ChannelType
from challonge_impl.accounts import get as get_account
from database.core import db
from log import set_level
from utils import ArrayFormater, paginate
from const import *


# DEV ONLY


@aliases('exit', 'out')
@cmds.register(minPermissions=Permissions.Dev, channelRestrictions=ChannelType.Private)
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
@cmds.register(minPermissions=Permissions.Dev, channelRestrictions=ChannelType.Private)
async def dump(client, message, **kwargs):
    def decorate(s):
        return '```ruby\n' + s + '```'

    name_id_fmt = '{0.name} ({0.id})'
    maxChars = 1800
    what = kwargs.get('what')
    if what is None or what == 'commands':
        for page in paginate(commands.dump(), maxChars):
            await client.send_message(message.author, decorate(page))
    if what is None or what == 'profile':
        pass
    if what is None or what == 'servers':
        a = ArrayFormater('Servers', 3)
        entries = []
        a.add('Server Name (ID)', 'Owner Name (ID)', 'Trigger')
        for s in db.get_servers():
            server = message.server
            if s.server_id:
                server = client.get_server(s.server_id)
                a.add(name_id_fmt.format(server), name_id_fmt.format(server.owner), str(s.trigger))
        for page in paginate(a.get(), maxChars):
            await client.send_message(message.author, decorate(page))
    if what is None or what == 'users':
        a = ArrayFormater('Users', 2)
        a.add('User Name (ID)', 'Challonge username')
        for u in db.get_users():
            if u.discord_id:
                user = None
                for server in client.servers:
                    user = discord.utils.get(server.members, id=u.discord_id)
                    if user:
                        break
                a.add(name_id_fmt. format(user), str(u.challonge_user_name))
        for page in paginate(a.get(), maxChars):
            await client.send_message(message.author, decorate(page))
    if what is None or what == 'tournaments':
        acc, exc = await get_account(app_config['devid'])
        if not acc:
            return
        a = ArrayFormater('Tournaments', 3)
        a.add('Server Name (ID)', 'Host Name (ID)', 'Tournament Url')
        for server in client.servers:
            for t in db.get_tournaments(server.id):
                host = discord.utils.get(server.members, id=t.host_id)
                url = 'Not Found'
                try:
                    t = await acc.tournaments.show(t.challonge_id)
                    url = t['full-challonge-url']
                except ChallongeException as e:
                    url = T_OnChallongeException.format(e)
                a.add(name_id_fmt.format(server), name_id_fmt.format(host), url)
        for page in paginate(a.get(), maxChars):
            await client.send_message(message.author, decorate(page))


@helpers('announcement')
@cmds.register(minPermissions=Permissions.Dev, channelRestrictions=ChannelType.Private)
async def announce(client, message, **kwargs):
    for owner_id in db.get_servers_owners():
        await client.send_message(discord.User(id=owner_id), 'Message from bot author: ```ruby\n{0}```'.format(kwargs.get('announcement')))
