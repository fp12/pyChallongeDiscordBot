from module import Module, Template


class Module_GameName(Module):
    template_file = 'module_gamename.template'
    template = None

    def __init__(self):
        self._data = {}

    def build(self, json_data):
        if not self.template:
            self.template = Template(self.template_file)

        valid, data = self.template.validate(json_data)
        if valid:
            self._data = data
        else:
            print('invalid data: ' + data)
