from enum import Enum


class ChannelType(Enum):
    Dev = 1 << 0
    Private = 1 << 1
    Mods = 1 << 2
    Tournament = 1 << 3
    Other = 1 << 4
    Any = Dev | Private | Mods | Tournament | Other

    def __or__(self, other):
        return self.value | other.value

    def __and__(self, other):
        return self.value & other.value


def get_channel_type(channel, db_server, db_tournament):
    # if channel.server.owner.id == app_config['devid']:
    #    return ChannelType.Dev
    if channel.is_private:
        return ChannelType.Private

    if db_server.management_channel_id == channel.id:
        return ChannelType.Mods

    if db_tournament.channel_id == channel.id:
        return ChannelType.Tournament

    return ChannelType.Other
