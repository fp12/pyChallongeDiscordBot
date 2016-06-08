import discord
from config import appConfig
import challonge
from db_access import db
import challonge_accounts

client = discord.Client()


@client.event
async def on_ready():
    print('# Starting cleanup')
    testServer = client.get_server('188517330127552513')
    account = await challonge_accounts.get(testServer)

    for t in await account.tournaments.index():
        if t["name"].startswith("pychallonge") or t["name"].startswith("bot_"):
            print(' removing tournament %s from challonge' % t["name"])
            await account.tournaments.destroy(t["id"])

    for r in testServer.roles:
        if r.name.startswith('Participant_') or r.name.startswith('Challonge') and r not in testServer.me.roles:
            try:
                await client.delete_role(testServer, r)
                print(' removed role %s from test server' % r.name)
            except:
                pass

    for c in list(testServer.channels):
        if c.name.startswith('t_bot') or c.name.startswith('challongemanagement'):
            try:
                await client.delete_channel(c)
                print(' removed channel %s from test server' % c.name)
            except:
                pass

    db.remove_all_tournaments(testServer)

    print('# Done cleanup')
    client.logout()


client.run(appConfig['discord']['token'])
