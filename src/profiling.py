import time
from enum import Enum
import utils
from db_access import db


class Scope(Enum):
    Core = 1
    Command = 0


class Profiler():
    def __init__(self, scope, name, args=None, server=None):
        self._scope = scope
        self._name = name
        self._args = args
        self._server = server

    def __enter__(self):
        self._start = time.time()
        return self

    def __exit__(self, *args):
        end = time.time()
        db.add_profile_log(self._start, self._scope, round((end - self._start) * 1000, 2), self._name, self._args, self._server)


def profile(scope):
    def decorator(func):
        def wrapper(*args, **kwargs):
            with Profiler(scope, name=func.__qualname__, args=repr(args)) as p:
                return func(*args, **kwargs)
        return wrapper
    return decorator


def profile_async(scope):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            with Profiler(scope, name=func.__qualname__, args=repr(args)) as p:
                return await func(*args, **kwargs)
        return wrapper
    return decorator
