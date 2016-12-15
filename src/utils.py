import re
from enum import Enum

from log import log_main


class AutoEnum(Enum):
    def __new__(cls):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj


def print_array(title, header, iterable, func):
    vert_sep = '|'
    array_sep = '='
    header_sep = '-'
    line_len = len(header)
    array_line_separators = ''.ljust(line_len, array_sep)
    header_line_separators = vert_sep.ljust(line_len - 1, header_sep) + vert_sep

    arr = []
    arr.append(array_line_separators)
    arr.append(vert_sep + ' ' + title.ljust(line_len - 3) + vert_sep)
    arr.append(header_line_separators)
    arr.append(header)
    arr.append(header_line_separators)
    for x in iterable:
        s = func(x)
        if s is not None and s != '':
            arr.append(s)
    arr.append(array_line_separators)

    finalStr = '\n'.join(arr)
    log_main.info(finalStr)
    return finalStr


def paginate(dump, max_per_page=2000):
    paginated = []
    if len(dump) < max_per_page:
        paginated.append(dump)
    else:
        page_index = 0
        len_count = 0
        split = dump.splitlines(True)
        for i, line in enumerate(split):
            if i == len(split) - 1:
                paginated.append(dump[page_index:])
            elif len_count + len(line) >= max_per_page:
                paginated.append(dump[page_index:page_index + len_count])
                page_index += len_count
                len_count = len(line)
            else:
                len_count += len(line)
    return paginated


def get_user_id_from_mention(mention):
    regexRes = re.findall(r'<@!?([0-9]+)>', mention)
    if len(regexRes) == 1:
        return regexRes[0]
    return 0


class ArrayFormater:
    def __init__(self, title, row_count):
        self.title = title
        self.row_count = row_count
        self.length_counter = [0] * row_count
        self.lines = []

    def add(self, *args):
        assert(len(args) == self.row_count)
        self.lines.append(tuple(args))
        for index in range(self.row_count):
            self.length_counter[index] = max(self.length_counter[index], len(args[index]))

    def get(self):
        pattern = '|'
        for index in range(self.row_count):
            match = '{0[' + str(index) + ']:{0}}}'.format(self.length_counter[index])
            pattern += ' {0} |'.format(match)
        txt = '| ' + self.title + '\n'
        for line in self.lines:
            txt += pattern.format(line) + '\n'
        return txt
