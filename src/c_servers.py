import json

serverFormat = ' {0:19}| {1:19}| {2:19}| {3}'

class ServersDB:
    def __init__(self):
        with open('data/servers.json') as in_file:
            self._db = json.load(in_file)

    def _save(self):
        with open('data/servers.json', 'w') as out_file:
            json.dump(self._db, out_file)

    def dump(self):
        print('===========================')
        print('Servers database')
        print(serverFormat.format('Server ID', 'Management Channel', 'Organization', 'Tournaments'))
        for x in self._db:
            print(serverFormat.format(x['id'], x['managementChannel'], x['organization'], 'to come'))
        print('===========================')

    def add(self, server, channel):
        found = False
        for x in self._db:
            if x['id'] == server.id:
                x['managementChannel'] = channel.id
                found = True
        if found == False:
            newServer = {'id':server.id, 'managementChannel':channel.id, 'organization':'', 'tournaments':[]}
            self._db.append(newServer)
        self._save()
        self.dump()


servers_db = ServersDB()
servers_db.dump()
