C_ManagementChannelName = 'ChallongeManagement'
C_RoleName = 'Challonge'

T_JoinServer_Header = 'Thanks for installing the Challonge Bot on server \'*{0}*\'\n'
T_JoinServer_NeedKey = 'Your challonge username is already registered (\'{}\'), but your API key is needed as well.\nPlease use this command in private message:\n*key: \{your_key\}*. ex: *key xxxxxxxxxxxxxxxxxxxxxxxxxxx*'
T_JoinServer_NeedName = 'Your API key is already registered, but not your challonge username.\nPlease use this command in private message: *username: \{your_username\}*. ex: *username fp12*'
T_JoinServer_NeedAll = 'Your challonge username and API key are needed for this bot to work with challonge.\nPlease use these commands in private message:\n*username \{your_username\}*. ex: *username fp12*\n*key: \{your_key\}*. ex: *key xxxxxxxxxxxxxxxxxxxxxxxxxxx*'
T_JoinServer_NeedNothing = 'I already have all the info I need. You can start using this bot in the new server right now! Enjoy!'
T_JoinServer_SetupDone = 'Bot setup has been completed: a new channel has been created on the server'

T_Log_JoinedServer = 'on_server_join [Server \'{0}\' ({1})] [Owner \'{2}\' ({3})]'
T_Log_RemovedServer = 'on_server_removed [Server \'{0}\' ({1})] [Owner \'{2}\' ({3})]'
T_Log_CleanRemovedServer = 'cleaned Server {} from db'
T_Log_ValidatedCommand = 'on_validated_command [{0}{1}] from @{2.author.name} on {3}'

T_ValidateCommandContext_BadParameters = 'Wrong number of parameters for command ***{0}*** (expected: {1}, given: {2})'
T_ValidateCommandContext_BadChannel = 'Wrong channel for command ***{}***'
T_ValidateCommandContext_BadPrivileges = 'Not enough privileges for command ***{}***'

T_LeaveServer_Instructions = 'Thanks you for using the Challonge bot! The management channel and the Challonge role have been removed from server {0}\n\Feel free to send feedback here with command *feedback*'