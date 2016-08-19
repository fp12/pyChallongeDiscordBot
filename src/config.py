import os

app_config = {}

keys = ['heroku',
        'devid',
        'discord_token',
        'cryptokey',
        'database',
        'whitelistedbots']

if os.getenv('heroku'):
    for k in keys:
        app_config[k] = os.getenv(k)
else:
    import json
    with open('config/config.json') as data_file:
        app_config = json.load(data_file)
