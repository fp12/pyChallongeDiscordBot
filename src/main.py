import discord

from const import (C_RoleName,
                   T_Log_JoinedServer, T_JoinServer_Header, T_Log_RemovedServer, T_Log_CleanRemovedServer,
                   T_JoinServer_NeedName, T_JoinServer_NeedKey, T_JoinServer_NeedNothing, T_JoinServer_NeedAll,
                   T_JoinServer_SetupDone, C_ManagementChannelName)
from config import app_config
from log import log_main
from profiling import profile_async, Scope
from commands.core import cmds
from database.core import db
from modules.core import modules


log_main.debug('app_start')


client = discord.Client()


@profile_async(Scope.Core)
async def greet_new_server(server):
    log_main.info(T_Log_JoinedServer.format(server.name, server.id, server.owner.name, server.owner.id))

    owner = db.get_user(server.owner.id)
    if not owner or not owner.discord_id:
        db.add_user(server.owner)

    # get assigned role from add link
    for r in server.me.roles:
        if r.name == C_RoleName:
            await on_challonge_role_assigned(server, r)


@profile_async(Scope.Core)
async def cleanup_removed_server(serverid):
    db.remove_server(serverid)
    log_main.info(T_Log_CleanRemovedServer.format(serverid))


@profile_async(Scope.Core)
async def on_ready_impl():
    log_main.info('Challonge Bot ready')

    db_servers = db.get_servers_id()

    for s in [s for s in client.servers if s.id not in db_servers]:
        log_main.info('on_ready greeting new server ' + s.name)
        await greet_new_server(s)

    for sid in [server_id for server_id in db_servers if client.get_server(server_id) not in client.servers]:
        log_main.info('on_ready cleaning removed server {0}'.format(sid))
        await cleanup_removed_server(sid)

    await modules.set_client(client)

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

    overwrite = discord.PermissionOverwrite()
    overwrite.send_messages = False
    overwrite.read_messages = False
    await client.edit_channel_permissions(chChannel, server.default_role, overwrite)

    overwrite = discord.PermissionOverwrite()
    overwrite.send_messages = True
    overwrite.read_messages = True
    overwrite.manage_messages = True
    overwrite.embed_links = True
    overwrite.attach_files = True
    overwrite.read_message_history = True
    overwrite.manage_channel = True
    await client.edit_channel_permissions(chChannel, chRole, overwrite)

    # notify owner
    owner = db.get_user(server.owner.id)
    needName = owner.challonge_user_name is None
    needKey = owner.api_key is None

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
    log_main.info(T_Log_RemovedServer.format(server.name, server.id, server.owner.name, server.owner.id))
    await cleanup_removed_server(server.id)


@profile_async(Scope.Core)
async def on_member_update_impl(before, after):
    if before != before.server.me:
        return

    statusChange = '/' if before.status == after.status else '\'{}\'->\'{}\''.format(before.status, after.status)
    gameChange = '/' if before.game == after.game else '\'{}\'->\'{}\''.format(before.game.name, after.game.name)
    avatarChange = '/' if before.avatar_url == after.avatar_url else '\'{}\'->\'{}\''.format(before.avatar_url, after.avatar_url)
    nickchange = '/' if before.nick == after.nick else '\'{}\'->\'{}\''.format(before.nick, after.nick)

    if before.roles != after.roles:
        deleted = [x.name for x in before.roles if x not in after.roles]
        added = [x.name for x in after.roles if x not in before.roles]
        rolesChange = '-{}'.format(' -'.join(deleted)) if len(deleted) > 0 else '' + ' +{}'.format(' +'.join(added)) if len(added) > 0 else ''
    else:
        rolesChange = '/'

    log_main.info('on_member_update [Server \'{}\'] [Status {}] [Game {}] [Avatar {}] [Nick {}] [Roles {}]'.format(
        before.server.name, statusChange, gameChange, avatarChange, nickchange, rolesChange))

    added = [x for x in after.roles if x not in before.roles and x.name == C_RoleName]
    if len(added) == 1:
        await on_challonge_role_assigned(before.server, added[0])


@client.event
async def on_member_update(before, after):
    await on_member_update_impl(before, after)


@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return

    await cmds.try_execute(client, message)


client.run(app_config['discord_token'])


log_main.debug('app_stop')
