import discord
from config import appConfig
import challonge
from c_users import users_db
from c_servers import servers_db

client = discord.Client()

@client.event
async def on_ready():
	print('# Starting cleanup')
	testServer = client.get_server('188517330127552513')
	account = users_db.get_account(testServer)

	for t in await account.tournaments.index():
	       if t["name"].startswith("pychallonge") or t["name"].startswith("bot_"):
	       		print(' removing tournament %s from challonge' % t["name"])
	        	await account.tournaments.destroy(t["id"])

	for r in testServer.roles:
		if r.name.startswith('Participant_'):
			print(' removing role %s from test server' % r.name)
			await client.delete_role(testServer, r)

	for c in list(testServer.channels):
		if c.name.startswith('t_bot'):
			print(' removing channel %s from test server' % c.name)
			await client.delete_channel(c)

	servers_db.remove_all_tournaments(testServer)

	print('# Done cleanup')
	client.logout()


client.run(appConfig['Discord']['token'])