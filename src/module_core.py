import json
from module_gamename import Module_GameName

modules = {}


def load_module(raw, serverid):
    raw_json = json.loads(raw)
    if 'name' in raw_json:
        if raw_json['name'] == 'gamename':
            new_module = Module_GameName()
        if new_module.build(raw_json):
            for m in modules[serverid]:
                if type(m) == type(new_module):
                    del m
            modules[serverid].append(new_module)


if __name__ == "__main__":
    with open('config/module_gamename_example.json') as data_file:
        load_module(data_file.read())
