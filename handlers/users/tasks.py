import re
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from loader import dp, db
from states.taskst import TaskState
from keyboards.default.mainbuttons import main_menu
from datetime import datetime

@dp.message_handler(text="➕ Vazifa qo‘shish")
async def add_task(message: types.Message):
    await message.answer("Vazifa sarlavhasini kiriting:")
    await TaskState.title.set()

@dp.message_handler(state=TaskState.title)
async def process_task_title(message: types.Message, state: FSMContext):
    title = message.text.strip()
    if not title:
        await message.answer("❌ Sarlavha bo‘sh bo‘lmasligi kerak. Iltimos, qaytadan kiriting:")
        return

    try:
        user = await db.user.find_first(where={"telegramId": message.from_user.id})
        if not user:
            await message.answer("❌ Ro‘yxatdan o‘ting. /start")
            await state.finish()
            return

        await db.task.create({
            "userId": user.id,
            "title": title,
            "status": "TODO",
        })
        await message.answer("✅ Vazifa qo‘shildi!", reply_markup=main_menu())
        await state.finish()
    except Exception as e:
        await message.answer("❌ Xato yuz berdi.")
        print(f"Xato: {e}")

def create_task_keyboard(task_id: int, status: str):
    """Vazifa uchun inline tugmalar yaratish"""
    keyboard = InlineKeyboardMarkup()
    if status == "TODO":
        keyboard.add(
            InlineKeyboardButton("✅ Tugallash", callback_data=f"task_{task_id}_complete"),
            InlineKeyboardButton("🗑 O‘chirish", callback_data=f"task_{task_id}_delete")
        )
    else:
        keyboard.add(
            InlineKeyboardButton("📋 Qayta faollashtirish", callback_data=f"task_{task_id}_reopen"),
            InlineKeyboardButton("🗑 O‘chirish", callback_data=f"task_{task_id}_delete")
        )
    return keyboard

@dp.message_handler(text="📋 Mening vazifalarim")
async def list_tasks(message: types.Message):
    try:
        user = await db.user.find_first(where={"telegramId": message.from_user.id})
        if not user:
            await message.answer("❌ Ro‘yxatdan o‘ting. /start")
            return

        tasks = await db.task.find_many(
            where={"userId": user.id, "status": "TODO"},
            order={"createdAt": "asc"}  # Birinchi qo‘shilgan vazifa birinchi chiqadi
        )

        if not tasks:
            await message.answer("📭 Faol vazifalar yo‘q.", reply_markup=main_menu())
            return

        for idx, task in enumerate(tasks, 1):
            response = f"{idx}. {task.title}"
            await message.answer(response, reply_markup=create_task_keyboard(task.id, task.status))
    except Exception as e:
        await message.answer("❌ Xato yuz berdi.")
        print(f"Xato: {e}")

@dp.message_handler(text="✅ Tugallanganlar")
async def list_completed_tasks(message: types.Message):
    try:
        user = await db.user.find_first(where={"telegramId": message.from_user.id})
        if not user:
            await message.answer("❌ Ro‘yxatdan o‘ting. /start")
            return

        tasks = await db.task.find_many(
            where={"userId": user.id, "status": "DONE"},
            order={"createdAt": "asc"}  # Birinchi qo‘shilgan vazifa birinchi chiqadi
        )

        if not tasks:
            await message.answer("✅ Tugallangan vazifalar yo‘q.", reply_markup=main_menu())
            return

        for idx, task in enumerate(tasks, 1):
            completed_at = task.completedAt.strftime("%Y-%m-%d %H:%M") if task.completedAt else "Noma'lum"
            response = f"{idx}. {task.title} (Tugallangan: {completed_at})"
            await message.answer(response, reply_markup=create_task_keyboard(task.id, task.status))
    except Exception as e:
        await message.answer("❌ Xato yuz berdi.")
        print(f"Xato: {e}")

@dp.message_handler(text="📊 Statistika")
async def show_statistics(message: types.Message):
    try:
        user = await db.user.find_first(where={"telegramId": message.from_user.id})
        if not user:
            await message.answer("❌ Ro‘yxatdan o‘ting. /start")
            return

        total_tasks = await db.task.count(where={"userId": user.id})
        todo_tasks = await db.task.count(where={"userId": user.id, "status": "TODO"})
        done_tasks = await db.task.count(where={"userId": user.id, "status": "DONE"})

        response = "📊 Sizning statistikangiz:\n\n"
        response += f"🔢 Umumiy vazifalar: {total_tasks}\n"
        response += f"📋 Faol vazifalar: {todo_tasks}\n"
        response += f"✅ Tugallangan vazifalar: {done_tasks}\n"

        await message.answer(response, reply_markup=main_menu())
    except Exception as e:
        await message.answer("❌ Xato yuz berdi.")
        print(f"Xato: {e}")

@dp.message_handler(text="ℹ️ Info")
async def show_info(message: types.Message):
    response = "ℹ️ To-do List Bot\n\n"
    response += "Bu bot vazifalarni boshqarishga yordam beradi:\n"
    response += "➕ Vazifa qo‘shish: Yangi vazifa yaratish.\n"
    response += "📋 Mening vazifalarim: Faol vazifalarni ko‘rish.\n"
    response += "✅ Tugallanganlar: Tugallangan vazifalarni ko‘rish.\n"
    response += "📊 Statistika: Vazifalar statistikasi.\n"
    response += "ℹ️ Info: Ushbu ma'lumot.\n\n"
    response += "Yordam uchun /start buyrug‘idan foydalaning."

    await message.answer(response, reply_markup=main_menu())

@dp.callback_query_handler(regexp=r"task_(\d+)_(complete|reopen|delete)")
async def handle_task_action(callback: types.CallbackQuery):
    try:
        match = re.match(r"task_(\d+)_(complete|reopen|delete)", callback.data)
        task_id = int(match.group(1))
        action = match.group(2)

        task = await db.task.find_first(where={"id": task_id})
        if not task:
            await callback.answer("❌ Vazifa topilmadi.")
            return

        user = await db.user.find_first(where={"telegramId": callback.from_user.id})
        if not user or task.userId != user.id:
            await callback.answer("❌ Bu sizning vazifangiz emas.")
            return

        if action == "complete":
            await db.task.update(
                where={"id": task_id},
                data={"status": "DONE", "completedAt": datetime.utcnow()}
            )
            await callback.message.edit_text(f"✅ {task.title} tugallandi!")
        elif action == "reopen":
            await db.task.update(
                where={"id": task_id},
                data={"status": "TODO", "completedAt": None}
            )
            await callback.message.edit_text(f"📋 {task.title} qayta faollashtirildi!")
        elif action == "delete":
            await db.task.delete(where={"id": task_id})
            await callback.message.edit_text(f"🗑 {task.title} o‘chirildi!")

        await callback.answer()
    except Exception as e:
        await callback.answer("❌ Xato yuz berdi.")
        print(f"Xato: {e}")