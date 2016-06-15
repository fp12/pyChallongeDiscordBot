import sqlite3
from config import appConfig
from db_models import *
from utils import *

serverFormat = '| {0:19}| {1:19}| {2:19}|'
userFormat = '| {0:19}| {1:19}| {2:15}|'
profileFormat = '| {0:45}| {1:12} | {2:10} | {3:5} |'


class DBAccess():
    def __init__(self):
        self._conn = sqlite3.connect(appConfig['db'])
        self._c = self._conn.cursor()

    def __del__(self):
        self._conn.close()

    def _log_exc(self, funcname, e):
        print('DBAccess Exception in {0}: {1}'.format(funcname, e))

    # Servers

    def add_server(self, server, channel):
        try:
            self._c.execute('INSERT INTO Server VALUES(?, ?, ?)',
                            (server.id, server.owner.id, channel.id))
            self._conn.commit()
        except Exception as e:
            self._log_exc('add_server', e)

    def remove_server(self, serverid):
        try:
            self._c.execute('DELETE FROM Server WHERE DiscordID = ?', (serverid,))
            self._conn.commit()
        except Exception as e:
            self._log_exc('remove_server', e)

    def get_servers_id(self):
        self._c.execute("SELECT DiscordID FROM Server")
        return [i[0] for i in self._c.fetchall()]

    def get_servers_owners(self):
        self._c.execute("SELECT OwnerID FROM Server")
        return [i[0] for i in self._c.fetchall()]

    def get_server(self, server):
        self._c.execute("SELECT * FROM Server WHERE DiscordID=?", (server.id,))
        return DBServer(self._c.fetchone())

    def dump_servers(self):
        self._c.execute("SELECT * FROM Server")
        rows = self._c.fetchall()
        return print_array('Servers database',
                           serverFormat.format(
                               'Server ID', 'Owner ID', 'Management Channel'),
                           rows,
                           lambda x: serverFormat.format(x[0], x[1], x[2]))

    # Tournaments

    def add_tournament(self, challongeId, channel, roleId, hostId):
        try:
            self._c.execute('INSERT INTO Tournament VALUES(?, ?, ?, ?, ?)',
                            (challongeId, channel.server.id, channel.id, roleId, hostId))
            self._conn.commit()
        except Exception as e:
            self._log_exc('add_tournament', e)

    def remove_tournament(self, challongeId):
        try:
            self._c.execute(
                'DELETE FROM Tournament WHERE ChallongeID=?', (challongeId,))
            self._conn.commit()
        except Exception as e:
            self._log_exc('remove_tournament', e)

    def remove_all_tournaments(self, server):
        try:
            self._c.execute(
                'DELETE FROM Tournament WHERE ServerID=?', (server.id,))
            self._conn.commit()
        except Exception as e:
            self._log_exc('remove_all_tournaments', e)

    def get_tournament(self, channel):
        self._c.execute(
            "SELECT * FROM Tournament WHERE ChannelID=?", (channel.id,))
        return DBTournament(self._c.fetchone())

    # Users

    def add_user(self, user):
        try:
            self._c.execute(
                'INSERT INTO User(DiscordID) VALUES(?)', (user.id, ))
            self._conn.commit()
        except Exception as e:
            self._log_exc('add_user', e)

    def get_user(self, user_id):
        self._c.execute("SELECT * FROM User WHERE DiscordID=?", (user_id,))
        return DBUser(self._c.fetchone())

    def set_username(self, user, username):
        try:
            self._c.execute('INSERT OR REPLACE INTO User (DiscordID, ChallongeUserName, ChallongeAPIKey) VALUES (?, ?, (SELECT ChallongeAPIKey FROM User WHERE DiscordID = ?))', (user.id, username, user.id))
            self._conn.commit()
        except Exception as e:
            self._log_exc('set_username', e)

    def set_api_key(self, user, api_key):
        from encoding import encoder
        try:
            self._c.execute('INSERT OR REPLACE INTO User (DiscordID, ChallongeAPIKey, ChallongeUserName) VALUES (?, ?, (SELECT ChallongeUserName FROM User WHERE DiscordID = ?))', (user.id, encoder.encrypt(api_key), user.id))
            self._conn.commit()
        except Exception as e:
            self._log_exc('set_api_key', e)

    def dump_users(self):
        self._c.execute("SELECT * FROM User")
        rows = self._c.fetchall()
        return print_array('Challonge users database',
                           userFormat.format(
                               'Discord ID', 'Challonge Username', 'API key set'),
                           rows,
                           lambda x: userFormat.format(x[0], x[1] if x[1] else '/', 'True' if x[2] else 'False'))

    # Profiling

    def add_profile_log(self, logged_at, scope, time, name, args, server):
        try:
            self._c.execute('INSERT INTO Profile VALUES(?, ?, ?, ?, ?, ?)',
                            (logged_at, scope.name, time, name, args, server))
            self._conn.commit()
        except Exception as e:
            self._log_exc('add_profile_log', e)

    def dump_profile(self):
        self._c.execute('SELECT Name, avg(Time) AS AVG, total(Time) as Total, count(Time) FROM Profile GROUP BY Name ORDER BY AVG DESC')
        rows = self._c.fetchall()
        return print_array('Profiling stats',
                           profileFormat.format('Name', 'Average (ms)', 'Total (ms)', 'Count'),
                           rows,
                           lambda x: profileFormat.format(x[0], round(x[1], 2), round(x[2], 2), x[3]))


db = DBAccess()
