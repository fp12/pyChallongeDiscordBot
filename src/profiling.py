import time
from enum import Enum


__enabled = False


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
        pass
        # end = time.time()


def profile(scope):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if __enabled:
                with Profiler(scope, name=func.__qualname__, args=repr(args)):
                    return func(*args, **kwargs)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def profile_async(scope):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if __enabled:
                with Profiler(scope, name=func.__qualname__, args=repr(args)):
                    return await func(*args, **kwargs)
            return await func(*args, **kwargs)
        return wrapper
    return decorator
