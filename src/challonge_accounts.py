from db_access import db
from challonge import Account, ChallongeException
from enum import Enum
from encoding import encoder
import asyncio

class ChallongeAccess(Enum):
    NotRequired = 0
    RequiredForAuthor = 1
    RequiredForHost = 2


class UserNotFound(Exception):
    def __str__(self):
        return '❌ User not found'


class UserNameNotSet(Exception):
    def __str__(self):
        return '❌ Your Challonge username has not been set. Please use the command `username [name]` to set it'


class APIKeyNotSet(Exception):
    def __str__(self):
        return '❌ Your Challonge API key has not been set. Please use the command `key [apikey]` to set it'


class InvalidCredentials(Exception):
    def __str__(self):
        return '❌ Your Challonge credentials are not valid. Please set them again via the `username` and `key` commands'


challonge_accounts = []


async def get(user_id):
    user = db.get_user(user_id)
    if not user.discord_id:
        raise UserNotFound()
    elif not user.user_name:
        raise UserNameNotSet()
    elif not user.api_key:
        raise APIKeyNotSet()

    for x in challonge_accounts:
        if x['user_id'] == user.discord_id:
            return x['account']
    
    newAccount = Account(user.user_name, encoder.decrypt(user.api_key))
    try:
        is_valid = await newAccount.is_valid
    except ChallongeException:
        raise InvalidCredentials()
    else:
        newEntry = {'user_id': user.discord_id, 'account': newAccount}
        challonge_accounts.append(newEntry)
        return newEntry['account']
