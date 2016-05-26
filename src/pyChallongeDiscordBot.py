import discord
import asyncio
import json
from c_users import users_db
from c_servers import servers_db
import text
import permissions
import commands

client = discord.Client()

with open('config/config.json') as data_file:
    config = json.load(data_file)


@client.event
async def on_ready():
    print('on_ready')


@client.event
async def on_server_join(server):
    print(text.Log_JoinedServer.format(server.name, server.id, server.owner.name, server.owner.id))

    # greetings stuff
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
    
    # setup: channel in this server
    newChannel = await client.create_channel(server, 'ChallongeManagement')
    # await client.edit_channel_permissions(newChannel, newRole, )

    servers_db.add(server, newChannel)
    
    # notify owner
    await client.send_message(server.owner, header + msg + '\n' + text.JoinServer_SetupDone)


@client.event
async def on_server_remove(server):
    print(text.Log_RemovedServer.format(server.name, server.id, server.owner.name, server.owner.id))

    # notify server owner
    await client.send_message(server.owner, text.LeaveServer_Instructions.format(server.name))

    # delete the Challonge role (auto created and used for management purposes)
    for r in server.roles:
        if r.name == 'Challonge':
            await client.delete_role(server, r)

    # delete the Management channel
    for c in server.channels:
        if c.name == 'ChallongeManagement':
            await client.delete_channel(c)



@client.event
async def on_message(message):
    if message.author == client.user:
        return

    cmd = commands.handler.validateCommand(client, message)
    if cmd != None and await cmd.validateContext(client, message):
        print(text.Log_ValidatedCommand.format(message.author.name,
                                               'PM' if message.channel.is_private else message.channel.name,
                                               message.content))
        await cmd.execute(client, message)


client.run(config['Discord']['token'])
