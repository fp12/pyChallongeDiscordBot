import asyncio
from permissions import Permissions, ChannelType, get_permissions, get_channel_type
import discord
from text import *

commandTrigger = '>>>'
commandFormat = ' {0:15}| {1:16}| {2:13}| {3:15}| {4:20}| {5:20}'

class Attributes:
    def __init__(self, **kwargs):
        self.minPermissions = kwargs.get('minPermissions', Permissions.User)
        self.channelRestrictions = kwargs.get('channelRestrictions', ChannelType.Other)


class Command:
    def __init__(self, name, cb, attributes=None):
        self.name = name
        self.cb = cb
        self.attributes = attributes
        self.aliases = []
        self.reqParams = []
        self.optParams = []

    def add_required_params(self, *args):
        self.reqParams = args
        return self

    def add_optional_params(self, *args):
        self.optParams = args
        return self

    def add_aliases(self, *args):
        self.aliases = args
        return self

    async def validate_context(self, client, message):
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
                                              T_ValidateCommandContext_BadParameters.format(split[1],
                                                                                            len(self.reqParams),
                                                                                            len(split) - 2))
            else:
                await client.send_message(message.channel, T_ValidateCommandContext_BadChannel.format(split[1]))
        else:
            await client.send_message(message.channel, T_ValidateCommandContext_BadPrivileges.format(split[1]))
        return False

    def validate_name(self, name):
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
        self._commands = []

    def _add(self, command):
        self._commands.append(command)
        return command

    def _find(self, name):
        for command in self._commands:
            if command.validate_name(name):
                return command
        return None

    def validate_command(self, client, message):
        split = message.content.split()
        if split[0] == commandTrigger or client.user in message.mentions:
            return self._find(split[1])
        return None

    def register(self, **kwargs):
        def decorator(func):
            async def wrapper(client, message, **kwArgs):
                await func(client, message, **kwArgs)
            return self._add(Command(func.__name__, wrapper, Attributes(**kwargs)))
        return decorator

    def dump(self):
        print('===========================')
        print('Commands registered')
        print(commandFormat.format('Name', 'Min Permissions', 'Channel Type', 'Aliases', 'Required Args', 'Optional Args'))
        for c in self._commands:
            print(commandFormat.format(c.name, 
                c.attributes.minPermissions.name, 
                c.attributes.channelRestrictions.name, 
                '-' if len(c.aliases) == 0 else '/'.join(c.aliases),
                '-' if len(c.reqParams) == 0 else '/'.join(c.reqParams), 
                '-' if len(c.optParams) == 0 else '/'.join(c.optParams)))
        print('===========================')


commands = CommandsHandler()


def required_args(*args):
    def decorator(func):
        return func.add_required_params(*args)
    return decorator


def optional_args(*args):
    def decorator(func):
        return func.add_optional_params(*args)
    return decorator


def aliases(*args):
    def decorator(func):
        return func.add_aliases(*args)
    return decorator