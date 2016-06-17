from inspect import cleandoc

C_ManagementChannelName = 'ChallongeManagement'
C_RoleName = 'Challonge'

T_JoinServer_Header = 'Thanks for installing the Challonge Bot on server \'*{0}*\'\n'
T_JoinServer_NeedKey = cleandoc("""Your challonge username is already registered (\'{}\'), but your API key is needed as well
    Please use this command in private message:
    key [your_key] | ex: key 1234567890abcdefg""")

T_JoinServer_NeedName = cleandoc("""Your API key is already registered, but not your challonge username
    Please use this command in private message:
    username: [your_username] | ex: username fp12""")

T_JoinServer_NeedAll = cleandoc("""Your challonge username and API key are needed for this bot to work with challonge
    Please use these commands in private message:
    username [your_username] | ex: username fp12
    key [your_key] | ex: key 1234567890abcdefg""")

T_JoinServer_NeedNothing = 'I already have all the info I need. You can start using this bot in the new server right now! Enjoy!'
T_JoinServer_SetupDone = 'Bot setup has been completed: the channel {} has been created on the server'.format(
    C_ManagementChannelName)

T_Log_JoinedServer = 'on_server_join [Server \'{0}\' ({1})] [Owner \'{2}\' ({3})]'
T_Log_RemovedServer = 'on_server_removed [Server \'{0}\' ({1})] [Owner \'{2}\' ({3})]'
T_Log_CleanRemovedServer = 'cleaned Server {} from db'
T_Log_ValidatedCommand = 'on_validated_command [{0}{1}] from @{2.author.name} on {3}'

T_ValidateCommandContext_BadParameters = '❌ Wrong number of parameters for this command (expected: {0}, given: {1})'
T_ValidateCommandContext_BadChannel = '❌ Wrong channel for this command'
T_ValidateCommandContext_BadPrivileges = '❌ Not enough privileges for this command'
T_ValidateCommandContext_BadTournamentState = '❌ This command cannot be executed right now (tournament state)'

T_LeaveServer_Instructions = cleandoc("""Thanks you for using the Challonge bot! The management channel and the Challonge role have been removed from server {0}
    Feel free to send feedback here with command *feedback*""")

T_TournamentCreated = cleandoc("""✅ Tournament **{0}** has been successfully created on challonge!
    Visit {1} to setup missing information such as game, description...
    The role {2} has been created to be assigned to participants when they join
    The channel {3} has been created to centralize all discussion about this tournament
    Have Fun!""")

T_OnChallongeException = cleandoc("""❌ Something happened during the Challonge request! Sorry, your command will fail...
    Here is the feedback from Challonge:
    ```{}```""")

T_PromoteError = cleandoc("""❌ Could not promote Member **{0.name}** because of insufficient permissions.
    {1} could you add Role 'Challonge' to this member? Thanks!""")
T_DemoteError = cleandoc("""❌ Could not demote Member **{0.name}** because of insufficient permissions.
    {1} could you remove Role 'Challonge' to this member? Thanks!""")

T_RemoveChallongeRoleError = '❌ Could not remove role ' + C_RoleName + ' because of: `{0}`'

T_ChannelDescriptionSeparator = '=-=-=-=\n'

T_HelpGlobal = cleandoc("""```ruby
    Usable Commands For You In This Channel
    ```
      {0}

    ```ruby
    [argument] >> Required Argument
    {{argument}} >> Optional Argument
    (do not type '[]' nor '{{}}')
    Note: some commands may only be available in Private Message. Send 'help' there too!
    ```""")

T_Info = cleandoc("""
    **Challonge Bot** by fp12
    Version: v.0.9.0
    Invite the bot into your server: https://discordapp.com/oauth2/authorize?client_id=183236147726516225&scope=bot&permissions=335670288
    Join the server to discuss further improvements, report bugs and more!
    https://discord.gg/0142k6dfba0Je6qo0
    """)
