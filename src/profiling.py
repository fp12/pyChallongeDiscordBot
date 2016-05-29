import time
from enum import Enum
import inspect
import utils

class Scope(Enum):
    Core = 1
    Command = 0



class ProfilerCollector():
    coreFormatHeader = '| {0:15}| {1:30}| {2:10}|'
    coreFormat = '| {0:15.4f}| {1:30}| {2:10.4f}|'
    commandFormatHeader = '| {0:15}| {1:15}| {2:30}| {3:10}| {4:19}|'
    commandFormat = '| {0:15.4f}| {1:15}| {2:30}| {3:10.4f}| {4:19}|'
    
    def __init__(self):
        self._start = time.time()
        self._stats = []
    
    def log(self, scope, start, time, **kwargs):
        self._stats.append({'start':start-self._start, 'scope':scope, 'time':time, **kwargs})

    def _print_core(self, x):
        if x['scope'] == Scope.Core:
            return self.coreFormat.format(x['start'], x['name'], x['time'])

    def _print_command(self, x):
        if x['scope'] == Scope.Command:
            return self.commandFormat.format(x['start'], x['name'], x['args'], x['time'], x['server'])

    def dump(self):
        utils.print_array('Profiling Core stats',
                          self.coreFormatHeader.format('Start', 'Name', 'Time'),
                          self._stats,
                          self._print_core)
        utils.print_array('Profiling Command stats',
                          self.commandFormatHeader.format('Start', 'Name', 'Args', 'Time', 'Server'),
                          self._stats,
                          self._print_command)

collector = ProfilerCollector()



class Profiler():
    def __init__(self, scope, **kwargs):
        self._scope = scope
        self._args = kwargs
    
    def __enter__(self):
        self._start = time.time()
        return self
    
    def __exit__(self, *args):
        end = time.time()
        collector.log(self._scope, self._start, (end - self._start) * 1000, **self._args)


def profile(scope, **profilingArgs):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            with Profiler(scope, **profilingArgs) as p:
                await func(*args, **kwargs)
        return wrapper
    return decorator
