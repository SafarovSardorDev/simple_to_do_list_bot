from aiogram import types
from loader import dp, db

@dp.message_handler(commands=['stats'])
async def stats_handler(message: types.Message):
    user_id = message.from_user.id
    tasks = await db.task.find_many(where={"user_id": user_id})
    
    total = len(tasks)
    done = len([t for t in tasks if t.is_done])
    left = total - done

    percent_done = int((done / total) * 100) if total else 0
    bar = "🟩" * (percent_done // 10) + "⬜️" * (10 - (percent_done // 10))

    text = (
        f"📊 <b>Statistika</b>\n\n"
        f"🔢 Umumiy vazifalar: <b>{total}</b>\n"
        f"✅ Bajarilgan: <b>{done}</b>\n"
        f"📌 Qolgan: <b>{left}</b>\n\n"
        f"{bar} {percent_done}% bajarilgan"
    )

    await message.answer(text)
