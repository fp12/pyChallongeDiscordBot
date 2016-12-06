import asyncio
import re
import discord

from discord_impl.permissions import Permissions, get_permissions
from discord_impl.channel_type import ChannelType, get_channel_type
from challonge_impl.accounts import ChallongeAccess, UserNotFound, UserNameNotSet, APIKeyNotSet, InvalidCredentials, get as get_account
from challonge_impl.utils import validate_tournament_state
from database.core import db
from const import *
from utils import print_array
from log import log_commands_core
from profiling import Profiler, Scope, profile, profile_async


commandFormat = '| {0:16} | {1:15} | {2:12} | {3:17} | {4:17} | {5:18} | {6:13} |'


class MissingParameters(Exception):
    def __init__(self, req, given):
        self.req = req
        self.given = given

    def __str__(self):
        return T_ValidateCommandContext_BadParameters.format(self.req, self.given)


class WrongChannel(Exception):
    def __str__(self):
        return T_ValidateCommandContext_BadChannel


class InsufficientPrivileges(Exception):
    def __str__(self):
        return T_ValidateCommandContext_BadPrivileges


class BadTournamentState(Exception):
    def __str__(self):
        return T_ValidateCommandContext_BadTournamentState


class Attributes:
    def __init__(self, **kwargs):
        self.minPermissions = kwargs.get('minPermissions', Permissions.User)
        self.channelRestrictions = kwargs.get('channelRestrictions', ChannelType.Other)
        self.challongeAccess = kwargs.get('challongeAccess', ChallongeAccess.NotRequired)
        self.tournamentState = kwargs.get('tournamentState', None)


class Command:
    def __init__(self, name, cb, attributes=None):
        self.name = name
        self.cb = cb
        self.attributes = attributes
        self.aliases = []
        self.reqParams = []
        self.optParams = []
        self.helpers = []

    def __repr__(self):
        return '[Command:%s]' % self.name

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

    async def validate_context(self, client, message, postCommand, context_cache):
        if context_cache['permissions'] < self.attributes.minPermissions:
            return False, InsufficientPrivileges()

        if not context_cache['channel_type'] & self.attributes.channelRestrictions:
            return False, WrongChannel()

        if self.attributes.challongeAccess == ChallongeAccess.RequiredForAuthor:
            acc, exc = await get_account(message.author.id)
            if exc:
                return False, exc
        elif self.attributes.challongeAccess == ChallongeAccess.RequiredForHost and context_cache['db_tournament']:
            acc, exc = await get_account(context_cache['db_tournament'].host_id)
            if exc:
                return False, exc
            if acc and self.attributes.tournamentState:
                if not await validate_tournament_state(acc, context_cache['db_tournament'].challonge_id, self.attributes.tournamentState):  # can raise
                    return False, BadTournamentState()

        reqParamsExpected = len(self.reqParams)
        givenParams = len(postCommand)
        if givenParams < reqParamsExpected:
            return False, MissingParameters(reqParamsExpected, givenParams)

        return True, None

    def validate_name(self, name):
        if self.name == name:
            return True
        if self.aliases is not None:
            return name in self.aliases
        return False

    async def _fetch_helpers(self, message, postCommand, context_cache):
        kwargs = {}
        for x in self.helpers:
            if x == 'account':
                if self.attributes.challongeAccess == ChallongeAccess.RequiredForAuthor:
                    kwargs[x], exc = await get_account(message.author.id)
                else:
                    kwargs[x], exc = await get_account(context_cache['db_tournament'].host_id)
            elif x == 'tournament_id':
                kwargs[x] = context_cache['db_tournament'].challonge_id
            elif x == 'tournament_role':
                roleid = context_cache['db_tournament'].role_id
                kwargs[x] = discord.utils.find(lambda r: r.id == roleid, message.server.roles)
            elif x == 'tournament_channel':
                channelid = context_cache['db_tournament'].channel_id
                kwargs[x] = discord.utils.find(lambda c: c.id == channelid, message.server.channels)
            elif x == 'participant_username':
                kwargs[x] = db.get_user(message.author.id).challonge_user_name
            elif x == 'announcement':
                kwargs[x] = ' '.join(postCommand)

        return kwargs

    def _fetch_args(self, postCommand):
        kwargs = {}

        for count, x in enumerate(self.reqParams):
            kwargs[x] = postCommand[count]
        offset = len(self.reqParams)

        for count, x in enumerate(self.optParams):
            if count + offset < len(postCommand):
                kwargs[x] = postCommand[count + offset]

        return kwargs

    async def execute(self, client, message, postCommand, context_cache):
        kwargs = {}
        kwargs.update(self._fetch_args(postCommand))
        kwargs.update(await self._fetch_helpers(message, postCommand, context_cache))
        await self.cb(client, message, **kwargs)

    def pretty_print(self):
        return self.simple_print() + '\n```{0}{1}```'.format('' if self.cb.__doc__ is None else self.cb.__doc__,
                                                             'No aliases' if len(self.aliases) == 0 else 'Aliases: ' + ' / '.join(self.aliases))

    def simple_print(self):
        return '`{0}` {1}{2} -- *{3}*'.format(self.name,
                                              '' if len(self.reqParams) == 0 else ' '.join(['[' + p + ']' for p in self.reqParams]),
                                              '' if len(self.optParams) == 0 else ' '.join(['{' + p + '}' for p in self.optParams]),
                                              'No description available' if self.cb.__doc__ is None else self.cb.__doc__.splitlines()[0])


