import json
import utils
from challonge import Account
from encoding import encoder
from enum import Enum


class UserNotFound(Exception):
    def __str__(self):
        return 'User not found'


class UserNameNotSet(Exception):
    def __str__(self):
        return 'Your Challonge username has not been set\nPlease use the command `username [name]` to set it'


class APIKeyNotSet(Exception):
    def __str__(self):
        return 'Your Challonge API key has not been set\nPlease use the command `key [apikey]` to set it'


class ChallongeAccess(Enum):
    NotRequired = 0
    Required = 1


userFormat = '| {0:19}| {1:19}|'
organizerFormat = '| {0:19}| {1:19}| {2:15}| {3:15}|'


class ChallongeUser:
    def __init__(self, discordId, challongeUserName):
        self.discordId = discordId
        self.challongeUserName = challongeUserName

    def has_username(self):
        return self.challongeUserName != ''

    def __repr__(self):
        return userFormat.format(self.discordId, self.challongeUserName)


class ChallongeOrganizer(ChallongeUser):
    def __init__(self, discordId, challongeUserName, challongeAPIKey):
        ChallongeUser.__init__(self, discordId, challongeUserName)
        self.challongeAPIKey = challongeAPIKey

    def has_key(self):
        return self.challongeAPIKey != ''

    def __repr__(self):
        return organizerFormat.format(self.discordId, self.challongeUserName, self.challongeAPIKey)


class ChallongeUsersDB:
    def __init__(self):
        with open('data/users.json') as in_file:
            self._db = json.load(in_file)
        for x in self._db:
            x.update({'account': None})

    def _save(self):
        with open('data/users.json', 'w') as out_file:
            listToSave = [{k: line[k] for k in (
                'id', 'challonge_username', 'challonge_apikey')} for line in self._db]
            json.dump(listToSave, out_file)
        self.dump()

    def get_user(self, id):
        return next((ChallongeUser(x['id'], x['challonge_username']) for x in self._db if x['id'] == id), None)

    def get_organizer(self, id):
        return next((ChallongeOrganizer(x['id'], x['challonge_username'], x['challonge_apikey']) for x in self._db if
                     x['id'] == id), None)

    def dump(self):
        return utils.print_array('Challonge users database',
                                 organizerFormat.format(
                                     'Discord ID', 'Challonge Username', 'Account in use', 'API key set'),
                                 self._db,
                                 lambda x: organizerFormat.format(x['id'],
                                                                  x['challonge_username'],
                                                                  'False' if x[
                                     'account'] is None else 'True',
                                     'False' if x['challonge_apikey'] == '' else 'True'))

    def add(self, serverOwnerId):
        found = False
        for x in self._db:
            if x['id'] == serverOwnerId:
                return
        if not found:
            newUser = {'id': serverOwnerId, 'challonge_username': '',
                       'account': None, 'challonge_apikey': ''}
            self._db.append(newUser)
        self._save()

    def set_username(self, id, username):
        found = False
        for x in self._db:
            if x['id'] == id:
                x['challonge_username'] = username
                found = True
        if not found:
            self._db.append({'id': id, 'challonge_username': username,
                             'account': None, 'challonge_apikey': ''})
        self._save()

    def set_key(self, id, key):
        found = False
        for x in self._db:
            if x['id'] == id:
                x['challonge_apikey'] = encoder.encrypt(key)
                found = True
        if not found:
            self._db.append({'id': id, 'challonge_username': '',
                             'account': None, 'challonge_apikey': encoder.encrypt(key)})
        self._save()

    def get_account(self, server):
        for x in self._db:
            if x['id'] == server.owner.id:
                if x['account'] is None:
                    if x['challonge_username'] == '':
                        raise UserNameNotSet()
                    elif x['challonge_apikey'] == '':
                        raise APIKeyNotSet()
                    else:
                        x['account'] = Account(
                            x['challonge_username'], encoder.decrypt(x['challonge_apikey']))
                        return x['account']
                else:
                    return x['account']
        raise UserNotFound()


users_db = ChallongeUsersDB()
