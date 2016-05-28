from enum import Enum
from const import *



class Permissions(Enum):
    Dev = 100
    ServerOwner = 75
    Organizer = 50
    Participant = 25
    User = 0

    def __ge__(self, other):
        return self.value >= other.value



def get_permissions(user, server):
    if user.id == '150316380992962562':
        return Permissions.Organizer
    if user.id == server.owner.id:
        return Permissions.ServerOwner
    if False: # has a tournament role on this server
        return Permissions.Participant
    if discord.utils.get(user.roles, name=C_RoleName) != None:
        return Permissions.Organizer
    return Permissions.User