import asyncio
from permissions import Permissions, get_permissions
from channel_type import ChannelType, get_channel_type
from c_users import users_db, ChallongeAccess, UserNotFound, UserNameNotSet, APIKeyNotSet
from db_access import db
import discord
from const import *
import utils
from profiling import Profiler, Scope, profile, profile_async

commandTrigger = '>>>'
commandFormat = '| {0:17}| {1:16}| {2:13}| {3:11}| {4:20}| {5:20}| {6:20}|'


class ContextValidationError_MissingParameters(Exception):
    def __init__(self, req, given):
        self.req = req
        self.given = given


class ContextValidationError_WrongChannel(Exception):
    def __str__(self):
        return T_ValidateCommandContext_BadChannel


class ContextValidationError_InsufficientPrivileges(Exception):
    def __str__(self):
        return T_ValidateCommandContext_BadPrivileges


class Attributes:
    def __init__(self, **kwargs):
        self.minPermissions = kwargs.get('minPermissions', Permissions.User)
        self.channelRestrictions = kwargs.get('channelRestrictions', ChannelType.Other)
        self.challongeAccess = kwargs.get('challongeAccess', ChallongeAccess.NotRequired)


class Command:
    def __init__(self, name, cb, attributes=None):
        self.name = name
        self.cb = cb
        self.attributes = attributes
        self.aliases = []
        self.reqParams = []
        self.optParams = []
        self.helpers = []

    def add_required_params(self, *args):
        self.reqParams = args
        return self

    def add_optional_params(self, *args):
        self.optParams = args
        return self

    def add_aliases(self, *args):
        self.aliases = args
        return self

    def add_helpers(self, *args):
        self.helpers = args
        return self

    @profile(Scope.Core)
    def validate_context(self, client, message, postCommand):
        authorPerms = get_permissions(message.author, message.channel)
        if authorPerms >= self.attributes.minPermissions:
            channelType = get_channel_type(message.channel)
            if channelType == ChannelType.Dev or channelType & self.attributes.channelRestrictions:
                reqParamsExpected = 0 if self.reqParams is None else len(self.reqParams)
                givenParams = len(postCommand)
                if givenParams >= reqParamsExpected:
                    if self.attributes.challongeAccess == ChallongeAccess.Required:
                        acc = users_db.get_account(message.server)  # can raise
                else:
                    raise ContextValidationError_MissingParameters(
                        reqParamsExpected, givenParams)
            else:
                raise ContextValidationError_WrongChannel
        else:
            raise ContextValidationError_InsufficientPrivileges

    def validate_name(self, name):
        if self.name == name:
            return True
        elif self.aliases is not None:
            return name in self.aliases
        return False

    @profile(Scope.Core)
    def _fetch_helpers(self, message):
        kwargs = {}
        for x in self.helpers:
            if x == 'account':
                kwargs[x] = users_db.get_account(message.server)
            elif x == 'tournament_id':
                kwargs[x] = db.get_tournament(message.channel).challonge_id
            elif x == 'tournament_role':
                roleid = db.get_tournament(message.channel).role_id
                kwargs[x] = discord.utils.find(lambda r: r.id == roleid, message.server.roles)
            elif x == 'tournament_channel':
                channelid = db.get_tournament(message.channel).channel_id
                kwargs[x] = discord.utils.find(lambda c: c.id == channelid, message.server.channels)
            elif x == 'participant_username':
                participant = users_db.get_user(message.author.id)
                if participant:
                    kwargs[x] = participant.challongeUserName

        return kwargs

    @profile_async(Scope.Core)
    async def execute(self, client, message, postCommand):
        kwargs = {}

        for count, x in enumerate(self.reqParams):
            kwargs[x] = postCommand[count]
        offset = len(self.reqParams)

        for count, x in enumerate(self.optParams):
            if count + offset < len(postCommand):
                kwargs[x] = postCommand[count + offset]

        kwargs.update(self._fetch_helpers(message))

        await self.cb(client, message, **kwargs)

    def pretty_print(self):
        return self.simple_print() + '\n```{0}{1}```'.format('' if self.cb.__doc__ is None else self.cb.__doc__,
                                                             'No aliases' if len(self.aliases) == 0 else 'Aliases: ' + ' / '.join(self.aliases))

    def simple_print(self):
        return '`{0}` {1}{2} -- *{3}*'.format(self.name,
                                              ' ' if len(self.reqParams) == 0 else ' '.join(['[' + p + ']' for p in self.reqParams]),
                                              ' ' if len(self.optParams) == 0 else ' '.join(['{' + p + '}' for p in self.optParams]),
                                              'No description available' if self.cb.__doc__ is None else self.cb.__doc__.splitlines()[0])


