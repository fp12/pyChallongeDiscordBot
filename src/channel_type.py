from enum import Enum
from db_access import db


class ChannelType(Enum):
    Dev = 1 << 0
    Private = 1 << 1
    Mods = 1 << 2
    Tournament = 1 << 3
    Other = 1 << 4
    NewTourney = Mods | Other
    Any = Dev | Private | Mods | Tournament | Other

    def __or__(self, other):
        return self.value | other.value

    def __and__(self, other):
        return self.value & other.value


def get_channel_type(channel):
    # if channel.server.owner.id == appConfig['devid']:
    #    return ChannelType.Dev
    if channel.is_private:
        return ChannelType.Private

    if db.get_server(channel.server).management_channel_id == channel.id:
        return ChannelType.Mods

    if db.get_tournament(channel).channel_id == channel.id:
        return ChannelType.Tournament

    return ChannelType.Other
