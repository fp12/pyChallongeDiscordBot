import discord
import asyncio
import json
from c_users import users_db
import text
import permissions
import commands

client = discord.Client()

with open('config.json') as data_file:    
  config = json.load(data_file)

@client.event
async def on_ready():
  print('on_ready')

@client.event
async def on_server_join(server):
  print(text.Log_JoinedServer.format(server.name, server.id, server.owner.name, server.owner.id))
  info = users_db.get_organizer(server.owner.id)
  needName = info == None or info.has_username() == False
  needKey = info == None or info.has_key() == False
  if needName or needKey:
    if needName and needKey == False:
      msg = text.JoinServer_NeedName
    elif needKey and needName == False:
      msg = text.JoinServer_NeedKey.format(server.owner.name)
    else:
      msg = text.JoinServer_NeedBoth
  else:
    msg = text.JoinServer_NeedNothing
  header = text.JoinServer_Header.format(server.name)
  await client.send_message(server.owner, header + msg)
  newRole = await client.create_role(server, name='ChallongeTeam')
  newChannel = await client.create_channel(server, 'ChallongeManagement')
  await client.send_message(server.owner, 'a new channel and a new role have been created on the server')
  #await client.edit_channel_permissions(newChannel, newRole, )


@client.event
async def on_server_remove(server):
  print(text.Log_RemovedServer.format(server.name, server.id, server.owner.name, server.owner.id))

@client.event
async def on_message(message):
  if message.author == client.user:
    return

  cmd = commands.handler.validateCommand(client, message)
  if cmd != None and await cmd.validateContext(client, message):
    print(text.Log_ValidatedCommand.format(message.author.name, 'PM' if message.channel.is_private else message.channel.name, message.content))
    await cmd.execute(client, message)


client.run(config['Discord']['token'])