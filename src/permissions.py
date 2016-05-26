from enum import Enum
import discord

class Permissions(Enum):
  Dev = 100
  ServerOwner = 75
  Organizer = 50
  Participant = 25
  User = 0

  def __ge__(self, other):
    return self.value >= other.value


class ChannelType(Enum):
  Dev         = 1 << 0
  Private     = 1 << 1
  Mods        = 1 << 2
  Tournament  = 1 << 3
  Other       = 1 << 4
  NewTourney  = Mods | Other
  Any         = Dev | Private | Mods | Tournament | Other

  def __or__(self, other):
    return self.value | other.value

  def __and__(self, other):
    return self.value & other.value

def get_permissions(user, server):
  if user.id == '150316380992962562':
    return Permissions.Dev
  if user.id == server.owner.id:
    return Permissions.ServerOwner
  if discord.utils.get(user.roles, name='ChallongeTO') != None:
    return Permissions.Organizer
  return Permissions.User

def get_channel_type(channel):
  if channel.server.owner.id == '150316380992962562':
    return ChannelType.Dev
  if channel.is_private:
    return ChannelType.Private 
  return ChannelType.Other