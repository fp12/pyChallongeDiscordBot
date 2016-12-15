from enum import Enum

from const import C_RoleName
from config import app_config
from database.core import db


class Permissions(Enum):
    Dev = 5
    TestBots = 4
    ServerOwner = 3
    Organizer = 2
    Participant = 1
    User = 0

    def __ge__(self, other):
        return self.value >= other.value

    def __lt__(self, other):
        return self.value < other.value


def get_permissions(user, channel):
    if user.id == app_config['devid']:
        return Permissions.Dev

    if user.id in app_config['whitelistedbots']:
        return Permissions.TestBots

    if not channel.is_private and user.id == channel.server.owner.id:
        return Permissions.ServerOwner

    if channel.is_private and user.id in db.get_servers_owners():
        return Permissions.ServerOwner

    if not channel.is_private:
        member_in_server = [m for m in channel.server.members if m.id == user.id][0]
        if len([r for r in member_in_server.roles if r.name == C_RoleName]) > 0:
            return Permissions.Organizer

    if not channel.is_private:
        print('get_permissions')
        tournament = db.get_tournament(channel)
        if tournament.role_id:
            member_in_server = [m for m in channel.server.members if m.id == user.id][0]
            if len([r for r in member_in_server.roles if r.id == tournament.role_id]) > 0:
                return Permissions.Participant

    return Permissions.User
