import json
import utils


serverFormat = '| {0:19}| {1:19}| {2:19}| {3:13}|'


class ServersDB:
    def __init__(self):
        with open('data/servers.json') as in_file:
            self._db = json.load(in_file)

    def _save(self):
        with open('data/servers.json', 'w') as out_file:
            json.dump(self._db, out_file)        
        self.dump()

    def dump(self):
        utils.print_array(
            'Servers database', 
            serverFormat.format('Server ID', 'Management Channel', 'Organization', 'Tournaments'), 
            self._db, 
            lambda x: serverFormat.format(  x['id'], 
                                            x['managementChannel'], 
                                            x['organization'], 
                                            'None' if len(x['tournaments']) == 0 else 'Some tournaments'))

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

    def get_management_channel(self, server):
        for x in self._db:
            if x['id'] == server.id:
                return x['managementChannel']
        return 0

servers_db = ServersDB()
