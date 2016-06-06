import sqlite3
from config import appConfig
from db_models import *
from encoding import encoder
from utils import *

serverFormat = '| {0:19}| {1:19}| {2:19}|'
userFormat = '| {0:19}| {1:19}| {2:15}|'

class DBAccess():
    def __init__(self):
        self._conn = sqlite3.connect(appConfig['db'])
        self._c = self._conn.cursor()

    def __del__(self):
        self._conn.close()

    # Servers

    def add_server(self, server, channel):
        try:
            self._c.execute('INSERT INTO Server VALUES(?, ?, ?)',
                            (server.id, server.owner.id, channel.id))
            self._conn.commit()
        except Exception as e:
            print(e)

    def remove_server(self, serverid):
        try:
            self._c.execute('DELETE FROM Server WHERE DiscordID = ?', (serverid,))
            self._conn.commit()
        except Exception as e:
            print(e)

    def get_servers_id(self):
        self._c.execute("SELECT DiscordID FROM Server")
        return [i[0] for i in self._c.fetchall()]

    def get_servers_owners(self):
        self._c.execute("SELECT OwnerID FROM Server")
        return [i[1] for i in self._c.fetchall()]

    def get_server(self, server):
        self._c.execute("SELECT * FROM Server WHERE DiscordID=?", (server.id,))
        return DBServer(self._c.fetchone())

    def dump_servers(self):
        self._c.execute("SELECT * FROM Server")
        rows = self._c.fetchall()
        return print_array('Servers database',
                            serverFormat.format('Server ID', 'Owner ID', 'Management Channel'),
                            rows,
                            lambda x: serverFormat.format(x[0], x[1], x[2]))


    # Tournaments

    def add_tournament(self, challongeID, channel, roleId):
        try:
            self._c.execute('INSERT INTO Tournament VALUES(?, ?, ?, ?)',
                            (challongeID, channel.server.id, channel.id, roleId))
            self._conn.commit()
        except Exception as e:
            print(e)

    def remove_tournament(self, challongeID):
        try:
            self._c.execute('DELETE FROM Tournament WHERE ChallongeID=?', (challongeID,))
            self._conn.commit()
        except Exception as e:
            print(e)

    def remove_all_tournaments(self, server):
        try:
            self._c.execute('DELETE FROM Tournament WHERE ServerID=?', (server.id,))
            self._conn.commit()
        except Exception as e:
            print(e)

    def get_tournament(self, channel):
        self._c.execute("SELECT * FROM Tournament WHERE ChannelID=?", (channel.id,))
        return DBTournament(self._c.fetchone())

    # Users

    def add_user(self, user):
        try:
            self._c.execute('INSERT INTO User(DiscordID) VALUES(?)', (user.id, ))
            self._conn.commit()
        except Exception as e:
            print(e)

    def get_user(self, user):
        self._c.execute("SELECT * FROM User WHERE DiscordID=?", (user.id,))
        return DBUser(self._c.fetchone())

    def set_username(self, user, username):
        try:
            self._c.execute('UPDATE User SET ChallongeUserName=? WHERE DiscordID=?', (username, user.id))
            self._conn.commit()
        except Exception as e:
            print(e)

    def set_api_key(self, user, api_key):
        try:
            self._c.execute('UPDATE User SET ChallongeAPIKey=? WHERE DiscordID=?', (encoder.encrypt(api_key), user.id))
            self._conn.commit()
        except Exception as e:
            print(e)

    def dump_users(self):
        self._c.execute("SELECT * FROM User")
        rows = self._c.fetchall()
        print(rows)
        return print_array('Challonge users database',
                            userFormat.format('Discord ID', 'Challonge Username', 'API key set'),
                            rows,
                            lambda x: userFormat.format(x[0], x[1] if x[1] else '/', 'True' if x[2] else 'False'))

db = DBAccess()
