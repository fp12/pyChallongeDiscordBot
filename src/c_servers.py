import json
import utils
from enum import Enum


serverFormatNoTourney = '| {0:19}| {1:19}| {2:19}| {3:^55}|'
serverFormatWTourney = '| {0:19}| {1:19}| {2:19}| {3:19}| {4:19}| {5:13}|'


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

    def _print_line(self, x):
        lines = []
        if len(x['tournaments']) == 0:
            lines.append(serverFormatNoTourney.format(x['id'],
                                                      x['managementChannel'],
                                                      '' if x['organization'] is None or x[
                                                          'organization'] == '' else x['organization'],
                                                      'None'))
        else:
            for i, t in enumerate(x['tournaments']):
                lines.append(serverFormatWTourney.format(x['id'] if i == 0 else '',
                                                         x['managementChannel'] if i == 0 else '',
                                                         x['organization'] if i == 0 and x[
                                                             'organization'] is not None and x['organization'] != '' else '',
                                                         x['tournaments'][
                                                             i]['channel'],
                                                         x['tournaments'][
                                                             i]['role'],
                                                         x['tournaments'][i]['challongeid']))
        return '\n'.join(lines)

    def dump(self):
        return utils.print_array('Servers database',
                                 serverFormatWTourney.format(
                                     'Server ID', 'Management Channel', 'Organization', 'T. Channel', 'T. Role', 'T. Challonge'),
                                 self._db,
                                 self._print_line)

    def add_server(self, server, channel):
        found = False
        for x in self._db:
            if x['id'] == server.id:
                x['managementChannel'] = channel.id
                found = True
                break

        if not found:
            newServer = {'id': server.id, 'managementChannel': channel.id,
                         'organization': '', 'tournaments': []}
            self._db.append(newServer)
        self._save()

    def remove_server(self, serverid):
        for x in self._db:
            if x['id'] == serverid:
                self._db.remove(x)
                break
        self._save()

    def edit(self, server, **kwargs):
        for x in self._db:
            if x['id'] == server.id:
                x['organization'] = kwargs.get('organization')
                self._save()
                return
        print(
            'Attempted to edit server \'{0.name}\' ({0.id}) but it was not found in db'.format(server))

    def add_tournament(self, server, **kwargs):
        for x in self._db:
            if x['id'] == server.id:
                x['tournaments'].append(kwargs)
                self._save()
                return
        print(
            'Attempted to add a tournament on server \'{0.name}\' ({0.id}) but it was not found in db'.format(server))

    def remove_tournament(self, server, tournament):
        for x in self._db:
            if x['id'] == server.id:
                for y in x['tournaments']:
                    if y['challongeid'] == tournament:
                        x['tournaments'].remove(y)
                        self._save()
                        return

    def get_management_channel(self, server):
        for x in self._db:
            if x['id'] == server.id:
                return x['managementChannel']
        return 0

    def _get_tournament_info(self, channel, info):
        result = [y[info] for x in self._db if x['id'] == channel.server.id for y in x[
            'tournaments'] if y['channel'] == channel.id]
        if len(result) == 0:
            print('No results for get_tournament_id')
        elif len(result) > 1:
            print('Too many results for get_tournament_id')
        else:
            return result[0]

    def get_tournament_id(self, channel):
        return self._get_tournament_info(channel, 'challongeid')

    def get_tournament_role(self, channel):
        return self._get_tournament_info(channel, 'role')


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
    # if channel.server.owner.id == appConfig['devid']:
    #    return ChannelType.Dev
    if channel.is_private:
        return ChannelType.Private
    if len([s for s in servers_db if s['id'] == channel.server.id and s['managementChannel'] == channel.id]) == 1:
        return ChannelType.Mods
    if len([t['challongeid'] for s in servers_db if s['id'] == channel.server.id for t in s['tournaments'] if t['channel'] == channel.id]) == 1:
        return ChannelType.Tournament
    return ChannelType.Other
