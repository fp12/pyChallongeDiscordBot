import discord
import asyncio
from c_users import users_db
from c_servers import servers_db
from text import *
from const import *

async def shutdown(client, message):
    await client.send_message(message.channel, 'logging out...')
    await client.logout()
    sys.exit()

async def key(client, message, **kwArgs):
    users_db.set_key(message.author.id, kwArgs.get('key'))
    await client.send_message(message.author, 'Your key has been set!')


async def organization(client, message):
    await client.send_message(message.channel, 'organization')


async def promote(client, message):
    await client.send_message(message.channel, 'promote')


async def create(client, message, **kwArgs):
    await client.send_message(message.channel, 'create')


async def shuffleseeds(client, message):
    await client.send_message(message.channel, 'shuffleseeds')


async def start(client, message):
    await client.send_message(message.channel, 'start')


async def reset(client, message):
    await client.send_message(message.channel, 'reset')


async def checkin_start(client, message):
    await client.send_message(message.channel, 'checkin_start')


async def checkin_stop(client, message):
    await client.send_message(message.channel, 'checkin_stop')


async def finalize(client, message):
    await client.send_message(message.channel, 'finalize')


async def reopen(client, message):
    await client.send_message(message.channel, 'reopen')


async def update(client, message):
    await client.send_message(message.channel, 'update')


async def forfeit(client, message):
    await client.send_message(message.channel, 'forfeit')


async def next(client, message):
    await client.send_message(message.channel, 'next')


async def checkin(client, message):
    await client.send_message(message.channel, 'checkin')


async def username(client, message, **kwArgs):
    users_db.set_username(message.author.id, kwArgs.get('username'))
    await client.send_message(message.author, 'Your username \'{}\' has been set!'.format(kwArgs.get('username')))


async def help(client, message):
    await client.send_message(message.channel, 'help')


async def join(client, message):
    await client.send_message(message.channel, 'join')


async def feedback(client, message, **kwArgs):
    await client.send_message(message.channel, 'feedback')

async def leaveserver(client, message):
    channelId = servers_db.get_management_channel(message.channel.server)
    await client.delete_channel(discord.Channel(server=message.channel.server, id=channelId))
    roles = [x for x in message.channel.server.me.roles if x.name == C_RoleName]
    #if len(roles) == 1:
    #    await client.delete_role(message.channel.server, roles[0])
    await client.leave_server(message.channel.server)


