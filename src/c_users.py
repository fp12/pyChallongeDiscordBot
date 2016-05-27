import json
import utils

userFormat = '| {0:19}| {1:19}|'
organizerFormat = '| {0:19}| {1:19}| {2:30}|'


class ChallongeUser:
    def __init__(self, discordId, challongeUserName):
        self.DiscordId = discordId
        self.ChallongeUserName = challongeUserName

    def has_username(self):
        return self.ChallongeUserName != ''

    def __repr__(self):
        return userFormat.format(self.DiscordId, self.ChallongeUserName)


class ChallongeOrganizer(ChallongeUser):
    def __init__(self, discordId, challongeUserName, challongeAPIKey):
        ChallongeUser.__init__(self, discordId, challongeUserName)
        self.ChallongeAPIKey = challongeAPIKey

    def has_key(self):
        return self.ChallongeAPIKey != ''

    def __repr__(self):
        return organizerFormat.format(self.DiscordId, self.ChallongeUserName, self.ChallongeAPIKey)


class ChallongeUsersDB:
    def __init__(self):
        with open('data/users.json') as in_file:
            self._db = json.load(in_file)

    def _save(self):
        with open('data/users.json', 'w') as out_file:
            json.dump(self._db, out_file)
        self.dump()

    def get_user(self, id):
        return next((ChallongeUser(x['id'], x['challonge_username']) for x in self._db if x['id'] == id), None)

    def get_organizer(self, id):
        return next((ChallongeOrganizer(x['id'], x['challonge_username'], x['challonge_apikey']) for x in self._db if
                     x['id'] == id), None)

    def dump(self):
        utils.print_array(
            'Challonge users database', 
            organizerFormat.format('Discord ID', 'Challonge Username', 'Challonge API key'), 
            self._db, 
            lambda x: organizerFormat.format(x['id'], x['challonge_username'], x['challonge_apikey']))

    def add(self, serverOwnerId):
        found = False
        for x in self._db:
            if x['id'] == serverOwnerId:
                return
        if found == False:
            newUser = {'id':serverOwnerId, 'challonge_username': '', 'challonge_apikey':''}
            self._db.append(newUser)
        self._save()

    def set_username(self, id, username):
        found = False
        for x in self._db:
            if x['id'] == id:
                x['challonge_username'] = username
                found = True
        if found == False:
            self._db.append(id=id, challonge_username=username)
        self._save()

    def set_key(self, id, key):
        found = False
        for x in self._db:
            if x['id'] == id:
                x['challonge_apikey'] = key
                found = True
        if found == False:
            self._db.append(id=id, challonge_apikey=keychallonge_apikey)
        self._save()


users_db = ChallongeUsersDB()
