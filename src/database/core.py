from config import app_config
from log import log_db
from database.models import DBServer, DBTournament, DBUser, DBModule
if 'heroku' in app_config:
    import psycopg2
    from urllib.parse import urlparse
else:
    import sqlite3


def to_list(x):
    return x if isinstance(x, list) else [x]


class DBAccess():
    def __init__(self):
        if 'heroku' in app_config:
            url = urlparse(app_config['database'])
            self._conn = psycopg2.connect(database=url.path[1:], user=url.username, password=url.password, host=url.hostname, port=url.port)
            self._token = '%s'
        else:
            self._conn = sqlite3.connect(app_config['database'])
            self._token = '?'
        self._c = self._conn.cursor()

    def __del__(self):
        self._conn.close()

    def _insert(self, table, columns, values):
        columns = to_list(columns) if columns else None
        if not columns or len(columns) == len(values):
            cols = ' ({0})'.format(', '.join(columns)) if columns else ''
            request = 'INSERT INTO {0}{1} VALUES ({2});'.format(str(table), cols, ', '.join([self._token] * len(values)))
            log_db.debug((request, values))
            try:
                self._c.execute(request, values)
                self._conn.commit()
            except psycopg2.Error as e:
                log_db.error(e.pgerror)
        else:
            log_db.error('[_insert] mismatch in numbers: {0} columns / {1} values'.format(str(columns), str(values)))

    def _insert_or_replace(self, table, replace_column, replace_value, where_column, where_value):
        request = ''
        args = ()
        if self._token == '%s':  # postgresql
            request = 'INSERT INTO {0}({1}, {2}) VALUES ({3}, {3}) ON CONFLICT ({1}) DO UPDATE SET {2} = {3};'
            request = request.format(str(table), where_column, replace_column, self._token)
            args = (where_value, replace_value, replace_value)
        else:  # sqlite
            # get non mentionned colums
            cols = table.columns[:]  # copy
            cols.remove(replace_column)
            cols.remove(where_column)

            # build select clause string and arguments
            select_clause_str = ['(SELECT {0} FROM {1} WHERE {2} = {3})'.format(x, str(table), where_column, self._token) for x in cols]

            # build request
            columns_names = ', '.join(cols)
            selects = ', '.join(select_clause_str)
            request = 'INSERT OR REPLACE INTO {0} ({1}, {2}, {3}) VALUES ({4}, {4}, {5});'
            request = request.format(str(table), where_column, replace_column, columns_names, self._token, selects)
            args = (where_value, replace_value) + (where_value,) * len(cols)

        log_db.debug((request, args))
        try:
            self._c.execute(request, args)
            self._conn.commit()
        except psycopg2.Error as e:
            log_db.error(e.pgerror)

    def _delete(self, table, column, value):
        request = 'DELETE FROM {0} WHERE {1} = {2};'.format(str(table), column, self._token)
        log_db.debug((request, value))
        self._c.execute(request, (value,))
        self._conn.commit()

    def _select(self, table, columns, where_column=None, where_value=None):
        request = 'SELECT {0} FROM {1}'.format(', '.join(to_list(columns)), str(table))
        try:
            if where_column:
                request = request + ' WHERE {0} = {1};'.format(where_column, self._token)
                log_db.debug((request, where_value))
                self._c.execute(request, (where_value,))
            else:
                request += ';'
                log_db.debug(request)
                self._c.execute(request)
        except psycopg2.Error as e:
            log_db.error(e.pgerror)
            return []
        else:
            return self._c

    def _update(self, table, set_column, set_value, where_column, where_value):
        request = 'UPDATE {0} SET {1} = {3} WHERE {2} = {3};'.format(str(table), set_column, where_column, self._token)
        log_db.debug(request, (set_value, where_value))
        try:
            self._c.execute(request, (set_value, where_value))
            self._conn.commit()
        except psycopg2.Error as e:
            log_db.error(e.pgerror)

    # Servers

    def add_server(self, server, channel):
        self._insert(table=DBServer, columns=DBServer.columns, values=(server.id, server.owner.id, channel.id, None))

    def remove_server(self, server_id):
        self._delete(table=DBServer, column=DBServer.server_id, value=server_id)
        self._delete(table=DBTournament, column=DBTournament.server_id, value=server_id)
        self._delete(table=DBModule, column=DBModule.server_id, value=server_id)

    def get_servers_id(self):
        cur = self._select(table=DBServer, columns=DBServer.server_id)
        return [i[0] for i in cur.fetchall()] if cur else []

    def get_servers_owners(self):
        cur = self._select(table=DBServer, columns=DBServer.owner_id)
        return [i[0] for i in cur.fetchall()] if cur else []

    def get_server(self, server):
        cur = self._select(table=DBServer, columns='*', where_column=DBServer.server_id, where_value=server.id)
        return DBServer(cur.fetchone() if cur else None)

    def set_server_trigger(self, server, trigger):
        self._update(table=DBServer,
                     set_column=DBServer.trigger, set_value=trigger,
                     where_column=DBServer.server_id, where_value=server.id)

    def get_servers(self):
        cur = self._select(table=DBServer, columns='*')
        return [DBServer(x) for x in cur]

    # Tournaments

    def add_tournament(self, challonge_id, channel, role_id, host_id):
        self._insert(table=DBTournament, columns=DBTournament.columns, values=(challonge_id, channel.server.id, channel.id, role_id, host_id))

    def remove_tournament(self, challonge_id):
        self._delete(table=DBTournament, column=DBTournament.challonge_id, value=challonge_id)

    def remove_all_tournaments(self, server):
        self._delete(table=DBTournament, column=DBTournament.server_id, value=server.id)

    def get_tournament(self, channel):
        cur = self._select(table=DBTournament, columns='*', where_column=DBTournament.channel_id, where_value=channel.id)
        return DBTournament(cur.fetchone() if cur else None)

    def get_tournaments(self, server_id):
        cur = self._select(table=DBTournament, columns='*', where_column=DBTournament.server_id, where_value=server_id)
        for x in cur:
            yield DBTournament(x)

    # Users

    def add_user(self, user):
        self._insert(table=DBUser, columns=DBUser.discord_id, values=(user.id,))

    def get_user(self, user_id):
        cur = self._select(table=DBUser, columns='*', where_column=DBUser.discord_id, where_value=user_id)
        return DBUser(cur.fetchone() if cur else None)

    def set_username(self, user, username):
        self._insert_or_replace(table=DBUser,
                                replace_column=DBUser.challonge_user_name, replace_value=username,
                                where_column=DBUser.discord_id, where_value=user.id)

    def set_api_key(self, user, api_key):
        from encoding import encoder
        self._insert_or_replace(table=DBUser,
                                replace_column=DBUser.api_key, replace_value=encoder.encrypt(api_key),
                                where_column=DBUser.discord_id, where_value=user.id)

    def get_users(self):
        cur = self._select(table=DBUser, columns='*')
        return [DBUser(x) for x in cur]

    # Modules

    def add_module(self, server_id, name, module_def):
        self._insert(table=DBModule, columns=DBModule.columns, values=(server_id, name, module_def))

    def get_modules(self):
        cur = self._select(table=DBModule, columns='*')
        for x in cur:
            yield DBModule(x)


db = DBAccess()
