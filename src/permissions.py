from enum import Enum
from const import *
import discord
from config import appConfig
from c_servers import servers_db

class Permissions(Enum):
    Dev = 5
    TestBots = 4
    ServerOwner = 3
    Organizer = 2
    Participant = 1
    User = 0

    def __ge__(self, other):
        return self.value >= other.value


def get_permissions(user, channel):
    if user.id == appConfig['devid']:
        return Permissions.Dev

    if user.id in appConfig['whitelistedbots']:
        return Permissions.TestBots

    if not channel.is_private and user.id == channel.server.owner.id:
        return Permissions.ServerOwner

    if channel.is_private and user.id in [s['ownerid'] for s in servers_db]:
        return Permissions.ServerOwner

    if not channel.is_private:
        memberInServer = [m for m in channel.server.members if m.id == user.id][0]
        if len([r for r in memberInServer.roles if r.name == C_RoleName ]) > 0:
            return Permissions.Organizer

    if not channel.is_private:
        alltourneysInServer = [s['tournaments'] for s in servers_db if s['id'] == channel.server.id and s['tournaments']]
        if alltourneysInServer:
            tourneyRole = [t['role'] for t in alltourneysInServer if t['channel'] == channel.id]
            if len(tourneyRole) == 1:
                memberInServer = [m for m in channel.server.members if m.id == user.id][0]
                if len([r for r in memberInServer.roles if r.id == tourneyRole]) > 0:
                    return Permissions.Participant
    
    return Permissions.User
