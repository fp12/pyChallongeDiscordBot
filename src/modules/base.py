import json
import asyncio
import re
from enum import Enum


class Type(Enum):
    String = 0
    Array = 1
    Enum = 2
    Struct = 3
    Time = 4


def _is_required(value):
    return value.startswith('required')


def _get_type(value):
    split = value.split('_')
    if len(split) == 1:
        return Type.String, ''
    elif len(split) == 2:
        if split[1] == 'time':
            return Type.Time, ''
        if split[1] == 'array':
            return Type.Array, ''
    elif len(split) == 3:
        if split[1] == 'array':
            return Type.Array, split[2]
        elif split[1] == 'enum':
            return Type.Enum, split[2]
        elif split[1] == 'struct':
            return Type.Struct, split[2]
    return Type.String, ''


class Template:
    def __init__(self, template):
        self.template = template
        self.structs = {}
        with open('./config/%s' % template) as data_file:
            raw_template = json.load(data_file)
            if 'structs' in raw_template:
                self.structs = raw_template['structs']
            if 'enums' in raw_template:
                self.enums = raw_template['enums']
            self.structs['main'] = {data: raw_template[data] for data in raw_template if data not in ['structs', 'enums']}

    def _get_string(self, data):
        return True, data

    def _get_string_arr(self, data):
        clean_data = []
        for d in data:
            clean_data.append(d)
        return True, clean_data

    def _get_struct_arr(self, data, struct):
        clean_data = []
        for d in data:
            ok, s = self._get_struct(d, struct)
            if not ok:
                return False, s
            clean_data.append(s)
        return True, clean_data

    def _get_enum(self, data, enum):
        if data in self.enums[enum]:
            return True, data
        return False, data + ' not in enum ' + enum

    def _get_struct(self, data, struct):
        clean_data = {}
        for key, info in self.structs[struct].items():
            if _is_required(info) and key not in data:
                return False, key + ' not found in data'
            elif key in data:
                datatype, name = _get_type(info)
                if datatype == Type.String:
                    ok, clean_data[key] = self._get_string(data[key])
                    if not ok:
                        return False, '_get_string failed for key ' + key + ': ' + clean_data[key]
                elif datatype == Type.Array:
                    if name == '':
                        ok, clean_data[key] = self._get_string_arr(data[key])
                        if not ok:
                            return False, '_get_string_arr failed for key ' + key + ': ' + clean_data[key]
                    elif name in self.structs:
                        ok, clean_data[key] = self._get_struct_arr(data[key], name)
                        if not ok:
                            return False, '_get_struct_arr failed for key ' + key + ': ' + clean_data[key]
                    else:
                        return False, name + ' not declared as struct'
                elif datatype == Type.Enum:
                    if name in self.enums:
                        ok, clean_data[key] = self._get_enum(data[key], name)
                        if not ok:
                            return False, '_get_enum failed for key ' + key + ': ' + clean_data[key]
                    else:
                        return False, name + ' not declared as enum'
                elif datatype == Type.Struct:
                    if name in self.structs:
                        ok, clean_data[key] = self._get_struct(data[key], name)
                        if not ok:
                            return False, '_get_struct failed for key ' + key + ': ' + clean_data[key]
                    else:
                        return False, name + ' not declared as struct'
                elif datatype == Type.Time:
                    ok, clean_data[key] = self._get_time(data[key])
                    if not ok:
                        return False, '_get_time failed for key ' + key + ': ' + clean_data[key]
                else:
                    return False, 'Unknown type for ' + info
        return True, data

    def _get_time(self, data):
        r = re.compile(r'(?:(?P<days>\d+)d)?(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?')
        m = r.match(data)
        if m:
            return True, int(m.group('seconds') or 0) + int(m.group('minutes') or 0) * 60 + int(m.group('hours') or 0) * 3600 + int(m.group('days') or 0) * 86400
        return False, ' not a good time format '

    def validate(self, data):
        ok, clean_data = self._get_struct(data, 'main')
        if ok:
            return True, clean_data
        else:
            return False, 'validate failed: ' + clean_data


class Module:
    def __init__(self, client, server_id):
        self._client = client
        self._server_id = server_id
        self._data = {}
        self._on_init()

    def accept_definition(self, data):
        self._data = data

    def _on_init(self):
        pass

    def build(self, json_data):
        return False

    async def terminate(self):
        pass

    async def post_init(self):
        pass

    async def on_event(self, event, **event_args):
        pass

    async def on_state_change(self, new_state, **event_args):
        pass
