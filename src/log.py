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

log_db.setLevel(logging.DEBUG)

__loggers = [log_main, log_db, log_modules, log_commands_core, log_commands_def, log_challonge]


def set_level(level, logger=None):
    if level == 'error':
        log_level = logging.ERROR
    elif level == 'warning':
        log_level = logging.WARNING
    elif level == 'debug':
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    if not logger:
        for l in __loggers:
            l.setLevel(log_level)
    else:
        logging.getLogger(__prefix + logger).setLevel(log_level)
