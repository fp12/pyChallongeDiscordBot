import json

userFormat = '{0:18}|{1:20}'
organizerFormat = '{0:18}|{1:20}|{2}'

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
    with open('challongeDB.json') as data_file:  
      self._db = json.load(data_file)

  def _save(self):
    pass

  def get_user(self, id):
    return next((ChallongeUser(x['id'], x['challonge_username']) for x in self._db if x['id'] == id), None)

  def get_organizer(self, id):
    return next((ChallongeOrganizer(x['id'], x['challonge_username'], x['challonge_apikey']) for x in self._db if x['id'] == id), None)  

  def dump(self):
    print('===========================')
    print('Challonge users database')
    print(organizerFormat.format('Discord ID', 'Challonge Username', 'Challonge API key'))
    for x in self._db:
      print(organizerFormat.format(x['id'], x['challonge_username'], x['challonge_apikey']))
    print('===========================')

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