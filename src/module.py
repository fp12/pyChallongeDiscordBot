import json
from db_access import db
from module_gamename import Module_GameName


class Modules:
    def __init__(self):
        self._client = None
        self.loaded_modules = {}

    def set_client(self, client):
        self._client = client
        self._load_from_db()

    def _create_new_module(self, name):
        if name == 'gamename':
            return Module_GameName(self._client)
        return None

    def _load_from_db(self):
        for m in db.get_modules():
            new_module = self._create_new_module(m.module_name)
            if new_module:
                new_module.accept_definition(m.module_def)
                if m.server_id not in self.loaded_modules:
                    self.loaded_modules[m.server_id] = []
                self.loaded_modules[m.server_id].append(new_module)

    def load_from_raw(self, raw, serverid):
        raw_json = json.loads(raw)
        if 'name' in raw_json:
            new_module = self._create_new_module(raw_json['name'])
            if new_module and new_module.build(raw_json):
                if serverid not in self.loaded_modules:
                    self.loaded_modules[serverid] = []
                for m in self.loaded_modules[serverid]:
                    if type(m) == type(new_module):
                        del m
                self.loaded_modules[serverid].append(new_module)
                db.add_module(serverid, raw_json['name'], str(new_module._data))
                return True
        return False

    def on_event(self, serverid, event, **event_args):
        if serverid in self.loaded_modules:
            for m in self.loaded_modules[serverid]:
                m.on_event(event, event_args)


modules = Modules()


if __name__ == "__main__":
    with open('config/module_gamename_example.json') as data_file:
        modules.load_raw(data_file.read())
