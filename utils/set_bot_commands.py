from aiogram import types

async def set_default_commands(dp):
    """Bot komandalarini o'rnatish uchun funksiya"""
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Botni qayta ishga tushirish"),
        types.BotCommand("help", "Yordam olish"),
    ])