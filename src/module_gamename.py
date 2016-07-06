from module_base import Module, Template


class Module_GameName(Module):
    template_file = 'module_gamename.template'
    template = None

    def __init__(self, client):
        super(Module_GameName, self).__init__(self, client)
        self._data = {}

    def accept_definition(self, data):
        self._data = data

    def build(self, json_data):
        if not self.template:
            self.template = Template(self.template_file)

        valid, data = self.template.validate(json_data)
        if valid:
            self._data = data
            return True
        else:
            print('invalid data: ' + data)
            return False

    def on_event(self, event, **event_args):
        if 'enums' in self._data and 'eventname' in self._data['enums'] and event.name in self._data['enums']['eventname']:
            print('[Module_GameName::on_event] event=%s args=%s' % (event.name, event_args))
            if 'states' in self._data:
                for s in self._data:
                    if 'events' in s:
                        for e in s['events']:
                            if e['name'] == event.name:
                                self._client.change_nickname(event_args.get('me'), e['text'])
