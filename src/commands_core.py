import asyncio
from permissions import Permissions, get_permissions
from c_servers import ChannelType, get_channel_type
import discord
from const import *
import utils

commandTrigger = '>>>'
commandFormat = '| {0:15}| {1:16}| {2:13}| {3:15}| {4:20}| {5:20}|'


class ContextValidationError_MissingParameters(Exception):
    def __init__(self, req, given):
        self.req = req
        self.given = given

class ContextValidationError_WrongChannel(Exception):
    pass

class ContextValidationError_InsufficientPrivileges(Exception):
    pass

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

    def validate_context(self, client, message, postCommand):
        authorPerms = get_permissions(message.author, message.server)
        if authorPerms >= self.attributes.minPermissions:
            channelType = get_channel_type(message.channel)
            if channelType == ChannelType.Dev or channelType & self.attributes.channelRestrictions:
                reqParamsExpected = 0 if self.reqParams == None else len(self.reqParams)
                givenParams = len(postCommand)
                if givenParams >= reqParamsExpected:
                    return True
                else:
                    raise ContextValidationError_MissingParameters(reqParamsExpected, givenParams)                    
            else:
                raise ContextValidationError_WrongChannel               
        else:
            raise ContextValidationError_InsufficientPrivileges

    def validate_name(self, name):
        if self.name == name:
            return True
        elif self.aliases != None:
            return name in self.aliases
        return False

    async def execute(self, client, message, postCommand):
        if len(self.reqParams) + len(self.optParams) > 0:
            kwargs = {}
            for count, x in enumerate(self.reqParams):
                kwargs[x] = postCommand[count]
            offset = len(self.reqParams)
            for count, x in enumerate(self.optParams):
                if count + offset < len(postCommand):
                    kwargs[x] = postCommand[count + offset]
            await self.cb(client, message, **kwargs)
        else:
            await self.cb(client, message)

    def pretty_print(self):
        return self.simple_print() + '\n```{3}{4}```'.format('' if self.cb.__doc__ == None else self.cb.__doc__,
                                                           'No aliases' if len(self.aliases) == 0 else 'Aliases: ' + ' / '.join(self.aliases))

    def simple_print(self):
        return '**{0}** {1}{2}'.format( self.name,
                                        ' ' if len(self.reqParams) == 0 else ' '.join(['['+p+']' for p in self.reqParams]),
                                        ' ' if len(self.optParams) == 0 else ' '.join(['{'+p+'}' for p in self.optParams]))



class CommandsHandler:
    def __init__(self):
        self._commands = []

    def _add(self, command):
        self._commands.append(command)
        return command

    def find(self, name):
        for command in self._commands:
            if command.validate_name(name):
                return command
        return None

    def _validate_command(self, client, message):
        split = message.content.split()
        if split[0] == commandTrigger or client.user in message.mentions:
            return self.find(split[1])
        return None

    def register(self, **kwargs):
        def decorator(func):
            async def wrapper(client, message, **kwArgs):
                await func(client, message, **kwArgs)
            wrapper.__doc__ = func.__doc__
            return self._add(Command(func.__name__, wrapper, Attributes(**kwargs)))
        return decorator

    async def try_execute(self, client, message):
        split = message.content.split()

        if message.channel.is_private:
            command = self.find(split[0])
            offset = 1
        elif split[0] == commandTrigger or client.user in message.mentions:
            command = self.find(split[1])
            offset = 2
        else:
            command = None

        if command != None:
            postCommand = split[offset:len(split)]
            try:
                command.validate_context(client, message, postCommand)
                print(T_Log_ValidatedCommand.format(command.name, 
                    '' if len(postCommand) == 0 else ' ' + ' '.join(postCommand),
                    message,
                    'PM' if message.channel.is_private else '#{0.channel.name}/{0.channel.server.name}'.format(message)))
                await command.execute(client, message, postCommand)
            except ContextValidationError_MissingParameters as e:
                await client.send_message(message.channel, T_ValidateCommandContext_BadParameters.format(command.name, e.req, e.given))
            except ContextValidationError_WrongChannel:
                await client.send_message(message.channel, T_ValidateCommandContext_BadChannel.format(command.name))
            except ContextValidationError_InsufficientPrivileges:
                await client.send_message(message.channel, T_ValidateCommandContext_BadPrivileges.format(command.name))

    def get_authorized_commands(self, client, message):
        for command in self._commands:
            try:
                command.validate_context(client, message, [])
            except ContextValidationError_WrongChannel:
                continue
            except ContextValidationError_InsufficientPrivileges:
                continue
            except:
                pass
            yield command

    def dump(self):
        utils.print_array(
            'Commands registered', 
            commandFormat.format('Name', 'Min Permissions', 'Channel Type', 'Aliases', 'Required Args', 'Optional Args'), 
            self._commands, 
            lambda c: commandFormat.format( c.name, 
                                            c.attributes.minPermissions.name, 
                                            c.attributes.channelRestrictions.name, 
                                            '-' if len(c.aliases) == 0 else '/'.join(c.aliases),
                                            '-' if len(c.reqParams) == 0 else '/'.join(c.reqParams), 
                                            '-' if len(c.optParams) == 0 else '/'.join(c.optParams)))


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