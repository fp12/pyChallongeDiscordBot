try:
    from database.meta import DBModel
except ImportError:
    from meta import DBModel  # debug


class DBServer(metaclass=DBModel,
               table_name='challonge_servers',
               metaattr=['server_id', 'owner_id', 'management_channel_id', 'trigger']):
    pass


class DBTournament(metaclass=DBModel,
                   table_name='challonge_tournaments',
                   metaattr=['challonge_id', 'server_id', 'channel_id', 'role_id', 'host_id']):
    pass


class DBUser(metaclass=DBModel,
             table_name='challonge_users',
             metaattr=['discord_id', 'challonge_user_name', 'api_key']):
    pass


class DBProfileEntry(metaclass=DBModel,
                     table_name='challonge_profile',
                     metaattr=['logged_at', 'scope', 'time', 'args', 'server']):
    pass


class DBModule(metaclass=DBModel,
               table_name='challonge_modules',
               metaattr=['server_id', 'module_name', 'module_def']):
    pass
