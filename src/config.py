import json

appConfig = []

with open('config/config.json') as data_file:
    appConfig = json.load(data_file)
