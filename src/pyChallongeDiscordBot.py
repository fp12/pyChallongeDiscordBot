from config import appConfig
import discord
import asyncio
from c_users import users_db
from c_servers import servers_db
from const import *
import commands_def
from commands_core import commands


print('app_start')

client = discord.Client()


async def greet_new_server(server):
    print(T_Log_JoinedServer.format(server.name, server.id, server.owner.name, server.owner.id))

    users_db.add(server.owner.id)

    # get assigned role from add link
    for r in server.me.roles:
         if r.name == C_RoleName:
             await on_challonge_role_assigned(server, r)

async def cleanup_removed_server(serverid):
    servers_db.remove(serverid)
    print(T_Log_CleanRemovedServer.format(serverid))

@client.event
async def on_ready():
    print('on_ready')    

    for s in [s for s in client.servers if s.id not in servers_db]:
        print('on_ready greeting new server ' + s.name)
        await greet_new_server(s)

    for sid in [s['id'] for s in servers_db if client.get_server(s['id']) not in client.servers]:
        print('on_ready cleaning removed server ' + sid)
        await cleanup_removed_server(sid)


async def on_challonge_role_assigned(server, chRole):
    await client.move_role(server, chRole, 1)
    
    # now create a channel
    chChannel = await client.create_channel(server, C_ManagementChannelName)
        
    servers_db.add(server, chChannel)
    
    await client.edit_channel_permissions(chChannel, chRole)
    
    # notify owner
    info = users_db.get_organizer(server.owner.id)
    needName = info == None or info.has_username() == False
    needKey = info == None or info.has_key() == False
    if needName or needKey:
        if needName and needKey == False:
            msg = T_JoinServer_NeedName
        elif needKey and needName == False:
            msg = T_JoinServer_NeedKey.format(server.owner.name)
        else:
            msg = T_JoinServer_NeedAll
    else:
        msg = T_JoinServer_NeedNothing

    header = T_JoinServer_Header.format(server.name)
    footer = T_JoinServer_SetupDone
    await client.send_message(server.owner, header + msg + '\n' + footer)

@client.event
async def on_server_join(server):    
    await greet_new_server(server)


@client.event
async def on_server_remove(server):
    print(T_Log_RemovedServer.format(server.name, server.id, server.owner.name, server.owner.id))
    await cleanup_removed_server(server.id)

@client.event
async def on_member_update(before, after):
    if before != before.server.me:
        return
    
    statusChange = '/' if before.status == after.status else '{}->{}'.format(before.status, after.status)
    gameChange = '/' if before.game == after.game else '{}->{}'.format(before.game.name, after.game.name)
    avatarChange = '/' if before.avatar_url == after.avatar_url else '{}->{}'.format(before.avatar_url, after.avatar_url)
    nickchange = '/' if before.nick == after.nick else '{}->{}'.format(before.nick, after.nick)

    if before.roles != after.roles:
        deleted = [x.name for x in before.roles if x not in after.roles]
        added = [x.name for x in after.roles if x not in before.roles]
        rolesChange = ' -{}'.format(' -'.join(deleted)) if len(deleted) > 0 else '' + ' +{}'.format(' +'.join(added)) if len(added) > 0 else ''
    else:
        rolesChange = '/'
    print('on_member_update [Status {}] [Game {}] [Avatar {}] [Nick {}] [Roles{}]'.format(statusChange, gameChange, avatarChange, nickchange, rolesChange))

    added = [x for x in after.roles if x not in before.roles and x.name == C_RoleName]
    if len(added) == 1:
        await on_challonge_role_assigned(before.server, added[0])


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    await commands.try_execute(client, message)

    #cmd = commands.validate_command(client, message)
    #if cmd != None and await cmd.validate_context(client, message):    
    #    await cmd.execute(client, message)


client.run(appConfig['Discord']['token'])

print('app_stop')