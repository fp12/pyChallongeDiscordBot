from config import appConfig
import discord
import asyncio
from const import *
import commands_def
from commands_core import commands
from profiling import profile_async, Scope
from db_access import db

print('app_start')


client = discord.Client()


@profile_async(Scope.Core)
async def greet_new_server(server):
    print(T_Log_JoinedServer.format(server.name,
                                    server.id, server.owner.name, server.owner.id))

    db.add_user(server.owner)

    # get assigned role from add link
    for r in server.me.roles:
        if r.name == C_RoleName:
            await on_challonge_role_assigned(server, r)


@profile_async(Scope.Core)
async def cleanup_removed_server(serverid):
    db.remove_server(serverid)
    print(T_Log_CleanRemovedServer.format(serverid))


@profile_async(Scope.Core)
async def on_ready_impl():
    print('on_ready')

    db_servers = db.get_servers_id()

    for s in [s for s in client.servers if s.id not in db_servers]:
        print('on_ready greeting new server ' + s.name)
        await greet_new_server(s)

    for sid in [server_id for server_id in db_servers if client.get_server(server_id) not in client.servers]:
        print('on_ready cleaning removed server %d' % sid)
        await cleanup_removed_server(sid)

    # Should we do a sanity check?


@client.event
async def on_ready():
    await on_ready_impl()


@profile_async(Scope.Core)
async def on_challonge_role_assigned(server, chRole):
    try:
        await client.move_role(server, chRole, 1)
    except discord.errors.HTTPException:
        pass

    # now create a channel
    chChannel = await client.create_channel(server, C_ManagementChannelName)

    db.add_server(server, chChannel)

    await client.edit_channel_permissions(chChannel, chRole)

    # notify owner
    owner = db.get_user(server.owner)
    needName = owner.user_name == ''
    needKey = owner.api_key == ''

    if needName and not needKey:
        msg = T_JoinServer_NeedName
    elif needKey and not needName:
        msg = T_JoinServer_NeedKey.format(server.owner.name)
    elif needKey and needName:
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


@profile_async(Scope.Core)
async def on_member_update_impl(before, after):
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
    print('on_member_update [Status {}] [Game {}] [Avatar {}] [Nick {}] [Roles{}]'.format(
        statusChange, gameChange, avatarChange, nickchange, rolesChange))

    added = [x for x in after.roles if x not in before.roles and x.name == C_RoleName]
    if len(added) == 1:
        await on_challonge_role_assigned(before.server, added[0])


@client.event
async def on_member_update(before, after):
    await on_member_update_impl(before, after)


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    await commands.try_execute(client, message)


client.run(appConfig['Discord']['token'])

print('app_stop')
