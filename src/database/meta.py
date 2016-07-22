metaattr = 'metaattr'


class DBModel(type):
    def __new__(cls, name, bases, namespace, **kargs):
        # don't propagate kargs but add them to namespace
        namespace[metaattr] = kargs.get(metaattr)
        return super().__new__(cls, name, bases, namespace)

    def __init__(cls, name, bases, namespace, **kargs):
        # don't propagate kargs
        super().__init__(name, bases, namespace)

    def __call__(cls, *args, **kwds):
        # create instance but don't propagate arguments
        obj = type.__call__(cls)
        # create attributes according to definition
        if metaattr in cls.__dict__:
            valid_args = []
            # allow plain args, tuples and lists
            if isinstance(args[0], tuple) or isinstance(args[0], list):
                valid_args = list(args[0])
            elif len(cls.__dict__[metaattr]) == len(args):
                valid_args = args
            if len(valid_args) == len(cls.__dict__[metaattr]):
                for i, f in enumerate(cls.__dict__[metaattr]):
                    setattr(obj, f, valid_args[i])
            else:
                for f in cls.__dict__[metaattr]:
                    setattr(obj, f, None)
        return obj
