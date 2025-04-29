from aiogram import types
from loader import dp, db

@dp.message_handler(commands=['info'])
async def user_info(message: types.Message):
    user = await db.user.find_unique(where={"telegram_id": message.from_user.id})
    if not user:
        await message.answer("❌ Siz ro‘yxatdan o‘tmagansiz. /start buyrug‘ini bosing.")
        return

    msg = (
        f"👤 <b>Ism:</b> {user.full_name}\n"
        f"📞 <b>Telefon:</b> {user.phone}\n"
        f"🆔 <b>Telegram ID:</b> {user.telegram_id}"
    )
    await message.answer(msg)
