from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    btns = ReplyKeyboardMarkup(resize_keyboard=True)
    btns.add("➕ Vazifa qo‘shish", "📋 Mening vazifalarim")
    btns.add("✅ Tugallanganlar", "📊 Statistika")
    btns.add("ℹ️ Info")
    return btns

def phone_request_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = KeyboardButton("📞 Raqamni yuborish", request_contact=True)
    keyboard.add(button)
    return keyboard
