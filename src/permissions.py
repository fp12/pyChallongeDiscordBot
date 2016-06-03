from enum import Enum
from const import *
import discord
from config import appConfig


class Permissions(Enum):
    Dev = 5
    TestBots = 4
    ServerOwner = 3
    Organizer = 2
    Participant = 1
    User = 0

    def __ge__(self, other):
        return self.value >= other.value


def get_permissions(user, server):
    if user.id == appConfig['devid']:
        return Permissions.Dev
    if user.id == server.owner.id:
        return Permissions.ServerOwner
    if False:  # has a tournament role on this server
        return Permissions.Participant
    if discord.utils.get(user.roles, name=C_RoleName) is not None:
        return Permissions.Organizer
    return Permissions.User
