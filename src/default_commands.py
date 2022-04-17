from aiogram import Bot, types


async def set_default_commands(bot: Bot):
    data = [
        (
            [
                types.BotCommand(command="start", description="Returns start message"),
                types.BotCommand(command="help", description="Helps"),
                types.BotCommand(command="contacts", description="Contacts"),
                types.BotCommand(command="health", description="Bot db healthcheck"),
                types.BotCommand(command="service", description="Run service"),
            ],
            types.BotCommandScopeAllPrivateChats(),
            None,
        )
    ]
    for commands, scope, lang_code in data:
        await bot.set_my_commands(commands=commands, scope=scope, language_code=lang_code)
