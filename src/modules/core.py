import json
import asyncio
import ast

from database.core import db
from modules.module_botname import Module_BotName


class Modules:
    def __init__(self):
        self._client = None
        self._loaded_modules = {}

    async def set_client(self, client):
        if self._client is None:
            self._client = client
            self._load_from_db()
            for k, v in self._loaded_modules.items():
                for m in v:
                    await m.post_init()
            print('modules initialized')

    def _create_new_module(self, name, server_id):
        if name == 'botname':
            return Module_BotName(self._client, server_id)
        return None

    def _load_from_db(self):
        for m in db.get_modules():
            new_module = self._create_new_module(m.module_name, m.server_id)
            if new_module:
                new_module.accept_definition(ast.literal_eval(m.module_def))
                if m.server_id not in self._loaded_modules:
                    self._loaded_modules[m.server_id] = []
                self._loaded_modules[m.server_id].append(new_module)

    async def load_from_raw(self, raw, server_id):
        raw_json = json.loads(raw)
        if 'name' in raw_json:
            new_module = self._create_new_module(raw_json['name'], server_id)
            if new_module and new_module.build(raw_json):
                if server_id not in self._loaded_modules:
                    self._loaded_modules[server_id] = []
                for m in self._loaded_modules[server_id]:
                    if type(m) == type(new_module):
                        await m.terminate()
                        del m
                self._loaded_modules[server_id].append(new_module)
                db.add_module(server_id, raw_json['name'], str(new_module._data))
                return True
        return False

    async def on_event(self, server_id, event, **event_args):
        if server_id in self._loaded_modules:
            for m in self._loaded_modules[server_id]:
                await m.on_event(event, **event_args)

    async def on_state_change(self, server_id, new_state, **event_args):
        if server_id in self._loaded_modules:
            for m in self._loaded_modules[server_id]:
                await m.on_state_change(new_state, **event_args)


modules = Modules()


if __name__ == "__main__":
    with open('config/module_botname_example.json') as data_file:
        modules.load_raw(data_file.read())
