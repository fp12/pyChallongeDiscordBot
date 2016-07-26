import asyncio

from database.core import db
from challonge_impl.accounts import ChallongeException, get as get_account
from challonge_impl.utils import TournamentState
from challonge_impl.events import Events
from modules.base import Module, Template


max_nickname_len = 31


class Module_BotName(Module):
    template_file = 'module_botname.template'
    template = None

    def _on_init(self):
        if not self.template:
            self.template = Template(self.template_file)

    def accept_definition(self, data):
        self._data = data

    def build(self, json_data):
        valid, data = self.template.validate(json_data)
        if valid:
            self._data = data
        else:
            print('invalid data: ' + data)
        return valid

    async def terminate(self):
        me = self._client.get_server(self._server_id).me
        await self._client.change_nickname(me, None)

    async def post_init(self):
        for db_t in db.get_tournaments(self._server_id):
            account, exc = await get_account(db_t.host_id)
            if not exc:
                try:
                    t = await account.tournaments.show(db_t.challonge_id)
                except ChallongeException as e:
                    print('Exception in Module_BotName._init_tournaments: %s' % e)
                else:
                    if t['state'] in TournamentState.__members__.keys():
                        await self.on_state_change(TournamentState[t['state']], t_name=t['name'])
            else:
                print('Exception in Module_BotName._init_tournaments: %s' % exc)

    async def _revert_to_default_in(self, time):
        await asyncio.sleep(time)
        await self.post_init()  # revert to current state (may have changed)

    async def on_event(self, event, **event_args):
        if self.template.enums and 'eventname' in self.template.enums and event.name in self.template.enums['eventname'] and 'states' in self._data:
            for s in self._data['states']:
                if 'events' in s:
                    for e in s['events']:
                        if e['name'] == event.name:
                            nickname = e['text'].format(**event_args)
                            me = event_args.get('me') if event_args.get('me') else self._client.get_server(self._server_id).me
                            if len(nickname) <= max_nickname_len and me.nick != nickname:
                                await self._client.change_nickname(me, nickname)
                                if 'duration' in e:
                                    print('Modules: Current nickname should be reverted in %ss' % e['duration'])
                                    self._client.loop.create_task(self._revert_to_default_in(e['duration']))

    async def on_state_change(self, new_state, **event_args):
        for s in self._data['states']:
            if s['name'] == new_state.name and 'text' in s:
                nickname = s['text'].format(**event_args)
                me = event_args.get('me') if event_args.get('me') else self._client.get_server(self._server_id).me
                if len(nickname) <= max_nickname_len and me.nick != nickname:
                    await self._client.change_nickname(me, nickname)