class CommandsHandler:
    def __init__(self):
        self._commands = []

    def _add(self, command):
        self._commands.append(command)
        return command

    @profile(Scope.Core)
    def find(self, name):
        for command in self._commands:
            if command.validate_name(name):
                return command
        return None

    def register(self, **attributes):
        def decorator(func):
            async def wrapper(client, message, **postCommand):
                # choose only those that are most likely arguments but not the api key (could be Account...)
                args = ' '.join([v for k, v in postCommand.items() if isinstance(v, str) and k != 'key'])
                # server for profiling info
                server = 0 if message.channel.is_private else message.channel.server.id
                with Profiler(Scope.Command, name=func.__name__, args=args, server=server) as p:
                    await func(client, message, **postCommand)
            wrapper.__doc__ = func.__doc__
            return self._add(Command(func.__name__, wrapper, Attributes(**attributes)))
        return decorator

    @profile_async(Scope.Core)
    async def try_execute(self, client, message):
        split = message.content.split()

        if message.channel.is_private:
            if split[0] == commandTrigger:
                command = self.find(split[1])
                offset = 2
            else:
                command = self.find(split[0])
                offset = 1
        elif split[0] == commandTrigger or client.user in message.mentions:
            command = self.find(split[1])
            offset = 2
        else:
            command = None

        if command is not None:
            postCommand = split[offset:len(split)]
            try:
                command.validate_context(client, message, postCommand)
            except ContextValidationError_MissingParameters as e:
                await client.send_message(message.channel, T_ValidateCommandContext_BadParameters.format(command.name, e.req, e.given))
            except (ContextValidationError_WrongChannel,
                    ContextValidationError_InsufficientPrivileges,
                    UserNotFound,
                    UserNameNotSet,
                    APIKeyNotSet) as e:
                await client.send_message(message.channel, e)
            else:
                await command.execute(client, message, postCommand)
                print(T_Log_ValidatedCommand.format(command.name,
                                                    '' if len(postCommand) == 0 else ' ' + ' '.join(postCommand),
                                                    message,
                                                    'PM' if message.channel.is_private else '{0.channel.server.name}/#{0.channel.name}'.format(message)))

    def get_authorized_commands(self, client, message):
        for command in self._commands:
            try:
                command.validate_context(client, message, [])
            except (ContextValidationError_WrongChannel, ContextValidationError_InsufficientPrivileges):
                continue
            except:
                pass
            yield command

    def dump(self):
        return utils.print_array('Commands registered',
                                 commandFormat.format('Name', 'Min Permissions', 'Channel Type', 'Challonge', 'Aliases', 'Required Args', 'Optional Args'),
                                 self._commands,
                                 lambda c: commandFormat.format(c.name,
                                                                c.attributes.minPermissions.name,
                                                                c.attributes.channelRestrictions.name,
                                                                'True' if c.attributes.challongeAccess == ChallongeAccess.Required else 'False',
                                                                '-' if len(c.aliases) == 0 else '/'.join(
                                                                    c.aliases),
                                                                '-' if len(c.reqParams) == 0 else '/'.join(
                                                                    c.reqParams),
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


def helpers(*args):
    def decorator(func):
        return func.add_helpers(*args)
    return decorator
