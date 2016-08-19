metaattr = 'metaattr'
table_name = 'table_name'
columns = 'columns'


class DBModel(type):
    def __new__(cls, name, bases, namespace, **kwargs):
        # adding table_name as a class member
        namespace[table_name] = kwargs.get(table_name)
        # adding columns as named class members
        for x in kwargs.get(metaattr):
            namespace[x] = x
        namespace[columns] = kwargs.get(metaattr)
        # preparing columns for instances
        namespace[metaattr] = kwargs.get(metaattr)
        # don't propagate kwargs: they are into namespace
        return super().__new__(cls, name, bases, namespace)

    def __init__(cls, name, bases, namespace, **kwargs):
        # don't propagate kwargs
        super().__init__(name, bases, namespace)

    def __call__(cls, *args, **kwargs):
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

    def __str__(self):
        return self.table_name
