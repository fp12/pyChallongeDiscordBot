import discord
import asyncio
from c_users import users_db

async def shutdown(client, message):
  await client.send_message(message.channel, 'logging out...')
  await client.logout()

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