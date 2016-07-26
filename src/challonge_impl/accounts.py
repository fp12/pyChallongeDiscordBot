import asyncio
from enum import Enum
from challonge import Account, ChallongeException

from encoding import encoder
from database.core import db


class ChallongeAccess(Enum):
    NotRequired = 0
    RequiredForAuthor = 1
    RequiredForHost = 2


class TournamentStateConstraint(Enum):
    Pending = 1 << 0
    Underway = 1 << 1
    AwaitingReview = 1 << 2
    Complete = 1 << 3
    NotComplete = Pending | Underway
    Any = Pending | Underway | AwaitingReview | Complete

    def __or__(self, other):
        return self.value | other.value

    def __and__(self, other):
        return self.value & other.value


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
        return None, UserNotFound()
    elif not user.user_name:
        return None, UserNameNotSet()
    elif not user.api_key:
        return None, APIKeyNotSet()

    for x in challonge_accounts:
        if x['user_id'] == user.discord_id:
            return x['account'], None

    newAccount = Account(user.user_name, encoder.decrypt(user.api_key))
    try:
        is_valid = await newAccount.is_valid
    except ChallongeException:
        return None, InvalidCredentials()
    else:
        newEntry = {'user_id': user.discord_id, 'account': newAccount}
        challonge_accounts.append(newEntry)
        return newEntry['account'], None
