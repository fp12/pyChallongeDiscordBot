import json
import utils
from enum import Enum



serverFormat = '| {0:19}| {1:19}| {2:19}| {3:13}|'


class ServersDB:
    def __init__(self):
        with open('data/servers.json') as in_file:
            self._db = json.load(in_file)

    def __contains__(self, serverId):
        for x in self._db:
            if x['id'] == serverId:
                return True
        return False

    def __getitem__(self, *args):
        return self._db.__getitem__(*args)

    def __delitem__(self, *args):
        self._db.__delitem__(*args)

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
                                            'None' if x['organization'] == None or x['organization'] == '' else x['organization'], 
                                            'None' if len(x['tournaments']) == 0 else 'Some tournaments'))

    def add(self, server, channel):
        found = False
        for x in self._db:
            if x['id'] == server.id:
                x['managementChannel'] = channel.id
                found = True
                break

        if found == False:
            newServer = {'id':server.id, 'managementChannel':channel.id, 'organization':'', 'tournaments':[]}
            self._db.append(newServer)
        self._save()

    def edit(self, server, **kwargs):
        for x in self._db:
            if x['id'] == server.id:
                x['organization'] = kwargs.get('organization')
                if kwargs.get('tournaments', '') != None:
                    pass #TODO
                self._save()
                return
        print('Attempted to edit db for [Server \'{0.name}\' ({0.id})] but it was not found'.format(server))

    def remove(self, serverid):
        for x in self._db:
            if x['id'] == serverid:
                self._db.remove(x)
                break
        self._save()

    def get_management_channel(self, server):
        for x in self._db:
            if x['id'] == server.id:
                return x['managementChannel']
        return 0

servers_db = ServersDB()


class ChannelType(Enum):
    Dev = 1 << 0
    Private = 1 << 1
    Mods = 1 << 2
    Tournament = 1 << 3
    Other = 1 << 4
    NewTourney = Mods | Other
    Any = Dev | Private | Mods | Tournament | Other
    
    def __or__(self, other):
        return self.value | other.value
    
    def __and__(self, other):
        return self.value & other.value


def get_channel_type(channel):
    #if channel.server.owner.id == '150316380992962562':
    #    return ChannelType.Dev
    if channel.is_private:
        return ChannelType.Private
    if len([s for s in servers_db if s['id'] == channel.server.id and s['managementChannel'] == channel.id]) == 1:
        return ChannelType.Mods
    if len([s for s in servers_db if s['id'] == channel.server.id and False]) == 1: # TODO
        return ChannelType.Tournament
    return ChannelType.Other
