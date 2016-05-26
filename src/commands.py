import asyncio
from permissions import Permissions, ChannelType, get_permissions, get_channel_type
import discord
import actions
import text

commandTrigger = '>>>'


class Attributes:
    def __init__(self, **kwargs):
        self.minPermissions = kwargs.get('minPermissions', Permissions.User)
        self.channelRestrictions = kwargs.get('channelRestrictions', ChannelType.Other)


class Command:
    def __init__(self, name, cb, attributes=None):
        self.name = name
        self.cb = cb
        self.attributes = attributes
        self.aliases = None

    def addParams(self, *args):
        self.reqParams = args
        return self

    def addOptionalParams(self, *args):
        self.optParams = args
        return self

    def addAliases(self, *args):
        self.aliases = args
        return self

    async def validateContext(self, client, message):
        split = message.content.split()
        authorPerms = get_permissions(message.author, message.server)
        if authorPerms >= self.attributes.minPermissions:
            channelType = get_channel_type(message.channel)
            if channelType == ChannelType.Dev or channelType & self.attributes.channelRestrictions:
                reqParamsExpected = 0 if self.reqParams == None else len(self.reqParams)
                optParamsExpected = 0 if self.optParams == None else len(self.optParams)
                givenParams = len(split) - 2
                if givenParams >= reqParamsExpected:
                    return True
                else:
                    await client.send_message(message.channel,
                                              text.ValidateCommandContext_BadParameters.format(split[1],
                                                                                               len(self.reqParams),
                                                                                               len(split) - 2))
            else:
                await client.send_message(message.channel, text.ValidateCommandContext_BadChannel.format(split[1]))
        else:
            await client.send_message(message.channel, text.ValidateCommandContext_BadPrivileges.format(split[1]))
        return False

    def validateName(self, name):
        if self.name == name:
            return True
        elif self.aliases != None:
            return name in self.aliases
        return False

    async def execute(self, client, message):
        split = message.content.split()
        if self.cb != None:
            if self.reqParams != None:
                kwargs = {}
                offset = 2  # trigger + command
                for count, x in enumerate(self.reqParams):
                    kwargs[x] = split[count + offset]
                offset = offset + len(self.reqParams)
                for count, x in enumerate(self.optParams):
                    if count + offset < len(split):
                        kwargs[x] = split[count + offset]
                await self.cb(client, message, **kwargs)
            else:
                await self.cb(client, message)


class CommandsHandler:
    def __init__(self):
        self.commands = []

    def add(self, command):
        self.commands.append(command)

    def _find(self, name):
        for cmd in self.commands:
            if cmd.validateName(name):
                return cmd
        return None

    def validateCommand(self, client, message):
        split = message.content.split()
        if split[0] == commandTrigger or client.user in message.mentions:
            return self._find(split[1])
        return None


handler = CommandsHandler()

attributes = Attributes(minPermissions=Permissions.Dev, channelRestrictions=ChannelType.Any)
handler.add(Command('shutdown', actions.shutdown, attributes).addAliases('exit', 'out'))

attributes = Attributes(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Private)
handler.add(Command('key', actions.key, attributes).addParams('key'))

attributes = Attributes(minPermissions=Permissions.ServerOwner, channelRestrictions=ChannelType.Mods)
handler.add(Command('organization', actions.organization, attributes).addParams('organization'))
handler.add(Command('promote', actions.promote, attributes).addParams('member'))

attributes = Attributes(minPermissions=Permissions.Organizer, channelRestrictions=ChannelType.NewTourney)
handler.add(Command('create', actions.create, attributes).addParams('name').addAliases('new'))

attributes = Attributes(minPermissions=Permissions.Organizer, channelRestrictions=ChannelType.Tournament)
handler.add(Command('shuffleseeds', actions.shuffleseeds, attributes).addAliases('shuffle'))
handler.add(Command('start', actions.start, attributes).addAliases('launch'))
handler.add(Command('reset', actions.reset, attributes))
handler.add(Command('checkin_start', actions.checkin_start, attributes))
handler.add(Command('checkin_stop', actions.checkin_stop, attributes))
handler.add(Command('finalize', actions.finalize, attributes))
handler.add(Command('reopen', actions.reopen, attributes).addParams('player1', 'player2'))

attributes = Attributes(minPermissions=Permissions.Participant, channelRestrictions=ChannelType.Tournament)
handler.add(Command('update', actions.update, attributes).addParams('score'))
handler.add(Command('forfeit', actions.forfeit, attributes))
handler.add(Command('next', actions.next, attributes))
handler.add(Command('checkin', actions.checkin, attributes))

attributes = Attributes(minPermissions=Permissions.User, channelRestrictions=ChannelType.Any)
handler.add(Command('username', actions.username, attributes).addParams('username'))
handler.add(Command('help', actions.help, attributes).addOptionalParams('command'))

attributes = Attributes(minPermissions=Permissions.User, channelRestrictions=ChannelType.Tournament)
handler.add(Command('join', actions.join, attributes))
