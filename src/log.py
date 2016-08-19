import logging

logging.basicConfig(format='[%(levelname)s] [%(name)s] %(message)s', level=logging.INFO)

__prefix = 'challonge_bot.'
log_main = logging.getLogger(__prefix + 'main')
log_db = logging.getLogger(__prefix + 'db')
log_modules = logging.getLogger(__prefix + 'modules')
log_commands_core = logging.getLogger(__prefix + 'commands_core')
log_commands_def = logging.getLogger(__prefix + 'commands_def')
log_challonge = logging.getLogger(__prefix + 'challonge_impl')

log_discord = logging.getLogger('discord')
log_discord.setLevel(logging.ERROR)
