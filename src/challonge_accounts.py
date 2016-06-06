from db_access import db
from challonge import Account
from enum import Enum
from encoding import encoder

class ChallongeAccess(Enum):
    NotRequired = 0
    Required = 1
    
class UserNotFound(Exception):
    def __str__(self):
        return 'User not found'

class UserNameNotSet(Exception):
    def __str__(self):
        return 'Your Challonge username has not been set\nPlease use the command `username [name]` to set it'

class APIKeyNotSet(Exception):
    def __str__(self):
        return 'Your Challonge API key has not been set\nPlease use the command `key [apikey]` to set it'


challonge_accounts = []

def get(server):
    user = db.get_user(server.owner)
    if user.discord_id == 0:
        raise UserNotFound()
    elif user.user_name == '':
        raise UserNameNotSet()
    elif user.api_key == '':
        raise APIKeyNotSet()

    for x in challonge_accounts:
        if x['user_id'] == user.discord_id:
            return x['account']
    newEntry = {'user_id':user.discord_id, 'account':Account(user.user_name, encoder.decrypt(user.api_key))}
    challonge_accounts.append(newEntry)
    return newEntry['account']
    