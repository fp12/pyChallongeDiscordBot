from database.meta import DBModel


class DBServer(metaclass=DBModel, metaattr=['server_id', 'owner_id', 'management_channel_id', 'trigger']):
    pass


class DBTournament(metaclass=DBModel, metaattr=['challonge_id', 'server_id', 'channel_id', 'role_id', 'host_id']):
    pass


class DBUser(metaclass=DBModel, metaattr=['discord_id', 'user_name', 'api_key']):
    pass


class DBProfileEntry(metaclass=DBModel, metaattr=['logget_at', 'scope', 'time', 'args', 'server']):
    pass


class DBModule(metaclass=DBModel, metaattr=['server_id', 'module_name', 'module_def']):
    pass
