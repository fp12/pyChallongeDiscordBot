class DBServer():
    def __init__(self, tup):
        if tup:
            self._tup = tup
        else:
            self._tup = (None, None, None, None)

    @property
    def server_id(self):
        return self._tup[0]

    @property
    def owner_id(self):
        return self._tup[1]

    @property
    def management_channel_id(self):
        return self._tup[2]

    @property
    def trigger(self):
        return self._tup[3]


class DBTournament():
    def __init__(self, tup):
        if tup:
            self._tup = tup
        else:
            self._tup = (None, None, None, None, None)

    @property
    def challonge_id(self):
        return self._tup[0]

    @property
    def server_id(self):
        return self._tup[1]

    @property
    def channel_id(self):
        return self._tup[2]

    @property
    def role_id(self):
        return self._tup[3]

    @property
    def host_id(self):
        return self._tup[4]


class DBUser():
    def __init__(self, tup):
        if tup:
            self._tup = tup
        else:
            self._tup = (None, None, None)

    @property
    def discord_id(self):
        return self._tup[0]

    @property
    def user_name(self):
        return self._tup[1]

    @property
    def api_key(self):
        return self._tup[2]


class DBProfileEntry():
    def __init__(self, tup):
        if tup:
            self._tup = tup
        else:
            self._tup = (None, None, None, None, None)

    @property
    def logget_at(self):
        return self._tup[0]

    @property
    def scope(self):
        return self._tup[1]

    @property
    def time(self):
        return self._tup[2]

    @property
    def args(self):
        return self._tup[3]

    @property
    def server(self):
        return self._tup[4]