class CommandsHandler:
    simple_word = r"""[!,\-\+\w@<>]+"""
    separated_words = r"""(?:{0}\s*)""".format(simple_word)
    argument = r"""\s*({0}|'{1}+')?""".format(simple_word, separated_words)
    base_regex = r"""(\w+){0}{0}{0}{0}""".format(argument)
    base_compiled_re = re.compile(base_regex, re.IGNORECASE)

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

    def _get_command_and_postcommand(self, client, message, context_cache):
        if not message.channel.is_private:
            commandTrigger = context_cache['db_server'].trigger
            regex = '(?:%s\s?|<@!?%s>\s)%s' % (commandTrigger, client.user.id, CommandsHandler.base_regex)
            r = re.compile(regex, re.IGNORECASE)
        else:
            r = CommandsHandler.base_compiled_re

        m = r.match(message.content)
        if m:
            return self.find(m.groups()[0]), [v for i, v in enumerate(m.groups()) if i > 0 and v is not None]
        return None, None

    def get_context_cache_update(self, context_cache, message):
        db_tournament = db.get_tournament(message.channel) if message.server else None
        context_cache.update({'permissions': get_permissions(message.author, message.channel),
                              'channel_type': get_channel_type(message.channel, context_cache['db_server'], db_tournament),
                              'db_tournament': db_tournament})
        return context_cache

    async def try_execute(self, client, message):
        context_cache = {'db_server': db.get_server(message.server) if message.server else None}
        command, postCommand = self._get_command_and_postcommand(client, message, context_cache)
        if command:
            # caching a few other things
            context_cache = self.get_context_cache_update(context_cache, message)
            validated, exc = await command.validate_context(client, message, postCommand, context_cache)
            if exc:
                await client.send_message(message.channel, exc)
            elif validated:
                await command.execute(client, message, postCommand, context_cache)
                log_commands_core.info(T_Log_ValidatedCommand.format(command.name,
                                                                     '' if len(postCommand) == 0 else ' ' + ' '.join(postCommand),
                                                                     message,
                                                                     'PM' if message.channel.is_private else '{0.channel.server.name}/#{0.channel.name}'.format(message)))

    def dump(self):
        return print_array('Commands Registered',
                            commandFormat.format('Name', 'Min Permissions', 'Channel Type', 'Challonge', 'Aliases', 'Required Args', 'Optional Args'),
                            self._commands,
                            lambda c: commandFormat.format(c.name,
                                                            c.attributes.minPermissions.name,
                                                            c.attributes.channelRestrictions.name,
                                                            c.attributes.challongeAccess.name,
                                                            '-' if len(c.aliases) == 0 else '/'.join(c.aliases),
                                                            '-' if len(c.reqParams) == 0 else '/'.join(c.reqParams),
                                                            '-' if len(c.optParams) == 0 else '/'.join(c.optParams)))


cmds = CommandsHandler()


class AuthorizedCommandsWrapper:
    def __init__(self, client, message):
        self._client = client
        self._message = message
        self._commands = iter(cmds._commands)
        self._context_cache = {'db_server': db.get_server(message.server) if message.server else None}
        self._context_cache = cmds.get_context_cache_update(self._context_cache, message)

    async def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            command = next(self._commands)
        except StopIteration:
            raise StopAsyncIteration

        validated, exc = await command.validate_context(self._client, self._message, [], self._context_cache)
        if validated or isinstance(exc, MissingParameters):
            return command.simple_print()
        else:
            return await self.__anext__()


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


import commands.definitions.admin  # needed to preload commands
import commands.definitions.management  # needed to preload commands
import commands.definitions.challonge  # needed to preload commands
